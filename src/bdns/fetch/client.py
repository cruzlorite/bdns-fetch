# SPDX-License-Identifier: MIT

"""Python client for the BDNS API.

[`BDNSClient`][bdns.fetch.client.BDNSClient] has one `fetch_*` method per
endpoint. Their keyword arguments are the API's own query parameters, with
the API's spelling, so the official documentation applies unchanged. For
an endpoint without a method, [`get`][bdns.fetch.client.BDNSClient.get],
[`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] and
[`pages`][bdns.fetch.client.BDNSClient.pages] take a path and apply the
same policies.

Three policies apply to every request:

- **Rate limit.** Requests are spaced evenly, 9.5 per second by default,
  shared by every client in the process that does not bring its own
  [`RateLimiter`][bdns.fetch.utils.RateLimiter]. That is the per-IP limit
  of the official good-practice guide.
- **Retries.** Network failures, HTTP 429 and 5xx, and error codes that
  signal a temporary condition (`ERR_MANTENIMIENTO_BBDD`) are retried with
  exponential backoff and jitter, honouring `Retry-After`. Any other error
  is raised at once: repeating a bad request cannot fix it.
- **Pagination.** Pages are fetched one at a time by default, as the
  official good-practice guide asks. With `max_workers` above 1 they are
  fetched concurrently but still yielded in page order, with at most
  `2 * max_workers` held in memory, so a slow consumer slows the download
  rather than growing memory.

Each is explained in [how the client works](../../explanation/policies.md),
and recorded with its alternatives in the [ADRs](../../adr/index.md).
"""

import collections
import concurrent.futures
import logging
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import date
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import requests
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from tqdm import tqdm

from bdns.fetch import endpoints
from bdns.fetch.exceptions import BDNSError, BDNSTransientError, error_from_response
from bdns.fetch.types import (
    Ambito,
    DescripcionTipoBusqueda,
    Direccion,
    Order,
    TipoAdministracion,
)
from bdns.fetch.utils import RateLimiter, format_date_for_api_request, format_url

__all__ = [
    "DEFAULT_RATE_LIMITER",
    "MAX_RETRY_WAIT",
    "RETRYABLE_STATUS_CODES",
    "TRANSIENT_API_ERROR_CODES",
    "BDNSClient",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
"""HTTP statuses retried as transient."""

TRANSIENT_API_ERROR_CODES = frozenset({"ERR_MANTENIMIENTO_BBDD"})
"""BDNS `codigo` values retried as transient, whatever the HTTP status."""

MAX_RETRY_WAIT = 60.0
"""Upper bound, in seconds, for a single wait between retries."""

DEFAULT_RATE_LIMITER = RateLimiter(rate=9.5)
"""Shared by every client that is not given its own limiter. The API allows 10 GET requests per second per IP and rejects bursts, so requests are spaced evenly, with a margin: 9.5 per second, one every ~105 ms."""

try:
    _VERSION = version("bdns")
except PackageNotFoundError:
    _VERSION = "0.0.0+unknown"

_USER_AGENT = f"bdns-fetch/{_VERSION} (+https://github.com/cruzlorite/bdns)"

Item = dict[str, Any]


def _query(params: Mapping[str, Any]) -> dict[str, Any]:
    """Build query parameters: drop `None`, format dates, unwrap enums."""
    query = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, date):
            value = format_date_for_api_request(value)
        elif isinstance(value, Enum):
            value = value.value
        query[key] = value
    return query


def _records(document: Any) -> Iterator[Any]:
    """Yield the records in a response document, whatever its shape."""
    if document is None:
        return
    if isinstance(document, list):
        yield from document
    elif isinstance(document, dict) and isinstance(document.get("content"), list):
        yield from document["content"]
    else:
        yield document


