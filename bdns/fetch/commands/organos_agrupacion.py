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

import typer

from bdns.fetch.utils import format_url
from bdns.fetch.types import TipoAdministracion
from bdns.fetch.fetch_write import fetch_and_write
from bdns.fetch.commands import options
from bdns.fetch.endpoints import BDNS_API_ENDPOINT_ORGANOS_AGRUPACION


def organos_agrupacion(
    ctx: typer.Context,
    vpd: str = options.vpd,
    idAdmon: TipoAdministracion = options.idAdmon_required,
) -> None:
    """
    Fetches data from https://www.infosubvenciones.es/bdnstrans/api/organos/agrupacion
    """
    params = {
        "vpd": vpd,
        "idAdmon": idAdmon.value,
    }
    fetch_and_write(
        url=format_url(BDNS_API_ENDPOINT_ORGANOS_AGRUPACION, params),
        output_file=ctx.obj["output_file"],
    )
