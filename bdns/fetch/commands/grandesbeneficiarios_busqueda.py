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

import asyncio
from typing import List

import typer

from bdns.fetch.utils import format_url
from bdns.fetch.types import Order, Direccion
from bdns.fetch.fetch_write import fetch_and_write_paginated
from bdns.fetch.commands import options
from bdns.fetch.endpoints import BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_BUSQUEDA


def grandesbeneficiarios_busqueda(
    ctx: typer.Context,
    vpd: str = options.vpd,
    num_pages: int = options.num_pages,
    from_page: int = options.from_page,
    pageSize: int = options.pageSize,
    order: Order = options.order,
    direccion: Direccion = options.direccion,
    anios: List[int] = options.anios,
    anio: str = None,  # Alias for backward compatibility
    nifCif: str = options.nifCif,
    beneficiario: int = options.beneficiario,
) -> None:
    """
    Fetches data from https://www.infosubvenciones.es/bdnstrans/api/grandesbeneficiarios/busqueda
    """
    # Use anio if provided, otherwise use anios
    years_param = anio if anio is not None else anios

    params = {
        "vpd": vpd,
        "pageSize": pageSize,
        "order": order,
        "direccion": direccion,
        "anios": years_param,
        "nifCif": nifCif,
        "beneficiario": beneficiario,
    }
    asyncio.run(
        fetch_and_write_paginated(
            url=format_url(BDNS_API_ENDPOINT_GRANDES_BENEFICIARIOS_BUSQUEDA, params),
            output_file=ctx.obj["output_file"],
            from_page=from_page,
            num_pages=num_pages,
            max_concurrent_requests=ctx.obj["max_concurrent_requests"],
        )
    )
