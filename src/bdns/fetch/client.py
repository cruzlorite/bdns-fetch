# SPDX-License-Identifier: GPL-3.0-or-later

"""Python client for the BDNS API.

[`BDNSClient`][bdns.fetch.client.BDNSClient] has one `fetch_*` method per
endpoint. Their keyword arguments are the API's own query parameters, with
the API's spelling, so the official documentation applies unchanged.

Three policies apply to every request, whatever the endpoint:

- **Rate limit.** At most 10 requests per second per process, shared by
  every client instance and worker thread. That is the limit the official
  good-practice guide sets per IP address.
- **Retries.** Network failures, HTTP 429 and 5xx, and error codes that
  signal a temporary condition (`ERR_MANTENIMIENTO_BBDD`) are retried with
  exponential backoff and jitter, honouring `Retry-After` when sent. Any
  other error is raised at once: repeating a bad request cannot fix it.
- **Pagination.** Search endpoints are paginated. Pages are fetched
  concurrently but yielded in page order, and at most `2 * max_workers`
  pages are held in memory at a time, so a slow consumer slows the
  download rather than growing memory.
"""

import collections
import concurrent.futures
import logging
import threading
import time
from collections.abc import Callable, Iterable, Iterator
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
from bdns.fetch.exceptions import (
    BDNSError,
    BDNSTransientError,
    format_bdns_error_message,
    handle_api_response,
    parse_bdns_error_response,
)
from bdns.fetch.types import (
    Ambito,
    DescripcionTipoBusqueda,
    Direccion,
    Order,
    TipoAdministracion,
)
from bdns.fetch.utils import RateLimiter, format_date_for_api_request, format_url

