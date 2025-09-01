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

from typing import Any, Dict, Generator, List, Union
from datetime import datetime
import logging

from bdns.fetch.fetch import fetch, fetch_paginated, fetch_binary
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

logger = logging.getLogger(__name__)


class BDNSClient:
    """
    Client for interacting with the BDNS API programmatically.
    """

    @extract_option_values
    def fetch_actividades(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/actividades"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_ACTIVIDADES, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_sectores(self) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/sectores"""
        params = {}
        url = format_url(BDNS_API_ENDPOINT_SECTORES, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_regiones(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/regiones"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_REGIONES, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_finalidades(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/finalidades"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_FINALIDADES, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_beneficiarios(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/beneficiarios"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_TIPOS_BENEFICIARIOS, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_instrumentos(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/instrumentos"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_INSTRUMENTOS, params)
        yield from fetch(url)

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
        yield from fetch(url)

    @extract_option_values
    def fetch_objetivos(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/objetivos"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_OBJETIVOS, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_grandesbeneficiarios_anios(self) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/grandesbeneficiarios/anios"""
        params = {}
        url = format_url(BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_ANIOS, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_planesestrategicos(
        self, idPES: int = options.idPES_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos"""
        params = {"idPES": idPES}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS, params)
        yield from fetch(url)

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
        yield from fetch(url)

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
        yield from fetch(url)

    @extract_option_values
    def fetch_organos_codigo(
        self, codigo: str = options.codigo
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/codigo"""
        params = {"codigo": codigo}
        url = format_url(BDNS_API_ENDPOINT_ORGANOS_CODIGO, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_organos_codigoadmin(
        self, codigoAdmin: str = options.codigoAdmin_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/codigoAdmin"""
        params = {"codigoAdmin": codigoAdmin}
        url = format_url(BDNS_API_ENDPOINT_ORGANOS_CODIGO_ADMIN, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_convocatorias(
        self, vpd: str = options.vpd, numConv: str = options.numConv_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias"""
        params = {"vpd": vpd, "numConv": numConv}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_concesiones_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_CONCESIONES_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_ayudasestado_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_AYUDASESTADO_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
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
        yield from fetch(url)

    @extract_option_values
    def fetch_convocatorias_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_CONVOCATORIAS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_convocatorias_ultimas(
        self, vpd: str = options.vpd
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/ultimas"""
        params = {"vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_ULTIMAS, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_convocatorias_documentos(
        self, idDocumento: int = options.idDocumento_required
    ) -> bytes:
        """Fetches binary document from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos"""
        params = {"idDocumento": idDocumento}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_DOCUMENTOS, params)
        return fetch_binary(url)

    @extract_option_values
    def fetch_convocatorias_pdf(
        self, id: int = options.id_required, vpd: str = options.vpd_required
    ) -> bytes:
        """Fetches PDF document from https://www.infosubvenciones.es/bdnstrans/api/convocatorias/pdf"""
        params = {"id": id, "vpd": vpd}
        url = format_url(BDNS_API_ENDPOINT_CONVOCATORIAS_PDF, params)
        return fetch_binary(url)

    @extract_option_values
    def fetch_grandesbeneficiarios_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_minimis_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_MINIMIS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_planesestrategicos_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_PLANESESTRATEGICOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_planesestrategicos_documentos(
        self, idDocumento: int = options.idDocumento_required
    ) -> bytes:
        """Fetches binary document from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/documentos"""
        params = {"idDocumento": idDocumento}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS_DOCUMENTOS, params)
        return fetch_binary(url)

    @extract_option_values
    def fetch_planesestrategicos_vigencia(
        self, vpd: str = options.vpd, idPES: int = options.idPES_required
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetches data from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/vigencia"""
        params = {"vpd": vpd, "idPES": idPES}
        url = format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS_VIGENCIA, params)
        yield from fetch(url)

    @extract_option_values
    def fetch_partidospoliticos_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_PARTIDOSPOLITICOS_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )

    @extract_option_values
    def fetch_sanciones_busqueda(
        self,
        max_concurrent_requests: int = options.max_concurrent_requests,
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

        yield from fetch_paginated(
            BDNS_API_ENDPOINT_SANCIONES_BUSQUEDA,
            params=params,
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=max_concurrent_requests,
        )
