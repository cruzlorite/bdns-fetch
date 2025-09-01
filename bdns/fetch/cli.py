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
BDNS Fetch CLI: Command-line interface for BDNS data fetching.
"""

import typer
import functools
import logging
import click
from pathlib import Path

from bdns.fetch.utils import extract_option_values, write_to_file
from bdns.fetch.client import BDNSClient
from bdns.fetch import options

app = typer.Typer()


@app.callback()
def main(
    ctx: typer.Context,
    output_file: Path = options.output_file,
    verbose_flag: bool = options.verbose_flag,
):
    """
    BDNS Fetch - Base de Datos Nacional de Subvenciones (BDNS) CLI

    Fetch data from the Base de Datos Nacional de Subvenciones (BDNS).

    \b
    Examples:
      bdns-fetch --output-file organos.jsonl organos
      bdns-fetch --output-file convocatorias.jsonl convocatorias-busqueda --fechaDesde "2024-01-01"
      bdns-fetch ayudasestado-busqueda --descripcion "innovation"

    \b
    Official API: https://www.infosubvenciones.es/bdnstrans/api
    """
    ctx.obj = {
        "output_file": output_file,
        "verbose": verbose_flag,
    }

    # Configure logging based on verbose flag
    if verbose_flag:
        # Set detailed logging for HTTP requests/responses
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("bdns.fetch").setLevel(logging.DEBUG)
        logging.getLogger("aiohttp.client").setLevel(logging.DEBUG)
        # Enable urllib3 logging for even more HTTP details
        logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
    else:
        # Keep default INFO level for normal operation
        logging.getLogger().setLevel(logging.INFO)


def cli_wrapper(client_method):
    """
    Wrapper that executes a client method and writes the result to file.
    All methods are now generators that stream data as it comes.

    Args:
        client_method: The client method to wrap

    Returns:
        A function that can be used as a Typer command
    """

    @functools.wraps(client_method)
    def wrapper(*args, **kwargs):
        # Access context using Click's get_current_context (no need for ctx parameter!)
        ctx = click.get_current_context()
        output_file = ctx.obj["output_file"]
        data_generator = client_method(*args, **kwargs)
        write_to_file(data_generator, output_file)
        return None  # CLI doesn't need to return data

    return wrapper


# Create a single client instance for all CLI commands
client = BDNSClient()

# Register all commands
app.command("actividades")(cli_wrapper(client.fetch_actividades))
app.command("sectores")(cli_wrapper(client.fetch_sectores))
app.command("regiones")(cli_wrapper(client.fetch_regiones))
app.command("finalidades")(cli_wrapper(client.fetch_finalidades))
app.command("beneficiarios")(cli_wrapper(client.fetch_beneficiarios))
app.command("instrumentos")(cli_wrapper(client.fetch_instrumentos))
app.command("reglamentos")(cli_wrapper(client.fetch_reglamentos))
app.command("objetivos")(cli_wrapper(client.fetch_objetivos))
app.command("grandesbeneficiarios-anios")(
    cli_wrapper(client.fetch_grandesbeneficiarios_anios)
)
app.command("planesestrategicos")(cli_wrapper(client.fetch_planesestrategicos))
app.command("organos")(cli_wrapper(client.fetch_organos))
app.command("organos-agrupacion")(cli_wrapper(client.fetch_organos_agrupacion))
app.command("organos-codigo")(cli_wrapper(client.fetch_organos_codigo))
app.command("organos-codigoadmin")(cli_wrapper(client.fetch_organos_codigoadmin))
app.command("convocatorias")(cli_wrapper(client.fetch_convocatorias))
app.command("concesiones-busqueda")(cli_wrapper(client.fetch_concesiones_busqueda))
app.command("ayudasestado-busqueda")(cli_wrapper(client.fetch_ayudasestado_busqueda))
app.command("terceros")(cli_wrapper(client.fetch_terceros))
app.command("convocatorias-busqueda")(cli_wrapper(client.fetch_convocatorias_busqueda))
app.command("convocatorias-ultimas")(cli_wrapper(client.fetch_convocatorias_ultimas))
app.command("convocatorias-documentos")(
    cli_wrapper(client.fetch_convocatorias_documentos)
)
app.command("convocatorias-pdf")(cli_wrapper(client.fetch_convocatorias_pdf))
app.command("grandesbeneficiarios-busqueda")(
    cli_wrapper(client.fetch_grandesbeneficiarios_busqueda)
)
app.command("minimis-busqueda")(cli_wrapper(client.fetch_minimis_busqueda))
app.command("partidospoliticos-busqueda")(
    cli_wrapper(client.fetch_partidospoliticos_busqueda)
)
app.command("planesestrategicos-busqueda")(
    cli_wrapper(client.fetch_planesestrategicos_busqueda)
)
app.command("planesestrategicos-documentos")(
    cli_wrapper(client.fetch_planesestrategicos_documentos)
)
app.command("planesestrategicos-vigencia")(
    cli_wrapper(client.fetch_planesestrategicos_vigencia)
)
app.command("sanciones-busqueda")(cli_wrapper(client.fetch_sanciones_busqueda))


if __name__ == "__main__":
    app()