__all__ = ["BDNSClient", "RETRYABLE_STATUS_CODES", "TRANSIENT_API_ERROR_CODES"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#: HTTP statuses retried as transient.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

#: BDNS `codigo` values retried as transient, whatever the HTTP status.
TRANSIENT_API_ERROR_CODES = frozenset({"ERR_MANTENIMIENTO_BBDD"})

#: Upper bound, in seconds, for a single wait between retries.
MAX_RETRY_WAIT = 60.0

try:
    _VERSION = version("bdns-fetch")
except PackageNotFoundError:
    _VERSION = "0.0.0+unknown"

_USER_AGENT = f"bdns-fetch/{_VERSION} (+https://github.com/cruzlorite/bdns-fetch)"

Item = dict[str, Any]


def _query(**params: Any) -> dict[str, Any]:
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


def _retry_after(response: requests.Response) -> float | None:
    """Read `Retry-After` as seconds. HTTP-date values are ignored."""
    value = response.headers.get("Retry-After")
    try:
        return max(0.0, float(value)) if value is not None else None
    except ValueError:
        return None


class BDNSClient:
    """Client for the BDNS API.

    Every `fetch_*` method takes keyword arguments only. JSON endpoints
    return an iterator of records (or of whole pages with `return_raw`);
    document endpoints return `bytes`.

    Args:
        max_retries: Retries after the first attempt, for transient
            failures only. 0 disables retrying.
        wait_time: Initial wait between retries, in seconds. It doubles on
            each retry, plus up to as much random jitter, capped at
            `MAX_RETRY_WAIT` (or `wait_time`, if larger).
        max_workers: Threads fetching pages of a paginated endpoint.
        return_raw: Yield whole page objects instead of the records in
            them.
        progress: Show a progress bar while fetching pages. `None` shows
            it only when standard error is a terminal.
        timeout: Seconds to wait for each HTTP response.
    """

    # Shared by every instance and thread: the API allows at most 10 GET
    # requests per second per IP, however many clients or workers there are.
    _rate_limiter = RateLimiter(rate=10, per=1.0)

    def __init__(
        self,
        max_retries: int = 3,
        wait_time: float = 2,
        max_workers: int = 5,
        return_raw: bool = False,
        progress: bool | None = None,
        timeout: float = 30,
    ):
        if max_retries < 0:
            raise ValueError("max_retries must be 0 or greater")
        if max_workers < 1:
            raise ValueError("max_workers must be 1 or greater")
        self.max_retries = max_retries
        self.wait_time = wait_time
        self.max_workers = max_workers
        self.return_raw = return_raw
        self.progress = progress
        self.timeout = timeout
        self._backoff = wait_exponential_jitter(
            initial=wait_time, max=max(MAX_RETRY_WAIT, wait_time), jitter=wait_time
        )
        self._local = threading.local()

    # ------------------------------------------------------------------ #
    # HTTP
    # ------------------------------------------------------------------ #

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

    def _get(self, url: str) -> requests.Response:
        """Send one rate-limited GET, without retrying."""
        self._rate_limiter.acquire()
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

    def _error_for(self, response: requests.Response, url: str, body: str) -> BDNSError:
        """Build the exception for an error response, transient or not."""
        code, messages = parse_bdns_error_response(body)
        if response.status_code == 200:
            # The API sometimes reports an error inside a 200 response.
            error = BDNSError(
                message=f"API returned error: {format_bdns_error_message(code, messages)}",
                suggestion="Check your parameters and try again. Use --help for valid options.",
                technical_details=f"HTTP 200 from {url}\nResponse content: {body[:500]}",
            )
        else:
            error = handle_api_response(response.status_code, url, body, dict(response.headers))

        if response.status_code in RETRYABLE_STATUS_CODES or code in TRANSIENT_API_ERROR_CODES:
            return BDNSTransientError(
                error.message,
                error.suggestion,
                error.technical_details,
                retry_after=_retry_after(response),
            )
        return error

    def _fetch_json(self, url: str) -> Any:
        """Fetch one JSON document. Returns `None` for an empty (204) answer."""

        def attempt() -> Any:
            response = self._get(url)
            if response.status_code == 204:
                return None
            try:
                data = response.json()
            except ValueError:
                data = None
            is_error_payload = isinstance(data, dict) and "codigo" in data and "error" in data
            if response.status_code != 200 or is_error_payload:
                raise self._error_for(response, url, response.text)
            return data

        return self._with_retries(attempt)

    def _fetch_binary(self, url: str) -> bytes:
        """Fetch a document as bytes. Returns `b""` for an empty (204) answer."""

        def attempt() -> bytes:
            response = self._get(url)
            if response.status_code == 200:
                return response.content
            if response.status_code == 204:
                return b""
            raise self._error_for(response, url, response.text)

        return self._with_retries(attempt)

    # ------------------------------------------------------------------ #
    # Shapes of response
    # ------------------------------------------------------------------ #

    def _items(self, data: Any) -> Iterator[Any]:
        """Yield the records in a response, or the response itself if raw."""
        if data is None:
            return
        if self.return_raw:
            yield data
        elif isinstance(data, list):
            yield from data
        elif isinstance(data, dict) and isinstance(data.get("content"), list):
            yield from data["content"]
        else:
            yield data

    def _fetch(self, url: str, params: dict[str, Any] | None = None) -> Iterator[Any]:
        """Fetch a non-paginated endpoint."""
        yield from self._items(self._fetch_json(format_url(url, params or {})))

    def _fetch_paginated(
        self,
        base_url: str,
        params: dict[str, Any],
        from_page: int = 0,
        num_pages: int = 0,
    ) -> Iterator[Any]:
        """Fetch a paginated endpoint, yielding pages in order.

        Args:
            base_url: Endpoint URL.
            params: Query parameters, without `page`.
            from_page: First page to fetch (0-based).
            num_pages: Pages to fetch from `from_page`; 0 means all.

        Yields:
            Records, or whole pages if `return_raw` is set.
        """
        first = self._fetch_json(format_url(base_url, {**params, "page": from_page}))
        if not isinstance(first, dict):
            yield from self._items(first)
            return
        yield from self._items(first)

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

        pages = range(from_page + 1, to_page)
        urls = [format_url(base_url, {**params, "page": page}) for page in pages]
        progress_disabled = None if self.progress is None else not self.progress
        for data in tqdm(
            self._fetch_in_order(urls),
            total=len(urls),
            desc="Fetching pages",
            disable=progress_disabled,
        ):
            yield from self._items(data)

    def _fetch_in_order(self, urls: Iterable[str]) -> Iterator[Any]:
        """Fetch `urls` concurrently and yield the responses in input order.

        A sliding window keeps `2 * max_workers` requests in flight, so
        memory stays bounded however many pages there are. If the consumer
        stops early, requests not yet started are cancelled.
        """
        url_iter = iter(urls)
        window = 2 * self.max_workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            pending: collections.deque = collections.deque()
            try:
                for url in url_iter:
                    pending.append(executor.submit(self._fetch_json, url))
                    if len(pending) >= window:
                        break
                while pending:
                    data = pending.popleft().result()
                    next_url = next(url_iter, None)
                    if next_url is not None:
                        pending.append(executor.submit(self._fetch_json, next_url))
                    yield data
            finally:
                for future in pending:
                    future.cancel()

    # ------------------------------------------------------------------ #
    # Catalogs
    # ------------------------------------------------------------------ #

    def fetch_actividades(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the economic activities catalog (`/actividades`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_ACTIVIDADES, _query(vpd=vpd))

    def fetch_sectores(self) -> Iterator[Item]:
        """Fetch the sectors catalog (`/sectores`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_SECTORES)

    def fetch_regiones(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the regions catalog (`/regiones`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_REGIONES, _query(vpd=vpd))

    def fetch_finalidades(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the spending-policy purposes catalog (`/finalidades`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_FINALIDADES, _query(vpd=vpd))

    def fetch_beneficiarios(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the beneficiary types catalog (`/beneficiarios`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_TIPOS_BENEFICIARIOS, _query(vpd=vpd))

    def fetch_instrumentos(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the aid instruments catalog (`/instrumentos`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_INSTRUMENTOS, _query(vpd=vpd))

    def fetch_reglamentos(self, *, vpd: str = "GE", ambito: Ambito | None = None) -> Iterator[Item]:
        """Fetch the regulations catalog (`/reglamentos`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_REGLAMENTOS, _query(vpd=vpd, ambito=ambito)
        )

    def fetch_objetivos(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the objectives catalog (`/objetivos`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_OBJETIVOS, _query(vpd=vpd))

    def fetch_grandesbeneficiarios_anios(self) -> Iterator[Item]:
        """Fetch the years with large-beneficiary data (`/grandesbeneficiarios/anios`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_ANIOS)

    # ------------------------------------------------------------------ #
    # Administrative bodies
    # ------------------------------------------------------------------ #

    def fetch_organos(self, *, vpd: str = "GE", idAdmon: TipoAdministracion) -> Iterator[Item]:
        """Fetch the administrative bodies of one type (`/organos`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_ORGANOS, _query(vpd=vpd, idAdmon=idAdmon)
        )

    def fetch_organos_agrupacion(
        self, *, vpd: str = "GE", idAdmon: TipoAdministracion
    ) -> Iterator[Item]:
        """Fetch the administrative bodies of one type, grouped (`/organos/agrupacion`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_ORGANOS_AGRUPACION, _query(vpd=vpd, idAdmon=idAdmon)
        )

    def fetch_organos_codigo(self, *, codigo: str) -> Iterator[Item]:
        """Fetch one administrative body by its code (`/organos/codigo`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_ORGANOS_CODIGO, _query(codigo=codigo))

    def fetch_organos_codigoadmin(self, *, codigoAdmin: str) -> Iterator[Item]:
        """Fetch one administrative body by its admin code (`/organos/codigoAdmin`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_ORGANOS_CODIGO_ADMIN, _query(codigoAdmin=codigoAdmin)
        )

    # ------------------------------------------------------------------ #
    # Calls for applications (convocatorias)
    # ------------------------------------------------------------------ #

    def fetch_convocatorias(self, *, vpd: str = "GE", numConv: str) -> Iterator[Item]:
        """Fetch one call for applications by its BDNS number (`/convocatorias`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_CONVOCATORIAS, _query(vpd=vpd, numConv=numConv)
        )

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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_CONVOCATORIAS_BUSQUEDA, params, from_page, num_pages
        )

    def fetch_convocatorias_ultimas(self, *, vpd: str = "GE") -> Iterator[Item]:
        """Fetch the most recently received calls for applications (`/convocatorias/ultimas`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_CONVOCATORIAS_ULTIMAS, _query(vpd=vpd))

    def fetch_convocatorias_documentos(self, *, idDocumento: int) -> bytes:
        """Download a document attached to a call (`/convocatorias/documentos`).

        Raises:
            BDNSError: If the document does not exist or cannot be served.
        """
        url = format_url(
            endpoints.BDNS_API_ENDPOINT_CONVOCATORIAS_DOCUMENTOS, _query(idDocumento=idDocumento)
        )
        return self._fetch_binary(url)

    def fetch_convocatorias_pdf(self, *, id: int, vpd: str) -> bytes:
        """Download a call for applications as PDF (`/convocatorias/pdf`).

        Raises:
            BDNSError: If the call does not exist or cannot be rendered.
        """
        url = format_url(endpoints.BDNS_API_ENDPOINT_CONVOCATORIAS_PDF, _query(id=id, vpd=vpd))
        return self._fetch_binary(url)

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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_CONCESIONES_BUSQUEDA, params, from_page, num_pages
        )

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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_AYUDASESTADO_BUSQUEDA, params, from_page, num_pages
        )

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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_MINIMIS_BUSQUEDA, params, from_page, num_pages
        )

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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_PARTIDOSPOLITICOS_BUSQUEDA, params, from_page, num_pages
        )

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
        params = _query(
            vpd=vpd,
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            anios=anios,
            nifCif=nifCif,
            beneficiario=beneficiario,
        )
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_BUSQUEDA, params, from_page, num_pages
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
        params = _query(
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
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_SANCIONES_BUSQUEDA, params, from_page, num_pages
        )

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
        `fetch_concesiones_busqueda` already returns the beneficiary data.
        """
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_TERCEROS,
            _query(vpd=vpd, ambito=ambito, busqueda=busqueda, idPersona=idPersona),
        )

    # ------------------------------------------------------------------ #
    # Strategic plans
    # ------------------------------------------------------------------ #

    def fetch_planesestrategicos(self, *, idPES: int) -> Iterator[Item]:
        """Fetch one strategic plan (`/planesestrategicos`)."""
        yield from self._fetch(endpoints.BDNS_API_ENDPOINT_PLANESESTRATEGICOS, _query(idPES=idPES))

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
        params = _query(
            pageSize=pageSize,
            order=order,
            direccion=direccion,
            vpd=vpd,
            descripcion=descripcion,
            descripcionTipoBusqueda=descripcionTipoBusqueda,
            fechaDesde=fechaDesde,
            fechaHasta=fechaHasta,
        )
        yield from self._fetch_paginated(
            endpoints.BDNS_API_ENDPOINT_PLANESESTRATEGICOS_BUSQUEDA, params, from_page, num_pages
        )

    def fetch_planesestrategicos_documentos(self, *, idDocumento: int) -> bytes:
        """Download a document attached to a strategic plan (`/planesestrategicos/documentos`).

        Raises:
            BDNSError: If the document does not exist or cannot be served.
        """
        url = format_url(
            endpoints.BDNS_API_ENDPOINT_PLANESESTRATEGICOS_DOCUMENTOS,
            _query(idDocumento=idDocumento),
        )
        return self._fetch_binary(url)

    def fetch_planesestrategicos_vigencia(self, *, vpd: str = "GE", idPES: int) -> Iterator[Item]:
        """Fetch the validity periods of one strategic plan (`/planesestrategicos/vigencia`)."""
        yield from self._fetch(
            endpoints.BDNS_API_ENDPOINT_PLANESESTRATEGICOS_VIGENCIA, _query(vpd=vpd, idPES=idPES)
        )
