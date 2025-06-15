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

from bdns.api.utils import format_url
from bdns.api.types import Order, Direccion
from bdns.api.fetch_write import fetch_and_write_paginated
from bdns.api.commands import options
from bdns.api.endpoints import BDNS_API_ENDPOINT_CONVOCATORIAS_ULTIMAS


def convocatorias_ultimas(
    ctx: typer.Context,
    num_pages: int = options.num_pages,
    from_page: int = options.from_page,
    pageSize: int = options.pageSize,
    order: Order = options.order,
    direccion: Direccion = options.direccion,
    vpd: str = options.vpd
) -> None:
    """
    Fetches convocatorias data from the BDNS API based on search parameters.
    """
    params = {
        "pageSize": pageSize,
        "order": order,
        "direccion": direccion,
        "vpd": vpd
    }
    asyncio.run(
        fetch_and_write_paginated(
            url=format_url(
                BDNS_API_ENDPOINT_CONVOCATORIAS_ULTIMAS,
                params
            ),
            output_file=ctx.obj["output_file"],
            from_page=from_page,
            num_pages=num_pages,
            rate_limit=ctx.obj["rate_limit"]
        )
    )
