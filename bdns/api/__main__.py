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

from bdns.api.commands import *
from bdns.api.commands import options


app = typer.Typer()
app.command(name="actividades")(actividades)
app.command(name="ayudasestado-busqueda")(ayudasestado_busqueda)
app.command(name="beneficiarios")(beneficiarios)
app.command(name="concesiones-busqueda")(concesiones_busqueda)
app.command(name="convocatorias")(convocatorias)
app.command(name="convocatorias-busqueda")(convocatorias_busqueda)
app.command(name="convocatorias-documentos")(convocatorias_documentos)
app.command(name="convocatorias-pdf")(convocatorias_pdf)
app.command(name="convocatorias-ultimas")(convocatorias_ultimas)
app.command(name="finalidades")(finalidades)
app.command(name="grandesbeneficiarios-anios")(grandesbeneficiarios_anios)
app.command(name="grandesbeneficiarios-busqueda")(grandesbeneficiarios_busqueda)
app.command(name="instrumentos")(instrumentos)
app.command(name="minimis-busqueda")(minimis_busqueda)
app.command(name="objetivos")(objetivos)
app.command(name="organos")(organos)
app.command(name="organos-agrupacion")(organos_agrupacion)
app.command(name="organos-codigo")(organos_codigo)
app.command(name="organos-codigoadmin")(organos_codigoadmin)
app.command(name="partidospoliticos-busqueda")(partidospoliticos_busqueda)
app.command(name="planesestrategicos-busqueda")(planesestrategicos_busqueda)
app.command(name="planesestrategicos-vigencia")(planesestrategicos_vigencia)
app.command(name="reglamentos")(reglamentos)
app.command(name="regiones")(regiones)
app.command(name="sanciones-busqueda")(sanciones_busqueda)
app.command(name="sectores")(sectores)
app.command(name="terceros")(terceros)


@app.callback()
def common_callback(
    ctx: typer.Context,
    output_file: Path = options.output_file,
    max_concurrent_requests: int = options.max_concurrent_requests,
):
    """
    Common callback for all commands.
    This function sets up the context for all commands and handles the output file option.
    """
    ctx.obj = {
        "output_file": output_file,
        "max_concurrent_requests": max_concurrent_requests
    }

if __name__ == "__main__":
    app()
