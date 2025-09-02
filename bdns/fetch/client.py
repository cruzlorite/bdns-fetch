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

import sys
import json
import asyncio
import logging
from typing import Any, Dict, Generator, List, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import requests
from tqdm.asyncio import tqdm
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

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)


class BDNSClient:
    """
    Client for interacting with the BDNS API programmatically.

    Provides configurable retry behavior and concurrent request handling
    for all BDNS API endpoints.
    """

    def __init__(
        self, max_retries: int = 3, wait_time: int = 2, max_concurrent_requests: int = 5
    ):
        """
        Initialize the BDNS client with configurable retry and concurrency settings.

        Args:
            max_retries (int): Maximum number of retries for failed requests. Default: 3
            wait_time (int): Time to wait between retries in seconds. Default: 2
            max_concurrent_requests (int): Maximum concurrent requests for pagination. Default: 5
        """
        self.max_retries = max_retries
        self.wait_time = wait_time
        self.max_concurrent_requests = max_concurrent_requests

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
            retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
            wait=wait_fixed(self.wait_time),
            before_sleep=self._log_retry_attempt,
        )

    async def _async_fetch_page(self, semaphore, session, url):
        """
        Fetches data from a single page with error handling and retries.
        """
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        async def fetch_with_retries():
            async with semaphore:
                # Log the outgoing request
                logger.debug(f"HTTP REQUEST: GET {url}")

                start_time = asyncio.get_event_loop().time()
                async with session.get(url) as resp:
                    end_time = asyncio.get_event_loop().time()
                    response_time = (
                        end_time - start_time
                    ) * 1000  # Convert to milliseconds

                    # Log response details
                    logger.debug(
                        f"HTTP RESPONSE: {resp.status} {resp.reason} - {response_time:.1f}ms"
                    )
                    logger.debug(f"Response Headers: {dict(resp.headers)}")

                    data = await resp.json()

                    # Log response content size and basic info
                    content_size = (
                        len(await resp.text()) if hasattr(resp, "text") else 0
                    )
                    logger.debug(f"Response Content-Length: {content_size} bytes")

                    if isinstance(data, dict):
                        if "content" in data and isinstance(data["content"], list):
                            logger.debug(
                                f"Response contains {len(data['content'])} items"
                            )
                        if "totalPages" in data:
                            logger.debug(f"Total pages available: {data['totalPages']}")
                        if "number" in data:
                            logger.debug(f"Current page: {data['number']}")

                    # Handle API errors
                    if "codigo" in data and "error" in data:
                        logger.error(f"API Error Response: {data}")
                        from bdns.fetch.exceptions import BDNSError

                        tech_details = f"API error code {data['codigo']}: {data['error']} from {url}"
                        tech_details += f"\nResponse status: {resp.status}"
                        tech_details += f"\nResponse headers: {dict(resp.headers)}"
                        tech_details += f"\nFull response data: {data}"

                        raise BDNSError(
                            message=f"API returned error: {data['error']}",
                            suggestion="Check your parameters and try again. Use --help for valid options.",
                            technical_details=tech_details,
                        )

                    if resp.status != 200:
                        logger.error(f"HTTP Error {resp.status}: {resp.reason}")
                        logger.error(f"Response body: {data}")
                        from bdns.fetch.exceptions import handle_api_error

                        response_text = (
                            json.dumps(data) if isinstance(data, dict) else str(data)
                        )
                        raise handle_api_error(
                            resp.status, url, response_text, dict(resp.headers)
                        )

                    return data

        return await fetch_with_retries()

    async def _async_fetch_paginated_generator(
        self,
        base_url: str,
        params: Dict[str, Any],
        from_page: int = 0,
        num_pages: int = 0,
        max_concurrent_requests: int = None,
    ):
        """
        Async generator that fetches paginated data with concurrent requests.
        """
        if max_concurrent_requests is None:
            max_concurrent_requests = self.max_concurrent_requests

        semaphore = asyncio.Semaphore(max_concurrent_requests)

        async with aiohttp.ClientSession() as session:
            # Fetch the first page to get total page count
            first_page_params = {**params, "page": from_page}
            first_page_url = format_url(base_url, first_page_params)

            try:
                first_response = await self._async_fetch_page(
                    semaphore, session, first_page_url
                )
                total_pages = first_response.get("totalPages", 1)

                # Yield items from the first page
                content = first_response.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        yield item

                # Determine pages to fetch
                to_page = (
                    total_pages
                    if num_pages == 0
                    else min(from_page + num_pages, total_pages)
                )

                # If there are more pages, fetch them concurrently
                if from_page + 1 < to_page:
                    # Create tasks for remaining pages
                    tasks = []
                    for page in range(from_page + 1, to_page):
                        page_params = {**params, "page": page}
                        page_url = format_url(base_url, page_params)
                        tasks.append(
                            asyncio.create_task(
                                self._async_fetch_page(semaphore, session, page_url)
                            )
                        )

                    # Process completed tasks as they finish
                    for task in tqdm(
                        asyncio.as_completed(tasks),
                        total=len(tasks),
                        desc="Fetching pages",
                    ):
                        try:
                            response = await task
                            content = response.get("content", [])
                            if isinstance(content, list):
                                for item in content:
                                    yield item
                        except Exception as e:
                            logger.error(f"Error fetching page: {e}")
                            continue

            except Exception as e:
                logger.error(f"Error in paginated fetch: {e}")
                raise

    def _fetch_paginated(
        self,
        base_url: str,
        params: Dict[str, Any],
        from_page: int = 0,
        num_pages: int = 0,
        max_concurrent_requests: int = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Synchronous generator wrapper for paginated data fetching.
        """
        if max_concurrent_requests is None:
            max_concurrent_requests = self.max_concurrent_requests

        # Run the async generator in a new event loop
        def run_async_generator():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = self._async_fetch_paginated_generator(
                    base_url, params, from_page, num_pages, max_concurrent_requests
                )

                async def collect_items():
                    items = []
                    async for item in async_gen:
                        items.append(item)
                    return items

                return loop.run_until_complete(collect_items())
            finally:
                loop.close()

        # Use ThreadPoolExecutor to avoid blocking the main thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_generator)
            items = future.result()

        # Yield each item
        for item in items:
            yield item

    async def _async_fetch_single(self, session, url):
        """
        Fetches data from a single URL with error handling and retries.
        """
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        async def fetch_with_retries():
            # Log the outgoing request
            logger.debug(f"HTTP REQUEST: GET {url}")

            start_time = asyncio.get_event_loop().time()
            async with session.get(url) as resp:
                end_time = asyncio.get_event_loop().time()
                response_time = (
                    end_time - start_time
                ) * 1000  # Convert to milliseconds

                # Log response details
                logger.debug(
                    f"HTTP RESPONSE: {resp.status} {resp.reason} - {response_time:.1f}ms"
                )
                logger.debug(f"Response Headers: {dict(resp.headers)}")

                data = await resp.json()

                # Log response content size and basic info
                content_size = len(await resp.text()) if hasattr(resp, "text") else 0
                logger.debug(f"Response Content-Length: {content_size} bytes")

                if isinstance(data, dict):
                    if "content" in data and isinstance(data["content"], list):
                        logger.debug(f"Response contains {len(data['content'])} items")
                elif isinstance(data, list):
                    logger.debug(f"Response contains {len(data)} items")

                # Handle API errors
                if isinstance(data, dict) and "codigo" in data and "error" in data:
                    logger.error(f"API Error Response: {data}")
                    from bdns.fetch.exceptions import BDNSAPIError

                    tech_details = (
                        f"API error code {data['codigo']}: {data['error']} from {url}"
                    )
                    tech_details += f"\nResponse status: {resp.status}"
                    tech_details += f"\nResponse headers: {dict(resp.headers)}"
                    tech_details += f"\nFull response data: {data}"

                    raise BDNSAPIError(
                        message=f"API returned error: {data['error']}",
                        suggestion="Check your parameters and try again. Use --help for valid options.",
                        technical_details=tech_details,
                    )

                if resp.status != 200:
                    logger.error(f"HTTP Error {resp.status}: {resp.reason}")
                    logger.error(f"Response body: {data}")
                    from bdns.fetch.exceptions import handle_api_error

                    response_text = (
                        json.dumps(data) if isinstance(data, dict) else str(data)
                    )
                    raise handle_api_error(
                        resp.status, url, response_text, dict(resp.headers)
                    )

                return data

        return await fetch_with_retries()

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

        # Run the async fetch in a new event loop
        def run_async_fetch():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:

                async def fetch_data():
                    async with aiohttp.ClientSession() as session:
                        return await self._async_fetch_single(session, full_url)

                return loop.run_until_complete(fetch_data())
            finally:
                loop.close()

        # Use ThreadPoolExecutor to avoid blocking the main thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_fetch)
            data = future.result()

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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
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
        fechaDesde: datetime = options.fechaDesde,
        fechaHasta: datetime = options.fechaHasta,
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
            max_concurrent_requests=self.max_concurrent_requests,
        )
