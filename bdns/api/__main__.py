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

"""
@file __main__.py
@brief Main entry point for the BDNS API command line interface.
@details
This script provides a command line interface to interact with the BDNS API.
It allows users to fetch data from the API and save it to a file or print it to stdout.
@author: José María Cruz Lorite <josemariacruzlorite@gmail.com>
"""

from pathlib import Path

import typer

from bdns.api.commands import (
    concesiones_busqueda,
    ayudas_estado_busqueda,
    grandesbeneficiarios_anios,
    grandesbeneficiarios_busqueda,
    beneficiarios,
    finalidades,
    regiones,
    terceros,
    minimis_busqueda,
    concesiones_busqueda,
    convocatorias,
    convocatorias_busqueda,
    convocatorias_ultimas,
    convocatorias_documentos,
    convocatorias_pdf,
    partidos_politicos_busqueda
)
from bdns.api.commands import options


app = typer.Typer()
app.command(name="concesiones-busqueda")(concesiones_busqueda)
app.command(name="ayudas-estado-busqueda")(ayudas_estado_busqueda)
app.command(name="grandesbeneficiarios-anios")(grandesbeneficiarios_anios)
app.command(name="grandesbeneficiarios-busqueda")(grandesbeneficiarios_busqueda)
app.command(name="minimis-busqueda")(minimis_busqueda)
app.command(name="convocatorias")(convocatorias)
app.command(name="convocatorias-busqueda")(convocatorias_busqueda)
app.command(name="convocatorias-ultimas")(convocatorias_ultimas)
app.command(name="convocatorias-documentos")(convocatorias_documentos)
app.command(name="convocatorias-pdf")(convocatorias_pdf)
app.command(name="partidos-politicos-busqueda")(partidos_politicos_busqueda)
app.command(name="beneficiarios")(beneficiarios)
app.command(name="finalidades")(finalidades)
app.command(name="regiones")(regiones)
app.command(name="terceros")(terceros)



@app.callback()
def common_callback(
    ctx: typer.Context,
    output_file: Path = options.output_file,
    rate_limit: float = options.rate_limit
):
    """
    Common callback for all commands.
    This function sets up the context for all commands and handles the output file option.
    """
    ctx.obj = {
        "output_file": output_file,
        "rate_limit": rate_limit
    }

if __name__ == "__main__":
    app()