class BDNSClient:
    """Client for the BDNS API.

    Every `fetch_*` method takes keyword arguments only. JSON endpoints
    return an iterator of records; document endpoints return `bytes`.
    Requests are lazy: an iterator sends nothing until it is consumed.

    Args:
        max_retries: Retries after the first attempt, for transient
            failures only. 0 disables retrying.
        wait_time: Initial wait between retries, in seconds. It doubles on
            each retry, plus up to as much random jitter, capped at
            `MAX_RETRY_WAIT` (or `wait_time`, if larger).
        max_workers: Threads fetching the pages of a paginated endpoint.
            The default, 1, follows the official guide, which asks for no
            concurrent calls. More threads only make a download faster;
            what makes large downloads reliable is splitting them by date
            ([`split_range`][bdns.fetch.dates.split_range]).
        progress: Show a progress bar while fetching pages. `None` shows
            it only when standard error is a terminal.
        timeout: Seconds to wait for each HTTP response.
        rate_limiter: Limiter every request acquires first. Defaults to
            `DEFAULT_RATE_LIMITER`, shared process-wide. Pass a slower one
            when several processes share an IP address.
        base_url: Root of the API.
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        wait_time: float = 2,
        max_workers: int = 1,
        progress: bool | None = None,
        timeout: float = 30,
        rate_limiter: RateLimiter | None = None,
        base_url: str = endpoints.BDNS_API_BASE_URL,
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be 0 or greater")
        if max_workers < 1:
            raise ValueError("max_workers must be 1 or greater")
        self.max_retries = max_retries
        self.wait_time = wait_time
        self.max_workers = max_workers
        self.progress = progress
        self.timeout = timeout
        self.rate_limiter = rate_limiter or DEFAULT_RATE_LIMITER
        self.base_url = base_url.rstrip("/")
        self._backoff = wait_exponential_jitter(
            initial=wait_time, max=max(MAX_RETRY_WAIT, wait_time), jitter=wait_time
        )
        self._local = threading.local()

    # ------------------------------------------------------------------ #
    # Any endpoint, by path
    # ------------------------------------------------------------------ #

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        """Fetch one JSON document from any endpoint.

        Rate limiting and retries apply as for the `fetch_*` methods.
        Parameter values are encoded the same way: dates as `dd/mm/yyyy`,
        enums by value, lists as repeated keys, `None` dropped.

        Args:
            path: Endpoint path under `base_url`, such as
                `/vpd/GE/configuracion`.
            params: Query parameters.

        Returns:
            The decoded JSON document, or `None` if the API answered 204.

        Raises:
            BDNSError: If the API reported an error.
        """
        url = self._url(path, params)
        return self._with_retries(lambda: self._decode_json(url))

    def get_bytes(self, path: str, params: Mapping[str, Any] | None = None) -> bytes:
        """Fetch a document from any endpoint as bytes.

        Args:
            path: Endpoint path under `base_url`.
            params: Query parameters, encoded as in [`get`][bdns.fetch.client.BDNSClient.get].

        Returns:
            The response body. `b""` if the API answered 204.

        Raises:
            BDNSError: If the API reported an error, including a document
                that does not exist.
        """
        url = self._url(path, params)

        def attempt() -> bytes:
            response = self._send(url)
            if response.status_code == 200:
                return response.content
            if response.status_code == 204:
                return b""
            raise self._error(response, url)

        return self._with_retries(attempt)

    def pages(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        from_page: int = 0,
        num_pages: int = 0,
    ) -> Iterator[dict[str, Any]]:
        """Fetch the pages of a paginated endpoint, in order.

        Each page is the document the API returns, with its `content` and
        its pagination fields (`totalPages`, `totalElements`...).

        Args:
            path: Endpoint path under `base_url`.
            params: Query parameters, without `page`. Include `pageSize`.
            from_page: First page to fetch (0-based).
            num_pages: Pages to fetch from `from_page`; 0 means all.

        Yields:
            Page documents. A warning is logged when pages that exist are
            left out.
        """
        params = dict(params or {})
        first = self.get(path, {**params, "page": from_page})
        if first is None:
            return
        yield first
        if not isinstance(first, dict):
            return

        total_pages = first.get("totalPages", 1)
        to_page = total_pages if num_pages == 0 else min(from_page + num_pages, total_pages)
        if to_page < total_pages:
            logger.warning(
                "Returning pages %d to %d of %d. Request all pages (num_pages=0) "
                "for the complete result.",
                from_page,
                to_page - 1,
                total_pages,
            )

        urls = [self._url(path, {**params, "page": page}) for page in range(from_page + 1, to_page)]
        progress_disabled = None if self.progress is None else not self.progress
        yield from tqdm(
            self._fetch_in_order(urls),
            total=len(urls),
            desc="Fetching pages",
            disable=progress_disabled,
        )

    # ------------------------------------------------------------------ #
    # HTTP
    # ------------------------------------------------------------------ #

    def _url(self, path: str, params: Mapping[str, Any] | None) -> str:
        """Build the full URL for `path` with `params` encoded."""
        return format_url(f"{self.base_url}/{path.lstrip('/')}", _query(params or {}))

    def _session(self) -> requests.Session:
        """Return this thread's session, creating it on first use.

        One session per thread keeps connections alive across the pages a
        worker fetches, without sharing a `Session` between threads, which
        `requests` does not guarantee to be safe.
        """
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            session.headers["User-Agent"] = _USER_AGENT
            self._local.session = session
        return session

    def _wait(self, retry_state: RetryCallState) -> float:
        """Seconds to wait before the next attempt."""
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = getattr(exc, "retry_after", None)
        if retry_after is not None:
            return min(retry_after, max(MAX_RETRY_WAIT, self.wait_time))
        return self._backoff(retry_state)

    def _log_retry(self, retry_state: RetryCallState) -> None:
        """Log a failed attempt that is about to be retried."""
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.warning(
            'Retrying after %s: "%s". Attempt %d of %d failed; waiting %.1fs.',
            type(exc).__name__,
            exc,
            retry_state.attempt_number,
            self.max_retries + 1,
            retry_state.next_action.sleep if retry_state.next_action else 0,
        )

    def _with_retries(self, attempt: Callable[[], Any]) -> Any:
        """Run `attempt`, retrying transient failures."""
        retrying = Retrying(
            stop=stop_after_attempt(self.max_retries + 1),
            retry=retry_if_exception_type((requests.RequestException, BDNSTransientError)),
            wait=self._wait,
            before_sleep=self._log_retry,
            reraise=True,
        )
        return retrying(attempt)

    def _send(self, url: str) -> requests.Response:
        """Send one rate-limited GET, without retrying."""
        self.rate_limiter.acquire()
        logger.debug("HTTP REQUEST: GET %s", url)
        start = time.monotonic()
        response = self._session().get(url, timeout=self.timeout)
        logger.debug(
            "HTTP RESPONSE: %s %s - %.1fms, %d bytes",
            response.status_code,
            response.reason,
            (time.monotonic() - start) * 1000,
            len(response.content),
        )
        return response

    def _error(self, response: requests.Response, url: str) -> BDNSError:
        """Build the exception for an error response, transient or not."""
        return error_from_response(
            status_code=response.status_code,
            url=url,
            body=response.text,
            headers=dict(response.headers),
            transient_statuses=RETRYABLE_STATUS_CODES,
            transient_codes=TRANSIENT_API_ERROR_CODES,
        )

    def _fetch_in_order(self, urls: Iterable[str]) -> Iterator[Any]:
        """Fetch `urls` concurrently and yield the documents in input order.

        A sliding window keeps `2 * max_workers` requests in flight, so
        memory stays bounded however many pages there are. If the consumer
        stops early, requests not yet started are cancelled.
        """
        url_iter = iter(urls)
        window = 2 * self.max_workers

        def fetch(url: str) -> Any:
            return self._with_retries(lambda: self._decode_json(url))

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            pending: collections.deque = collections.deque()
            try:
                for url in url_iter:
                    pending.append(executor.submit(fetch, url))
                    if len(pending) >= window:
                        break
                while pending:
                    document = pending.popleft().result()
                    next_url = next(url_iter, None)
                    if next_url is not None:
                        pending.append(executor.submit(fetch, next_url))
                    yield document
            finally:
                for future in pending:
                    future.cancel()

    def _decode_json(self, url: str) -> Any:
        """One attempt at fetching a JSON document by full URL. `None` on 204."""
        response = self._send(url)
        if response.status_code == 204:
            return None
        try:
            document = response.json()
        except ValueError:
            document = None
        if response.status_code != 200 or (
            isinstance(document, dict) and "codigo" in document and "error" in document
        ):
            raise self._error(response, url)
        return document

    # ------------------------------------------------------------------ #
    # Shapes of endpoint
    # ------------------------------------------------------------------ #

    def _list(self, path: str, params: Mapping[str, Any] | None = None) -> Iterator[Item]:
        """Records of a non-paginated endpoint."""
        yield from _records(self.get(path, params))

    def _search(
        self, path: str, params: Mapping[str, Any], from_page: int, num_pages: int
    ) -> Iterator[Item]:
        """Records of a paginated endpoint, page after page."""
        for page in self.pages(path, params, from_page=from_page, num_pages=num_pages):
            yield from _records(page)

    # ------------------------------------------------------------------ #
    # Catalogs
    # ------------------------------------------------------------------ #

    def fetch_actividades(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the economic activities catalog (`/actividades`)."""
        yield from self._list(endpoints.ACTIVIDADES, dict(vpd=vpd))

    def fetch_sectores(self) -> Iterator[Item]:
        """Fetch the sectors catalog (`/sectores`)."""
        yield from self._list(endpoints.SECTORES)

    def fetch_regiones(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the regions catalog (`/regiones`)."""
        yield from self._list(endpoints.REGIONES, dict(vpd=vpd))

    def fetch_finalidades(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the spending-policy purposes catalog (`/finalidades`)."""
        yield from self._list(endpoints.FINALIDADES, dict(vpd=vpd))

    def fetch_beneficiarios(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the beneficiary types catalog (`/beneficiarios`)."""
        yield from self._list(endpoints.BENEFICIARIOS, dict(vpd=vpd))

    def fetch_instrumentos(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the aid instruments catalog (`/instrumentos`)."""
        yield from self._list(endpoints.INSTRUMENTOS, dict(vpd=vpd))

    def fetch_reglamentos(self, *, vpd: str = "GE", ambito: Ambito | None = None) -> Iterator[Item]:
        """Fetch the regulations catalog (`/reglamentos`)."""
        yield from self._list(endpoints.REGLAMENTOS, dict(vpd=vpd, ambito=ambito))

    def fetch_objetivos(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the objectives catalog (`/objetivos`)."""
        yield from self._list(endpoints.OBJETIVOS, dict(vpd=vpd))

    def fetch_grandesbeneficiarios_anios(self) -> Iterator[Item]:
        """Fetch the years with large-beneficiary data (`/grandesbeneficiarios/anios`)."""
        yield from self._list(endpoints.GRANDESBENEFICIARIOS_ANIOS)

    # ------------------------------------------------------------------ #
    # Administrative bodies
    # ------------------------------------------------------------------ #

    def fetch_organos(self, *, vpd: str = "GE", idAdmon: TipoAdministracion) -> Iterator[Item]:
        """Fetch the administrative bodies of one type (`/organos`)."""
        yield from self._list(endpoints.ORGANOS, dict(vpd=vpd, idAdmon=idAdmon))

    def fetch_organos_agrupacion(
        self, *, vpd: str = "GE", idAdmon: TipoAdministracion
    ) -> Iterator[Item]:
        """Fetch the administrative bodies of one type, grouped (`/organos/agrupacion`)."""
        yield from self._list(endpoints.ORGANOS_AGRUPACION, dict(vpd=vpd, idAdmon=idAdmon))

    def fetch_organos_codigo(self, *, codigo: str) -> Iterator[Item]:
        """Fetch one administrative body by its code (`/organos/codigo`)."""
        yield from self._list(endpoints.ORGANOS_CODIGO, dict(codigo=codigo))

    def fetch_organos_codigoadmin(self, *, codigoAdmin: str) -> Iterator[Item]:
        """Fetch one administrative body by its admin code (`/organos/codigoAdmin`)."""
        yield from self._list(endpoints.ORGANOS_CODIGOADMIN, dict(codigoAdmin=codigoAdmin))

    # ------------------------------------------------------------------ #
    # Calls for applications (convocatorias)
    # ------------------------------------------------------------------ #

    def fetch_convocatorias(self, *, vpd: str = "GE", numConv: str) -> Iterator[Item]:
        """Fetch one call for applications by its BDNS number (`/convocatorias`)."""
        yield from self._list(endpoints.CONVOCATORIAS, dict(vpd=vpd, numConv=numConv))

    def fetch_convocatorias_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        mrr: bool = False,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        tiposBeneficiario: list[str] | None = None,
        instrumentos: list[int] | None = None,
        finalidad: int | None = None,
        ayudaEstado: str | None = None,
    ) -> Iterator[Item]:
        """Search calls for applications (`/convocatorias/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            mrr=mrr,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            tiposBeneficiario=tiposBeneficiario,
            instrumentos=instrumentos,
            finalidad=finalidad,
            ayudaEstado=ayudaEstado,
        )
        yield from self._search(endpoints.CONVOCATORIAS_BUSQUEDA, params, from_page, num_pages)

    def fetch_convocatorias_ultimas(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the most recently received calls for applications (`/convocatorias/ultimas`)."""
        yield from self._list(endpoints.CONVOCATORIAS_ULTIMAS, dict(vpd=vpd))

    def fetch_convocatorias_documentos(self, *, idDocumento: int) -> bytes:
        """Download a document attached to a call (`/convocatorias/documentos`).

        Raises:
            BDNSError: If the document does not exist or cannot be served.
        """
        return self.get_bytes(endpoints.CONVOCATORIAS_DOCUMENTOS, dict(idDocumento=idDocumento))

    def fetch_convocatorias_pdf(self, *, id: int, vpd: str) -> bytes:
        """Download a call for applications as PDF (`/convocatorias/pdf`).

        Raises:
            BDNSError: If the call does not exist or cannot be rendered.
        """
        return self.get_bytes(endpoints.CONVOCATORIAS_PDF, dict(id=id, vpd=vpd))

    # ------------------------------------------------------------------ #
    # Awards and other searches
    # ------------------------------------------------------------------ #

    def fetch_concesiones_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        fechaRegInicio: date | None = None,
        fechaRegFin: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
        instrumentos: list[int] | None = None,
        actividad: list[int] | None = None,
        finalidad: int | None = None,
    ) -> Iterator[Item]:
        """Search awards (`/concesiones/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            fechaRegInicio=fechaRegInicio,
            fechaRegFin=fechaRegFin,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            nifCif=nifCif,
            beneficiario=beneficiario,
            instrumentos=instrumentos,
            actividad=actividad,
            finalidad=finalidad,
        )
        yield from self._search(endpoints.CONCESIONES_BUSQUEDA, params, from_page, num_pages)

    def fetch_ayudasestado_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        codConcesion: str | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        fechaRegInicio: date | None = None,
        fechaRegFin: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        objetivos: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
        instrumentos: list[int] | None = None,
        actividad: list[int] | None = None,
        ayudaEstado: str | None = None,
        reglamento: list[int] | None = None,
        finalidad: int | None = None,
    ) -> Iterator[Item]:
        """Search state aid awards (`/ayudasestado/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            codConcesion=codConcesion,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            fechaRegInicio=fechaRegInicio,
            fechaRegFin=fechaRegFin,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            objetivos=objetivos,
            nifCif=nifCif,
            beneficiario=beneficiario,
            instrumentos=instrumentos,
            actividad=actividad,
            ayudaEstado=ayudaEstado,
            reglamento=reglamento,
            finalidad=finalidad,
        )
        yield from self._search(endpoints.AYUDASESTADO_BUSQUEDA, params, from_page, num_pages)

    def fetch_minimis_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        codConcesion: str | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        fechaRegInicio: date | None = None,
        fechaRegFin: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
        instrumentos: list[int] | None = None,
        actividad: list[int] | None = None,
        reglamento: list[int] | None = None,
        producto: list[int] | None = None,
        finalidad: int | None = None,
    ) -> Iterator[Item]:
        """Search de minimis aid awards (`/minimis/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            codConcesion=codConcesion,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            fechaRegInicio=fechaRegInicio,
            fechaRegFin=fechaRegFin,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            nifCif=nifCif,
            beneficiario=beneficiario,
            instrumentos=instrumentos,
            actividad=actividad,
            reglamento=reglamento,
            producto=producto,
            finalidad=finalidad,
        )
        yield from self._search(endpoints.MINIMIS_BUSQUEDA, params, from_page, num_pages)

    def fetch_partidospoliticos_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        codConcesion: str | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        fechaRegInicio: date | None = None,
        fechaRegFin: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
    ) -> Iterator[Item]:
        """Search awards to political parties (`/partidospoliticos/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            codConcesion=codConcesion,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            fechaRegInicio=fechaRegInicio,
            fechaRegFin=fechaRegFin,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            nifCif=nifCif,
            beneficiario=beneficiario,
        )
        yield from self._search(endpoints.PARTIDOSPOLITICOS_BUSQUEDA, params, from_page, num_pages)

    def fetch_grandesbeneficiarios_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        anios: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
    ) -> Iterator[Item]:
        """Search large beneficiaries (`/grandesbeneficiarios/busqueda`). Paginated."""
        params = dict(
            vpd=vpd,
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            anios=anios,
            nifCif=nifCif,
            beneficiario=beneficiario,
        )
        yield from self._search(
            endpoints.GRANDESBENEFICIARIOS_BUSQUEDA, params, from_page, num_pages
        )

    def fetch_sanciones_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        numeroConvocatoria: str | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
        tipoAdministracion: TipoAdministracion | None = None,
        organos: list[int] | None = None,
        regiones: list[int] | None = None,
        nifCif: str | None = None,
        beneficiario: int | None = None,
        instrumentos: list[int] | None = None,
        actividad: list[int] | None = None,
        finalidad: int | None = None,
    ) -> Iterator[Item]:
        """Search sanctions (`/sanciones/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            numeroConvocatoria=numeroConvocatoria,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
            tipoAdministracion=tipoAdministracion,
            organos=organos,
            regiones=regiones,
            nifCif=nifCif,
            beneficiario=beneficiario,
            instrumentos=instrumentos,
            actividad=actividad,
            finalidad=finalidad,
        )
        yield from self._search(endpoints.SANCIONES_BUSQUEDA, params, from_page, num_pages)

    def fetch_terceros(
        self,
        *,
        vpd: str = "GE",
        ambito: Ambito | None = None,
        busqueda: str | None = None,
        idPersona: int | None = None,
    ) -> Iterator[Item]:
        """Search third parties (`/terceros`).

        The official good-practice guide calls this endpoint redundant:
        [`fetch_concesiones_busqueda`][bdns.fetch.client.BDNSClient.fetch_concesiones_busqueda]
        already returns the beneficiary data.
        """
        yield from self._list(
            endpoints.TERCEROS,
            dict(vpd=vpd, ambito=ambito, busqueda=busqueda, idPersona=idPersona),
        )

    # ------------------------------------------------------------------ #
    # Strategic plans
    # ------------------------------------------------------------------ #

    def fetch_planesestrategicos(self, *, idPES: int) -> Iterator[Item]:
        """Fetch one strategic plan (`/planesestrategicos`)."""
        yield from self._list(endpoints.PLANESESTRATEGICOS, dict(idPES=idPES))

    def fetch_planesestrategicos_busqueda(
        self,
        *,
        num_pages: int = 0,
        from_page: int = 0,
        pageSize: int = 10000,
        order: Order | None = None,
        direccion: Direccion | None = None,
        vpd: str = "GE",
        descripcion: str | None = None,
        descripcionTipoBusqueda: DescripcionTipoBusqueda | None = None,
        fechaDesde: date | None = None,
        fechaHasta: date | None = None,
    ) -> Iterator[Item]:
        """Search strategic plans (`/planesestrategicos/busqueda`). Paginated."""
        params = dict(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
        )
        yield from self._search(endpoints.PLANESESTRATEGICOS_BUSQUEDA, params, from_page, num_pages)

    def fetch_planesestrategicos_documentos(self, *, idDocumento: int) -> bytes:
        """Download a document attached to a strategic plan (`/planesestrategicos/documentos`).

        Raises:
            BDNSError: If the document does not exist or cannot be served.
        """
        return self.get_bytes(
            endpoints.PLANESESTRATEGICOS_DOCUMENTOS, dict(idDocumento=idDocumento)
        )

    def fetch_planesestrategicos_vigencia(self, *, vpd: str = "GE", idPES: int) -> Iterator[Item]:
        """Fetch the validity periods of one strategic plan (`/planesestrategicos/vigencia`)."""
        yield from self._list(endpoints.PLANESESTRATEGICOS_VIGENCIA, dict(vpd=vpd, idPES=idPES))
