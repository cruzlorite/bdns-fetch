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

from datetime import datetime
import asyncio

import typer

from bdns.api.utils import format_date_for_api_request, format_url
from bdns.api.types import Order, Direccion, TipoAdministracion, DescripcionTipoBusqueda
from bdns.api.fetch_write import fetch_and_write_paginated
from bdns.api.commands import options
from bdns.api.endpoints import BDNS_API_ENDPOINT_PLANESESTRATEGICOS


def ayudasestado_busqueda(
    ctx: typer.Context,
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
    organos: str = options.organos,
    regiones: str = options.regiones,
    nifCif: str = options.nifCif,
    beneficiario: int = options.beneficiario,
    instrumentos: str = options.instrumentos,
    actividad: str = options.actividad,
    finalidad: int = options.finalidad,
) -> None:
    """
    Fetches ayudas estado data from the BDNS API based on search parameters.
    """
    params = {
        "vpd": vpd,
        "pageSize": pageSize,
        "order": order,
        "direccion": direccion,
        "descripcion": descripcion,
        "tipoAdministracion": tipoAdministracion,
        "descripcionTipoBusqueda": descripcionTipoBusqueda,
        "fechaDesde": format_date_for_api_request(fechaDesde),
        "fechaHasta": format_date_for_api_request(fechaHasta),
        "numeroConvocatoria": numeroConvocatoria,
        "organos": organos,
        "regiones": regiones,
        "nifCif": nifCif,
        "beneficiario": beneficiario,
        "instrumentos": instrumentos,
        "actividad": actividad,
        "finalidad": finalidad,
    }
    asyncio.run(
        fetch_and_write_paginated(
            url=format_url(BDNS_API_ENDPOINT_PLANESESTRATEGICOS, params),
            output_file=ctx.obj["output_file"],
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=ctx.obj["max_concurrent_requests"],
        )
    )
