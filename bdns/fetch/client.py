# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import logging
from typing import Any, Dict, Generator, List
from datetime import date
import concurrent.futures

import requests
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed

from bdns.fetch.utils import (
    format_url,
    format_date_for_api_request,
    extract_option_values,
)
from bdns.fetch.endpoints import *
from bdns.fetch.types import (
    TipoAdministracion,
    Ambito,
    Order,
    Direccion,
    DescripcionTipoBusqueda,
)
from bdns.fetch import options

# Use a named logger for this module, don't configure at import time
logger = logging.getLogger(__name__)

# Add a NullHandler to prevent logging errors if no handlers are configured
logger.addHandler(logging.NullHandler())


class BDNSClient:
    """
    Client for interacting with the BDNS API programmatically.

    Provides configurable retry behavior for all BDNS API endpoints.
    """

    def __init__(
        self,
        max_retries: int = 3,
        wait_time: int = 2,
        max_workers: int = 5,
        return_raw: bool = False,
    ):
        """
        Initialize the BDNS client with configurable retry settings.

        Args:
            max_retries (int): Maximum number of retries for failed requests. Default: 3
            wait_time (int): Time to wait between retries in seconds. Default: 2
            max_workers (int): Maximum number of concurrent threads for paginated requests. Default: 5
            return_raw (bool): Return raw page objects instead of individual items from paginated responses. Default: False
        """
        self.max_retries = max_retries
        self.wait_time = wait_time
        self.max_workers = max_workers
        self.return_raw = return_raw

    def _log_retry_attempt(self, retry_state):
        """Log retry attempts with instance-specific retry count."""
        exc = retry_state.outcome.exception()
        exc_type = type(exc).__name__ if exc else "None"
        exc_msg = str(exc) if exc else "No exception"

        logger.warning(
            f' Retrying due to {exc_type}: "{exc_msg}". '
            f"Attempt {retry_state.attempt_number} of {self.max_retries}."
        )

    def _create_retry_decorator(self):
        """Create a retry decorator with instance-specific settings."""
        return retry(
            stop=stop_after_attempt(self.max_retries),
            retry=retry_if_exception_type((requests.RequestException,)),
            wait=wait_fixed(self.wait_time),
            before_sleep=self._log_retry_attempt,
        )

    def _fetch_single_page(self, url: str) -> Dict[str, Any]:
        """
        Fetches data from a single page with error handling and retries.
        """
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def fetch_with_retries():
            # Log the outgoing request
            logger.debug(f"HTTP REQUEST: GET {url}")

            import time

            start_time = time.time()

            response = requests.get(url, timeout=30)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Log response details
            logger.debug(
                f"HTTP RESPONSE: {response.status_code} {response.reason} - {response_time:.1f}ms"
            )
            logger.debug(f"Response Headers: {dict(response.headers)}")

            try:
                data = response.json()
            except ValueError:
                data = response.text

            # Log response content size and basic info
            content_size = len(response.text)
            logger.debug(f"Response Content-Length: {content_size} bytes")

            if isinstance(data, dict):
                if "content" in data and isinstance(data["content"], list):
                    logger.debug(f"Response contains {len(data['content'])} items")
                if "totalPages" in data:
                    logger.debug(f"Total pages available: {data['totalPages']}")
                if "number" in data:
                    logger.debug(f"Current page: {data['number']}")

            # Handle API errors
            if isinstance(data, dict) and "codigo" in data and "error" in data:
                logger.error(f"API Error Response: {data}")
                from bdns.fetch.exceptions import BDNSError

                tech_details = (
                    f"API error code {data['codigo']}: {data['error']} from {url}"
                )
                tech_details += f"\nResponse status: {response.status_code}"
                tech_details += f"\nResponse headers: {dict(response.headers)}"
                tech_details += f"\nFull response data: {data}"

                raise BDNSError(
                    message=f"API returned error: {data['error']}",
                    suggestion="Check your parameters and try again. Use --help for valid options.",
                    technical_details=tech_details,
                )

            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.reason}")
                logger.error(f"Response body: {data}")
                from bdns.fetch.exceptions import handle_api_error

                response_text = (
                    json.dumps(data) if isinstance(data, dict) else str(data)
                )
                raise handle_api_error(
                    response.status_code, url, response_text, dict(response.headers)
                )

            return data

        return fetch_with_retries()

    def _fetch_paginated(
        self,
        base_url: str,
        params: Dict[str, Any],
        from_page: int = 0,
        num_pages: int = 0,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Synchronous generator for paginated data fetching.
        """
        # Fetch the first page to get total page count
        first_page_params = {**params, "page": from_page}
        first_page_url = format_url(base_url, first_page_params)

        try:
            first_response = self._fetch_single_page(first_page_url)
            total_pages = first_response.get("totalPages", 1)

            # Handle first page based on return_raw setting
            if self.return_raw:
                # Yield the entire first page response
                yield first_response
            else:
                # Yield individual items from the first page
                for item in first_response["content"]:
                    yield item

            # Determine pages to fetch
            to_page = (
                total_pages
                if num_pages == 0
                else min(from_page + num_pages, total_pages)
            )

            # # If there are more pages, fetch them sequentially
            # if from_page + 1 < to_page:
            #     pages_to_fetch = list(range(from_page + 1, to_page))

            #     for page in tqdm(
            #         pages_to_fetch,
            #         desc=f"Fetching from page {from_page + 1} to page {to_page} out of {total_pages} pages",
            #     ):
            #         page_params = {**params, "page": page}
            #         page_url = format_url(base_url, page_params)
            #         response = self._fetch_single_page(page_url)
            #         content = response.get("content", [])
            #         if isinstance(content, list):
            #             for item in content:
            #                 yield item

            pages_to_fetch = list(range(from_page + 1, to_page))
            urls = [
                format_url(base_url, {**params, "page": page})
                for page in pages_to_fetch
            ]

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:
                # Submit all tasks, getting a future for each
                futures = [
                    executor.submit(self._fetch_single_page, url) for url in urls
                ]

                # Process results as they complete
                for future in tqdm(
                    concurrent.futures.as_completed(futures),
                    total=len(futures),
                    desc="Fetching pages",
                ):
                    data = future.result()
                    if isinstance(data, dict):
                        if self.return_raw:
                            # Yield the entire page response
                            yield data
                        else:
                            # Yield individual items from content
                            for item in data["content"]:
                                yield item
                    futures.remove(future)

        except Exception as e:
            logger.error(f"Error in paginated fetch: {e}")
            raise

    def _fetch(
        self, url: str, params: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetches data from a single non-paginated endpoint with retries and error handling.
        """
        # Format URL with parameters
        if params:
            full_url = format_url(url, params)
        else:
            full_url = url

        # Use the synchronous single page fetch method
        data = self._fetch_single_page(full_url)

        # Handle return_raw setting
        if self.return_raw:
            # Yield the entire response object as returned by _fetch_single_page
            yield data
        else:
            # Yield individual items based on response structure
            if isinstance(data, list):
                # Direct list response
                for item in data:
                    yield item
            elif isinstance(data, dict):
                if "content" in data and isinstance(data["content"], list):
                    # Paginated response structure (but single page)
                    for item in data["content"]:
                        yield item
                else:
                    # Single object response
                    yield data
            else:
                logger.warning(f"Unexpected response type: {type(data)}")
                yield data

    def _fetch_binary(self, url: str) -> bytes:
        """
        Synchronously fetches binary content from a URL using requests.
        """
        from bdns.fetch.exceptions import handle_api_response

        logger.debug(f"Starting binary fetch from: {url}")

        try:
            response = requests.get(url, timeout=30)

            logger.debug(
                f"Binary response: {response.status_code} - Content-Type: {response.headers.get('content-type', 'unknown')}"
            )

            if response.status_code == 200:
                content = response.content
                logger.debug(f"Binary content fetched: {len(content)} bytes")
                return content
            elif response.status_code == 204:
                logger.debug("No content returned (204)")
                return b""
            elif response.status_code == 404:
                logger.warning(f"Resource not found (404) for URL: {url}")
                return b""
            else:
                # Handle API errors using existing error handler
                raise handle_api_response(
                    response.status_code, url, response.text, dict(response.headers)
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for binary fetch: {e}")
            raise

    @extract_option_values
    def fetch_actividades(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/actividades"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_ACTIVIDADES, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_sectores(self) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/sectores"""
        params = {}
        url = format_url(BDNS_API_ENDPOINT_SECTORES, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_regiones(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/regiones"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_REGIONES, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_finalidades(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/finalidades"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_FINALIDADES, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_beneficiarios(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/beneficiarios"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_TIPOS_BENEFICIARIOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_instrumentos(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/instrumentos"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_INSTRUMENTOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_reglamentos(
        self, vpd: str = options.vpd, ambito: Ambito = options.ambito
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/reglamentos"""
        params = {
            "vpd": vpd,
            "ambito": ambito.value if hasattr(ambito, "value") else ambito,
        }
        url = format_url(BDNS_API_ENDPOINT_REGLAMENTOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_objetivos(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/objetivos"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_OBJETIVOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_grandesbeneficiarios_anios(self) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/grandesbeneficiarios/anios"""
        params = {}
        url = format_url(BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_ANIOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_planesestrategicos(
        self, idPES: int = options.idPES_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos"""
        params = {"idPES": idPES}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_organos(
        self,
        vpd: str = options.vpd,
        idAdmon: TipoAdministracion = options.idAdmon_required,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos"""
        params = {
            "vpd": vpd,
            "idAdmon": idAdmon.value if hasattr(idAdmon, "value") else idAdmon,
        }
        url = format_url(BDNS_API_ENDPOINT_ORGANOS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_organos_agrupacion(
        self,
        vpd: str = options.vpd,
        idAdmon: TipoAdministracion = options.idAdmon_required,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/agrupacion"""
        params = {
            "vpd": vpd,
            "idAdmon": idAdmon.value if hasattr(idAdmon, "value") else idAdmon,
        }
        url = format_url(BDNS_API_ENDPOINT_ORGANOS_AGRUPACION, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_organos_codigo(
        self, codigo: str = options.codigo
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/codigo"""
        params = {"codigo": codigo}
        url = format_url(BDNS_API_ENDPOINT_ORGANOS_CODIGO, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_organos_codigoadmin(
        self, codigoAdmin: str = options.codigoAdmin_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/codigoAdmin"""
        params = {"codigoAdmin": codigoAdmin}
        url = format_url(BDNS_API_ENDPOINT_ORGANOS_CODIGO_ADMIN, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_convocatorias(
        self, vpd: str = options.vpd, numConv: str = options.numConv_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias"""
        params = {"vpd": vpd, "numConv": numConv}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_concesiones_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
        instrumentos: List[int] = options.instrumentos,
        actividad: List[int] = options.actividad,
        finalidad: int = options.finalidad,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "organos": organos,
            "regiones": regiones,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
            "instrumentos": instrumentos,
            "actividad": actividad,
            "finalidad": finalidad,
            "numeroConvocatoria": numeroConvocatoria,
        }
        # Remove None values to keep URL clean
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_CONCESIONES_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_ayudasestado_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        codConcesion: str = options.codConcesion,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        objetivos: List[int] = options.objetivos,
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
        instrumentos: List[int] = options.instrumentos,
        actividad: List[int] = options.actividad,
        ayudaEstado: str = options.ayudaEstado,
        reglamento: int = options.reglamento,
        finalidad: int = options.finalidad,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/ayudasestado/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "organos": organos,
            "regiones": regiones,
            "objetivos": objetivos,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
            "instrumentos": instrumentos,
            "actividad": actividad,
            "numeroConvocatoria": numeroConvocatoria,
            "codConcesion": codConcesion,
            "ayudaEstado": ayudaEstado,
            "reglamento": reglamento,
            "finalidad": finalidad,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_AYUDASESTADO_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_terceros(
        self,
        vpd: str = options.vpd,
        ambito: Ambito = options.ambito,
        busqueda: str = options.busqueda,
        idPersona: int = options.idPersona,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/terceros

        Args:
            vpd: Identificador del portal (e.g., "A02")
            ambito: Ámbito donde buscar - C, A, M, S, P, G
            busqueda: Filtro para descripción (mín. 3 caracteres)
            idPersona: Identificador de la persona
        """
        params = {
            "vpd": vpd,
            "ambito": ambito,
            "busqueda": busqueda,
            "idPersona": idPersona,
        }
        url = format_url(BDNS_API_ENDPOINT_TERCEROS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_convocatorias_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        mrr: bool = options.mrr,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        tiposBeneficiario: List[str] = options.tiposBeneficiario_str,
        instrumentos: List[int] = options.instrumentos,
        finalidad: int = options.finalidad,
        ayudaEstado: str = options.ayudaEstado,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "numeroConvocatoria": numeroConvocatoria,
            "mrr": mrr,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "organos": organos,
            "regiones": regiones,
            "tiposBeneficiario": tiposBeneficiario,
            "instrumentos": instrumentos,
            "finalidad": finalidad,
            "ayudaEstado": ayudaEstado,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_CONVOCATORIAS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_convocatorias_ultimas(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/ultimas"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_ULTIMAS, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_convocatorias_documentos(
        self, idDocumento: int = options.idDocumento_required
    ) -> bytes:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos"""
        params = {"idDocumento": idDocumento}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_DOCUMENTOS, params)
        return self._fetch_binary(url)

    @extract_option_values
    def fetch_convocatorias_pdf(
        self, id: int = options.id_required, vpd: str = options.vpd_required
    ) -> bytes:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/pdf"""
        params = {"id": id, "vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_PDF, params)
        return self._fetch_binary(url)

    @extract_option_values
    def fetch_grandesbeneficiarios_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        anios: List[int] = options.anios,
        anio: str = None,  # Alias for backward compatibility
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/grandesbeneficiarios/busqueda"""
        # Use anio if provided, otherwise use anios
        years_param = anio if anio is not None else anios

        params = {
            "vpd": vpd,
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "anios": years_param,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_minimis_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        codConcesion: str = options.codConcesion,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
        instrumentos: List[int] = options.instrumentos,
        actividad: List[int] = options.actividad,
        reglamento: int = options.reglamento,
        producto: int = options.producto,
        finalidad: int = options.finalidad,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/minimis/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "numeroConvocatoria": numeroConvocatoria,
            "codConcesion": codConcesion,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "organos": organos,
            "regiones": regiones,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
            "instrumentos": instrumentos,
            "actividad": actividad,
            "reglamento": reglamento,
            "producto": producto,
            "finalidad": finalidad,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_MINIMIS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_planesestrategicos_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_PLANESESTRATEGICOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_planesestrategicos_documentos(
        self, idDocumento: int = options.idDocumento_required
    ) -> bytes:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/documentos"""
        params = {"idDocumento": idDocumento}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS_DOCUMENTOS, params)
        return self._fetch_binary(url)

    @extract_option_values
    def fetch_planesestrategicos_vigencia(
        self, vpd: str = options.vpd, idPES: int = options.idPES_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/vigencia"""
        params = {"vpd": vpd, "idPES": idPES}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS_VIGENCIA, params)
        yield from self._fetch(url)

    @extract_option_values
    def fetch_partidospoliticos_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        codConcesion: str = options.codConcesion,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/partidospoliticos/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "numeroConvocatoria": numeroConvocatoria,
            "codConcesion": codConcesion,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "organos": organos,
            "regiones": regiones,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_PARTIDOSPOLITICOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )

    @extract_option_values
    def fetch_sanciones_busqueda(
        self,
        num_pages: int = options.num_pages,
        from_page: int = options.from_page,
        pageSize: int = options.pageSize,
        order: Order = options.order,
        direccion: Direccion = options.direccion,
        vpd: str = options.vpd,
        descripcion: str = options.descripcion,
        descripcionTipoBusqueda: DescripcionTipoBusqueda = options.descripcionTipoBusqueda,
        numeroConvocatoria: str = options.numeroConvocatoria,
        fechaDesde: date = options.fechaDesde,
        fechaHasta: date = options.fechaHasta,
        tipoAdministracion: TipoAdministracion = options.tipoAdministracion,
        organos: List[int] = options.organos,
        regiones: List[int] = options.regiones,
        nifCif: str = options.nifCif,
        beneficiario: int = options.beneficiario,
        instrumentos: List[int] = options.instrumentos,
        actividad: List[int] = options.actividad,
        finalidad: int = options.finalidad,
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/sanciones/busqueda"""
        params = {
            "pageSize": pageSize,
            "order": order.value if order else None,
            "direccion": direccion.value if direccion else None,
            "vpd": vpd,
            "descripcion": descripcion,
            "descripcionTipoBusqueda": descripcionTipoBusqueda.value
            if descripcionTipoBusqueda
            else None,
            "numeroConvocatoria": numeroConvocatoria,
            "fechaDesde": format_date_for_api_request(fechaDesde)
            if fechaDesde
            else None,
            "fechaHasta": format_date_for_api_request(fechaHasta)
            if fechaHasta
            else None,
            "tipoAdministracion": tipoAdministracion.value
            if tipoAdministracion
            else None,
            "organos": organos,
            "regiones": regiones,
            "nifCif": nifCif,
            "beneficiario": beneficiario,
            "instrumentos": instrumentos,
            "actividad": actividad,
            "finalidad": finalidad,
        }
        params = {k: v for k, v in params.items() if v is not None}

        yield from self._fetch_paginated(
            BDNS_API_ENDPOINT_SANCIONES_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
        )
