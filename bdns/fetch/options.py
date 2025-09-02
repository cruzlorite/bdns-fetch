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

from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

import typer

from bdns.fetch.types import (
    Order,
    Ambito,
    Direccion,
    TipoAdministracion,
    DescripcionTipoBusqueda,
)


def parse_date(value: str) -> date:
    try:
        if value:
            return datetime.strptime(value, "%Y-%m-%d").date()
        else:
            return None
    except ValueError:
        raise typer.BadParameter("Date must be in YYYY-MM-DD format")


output_file: Optional[Path] = typer.Option(
    "-",
    "--output-file",
    "-o",
    help="File to save the output. '-' means standard output.",
    show_default=True,
)
max_concurrent_requests: int = typer.Option(
    5,
    "--max-concurrent-requests",
    "-mcr",
    min=1,
    help="Maximum number of concurrent requests to the API.",
    show_default=True,
)
max_retries: int = typer.Option(
    3,
    "--max-retries",
    "-mr",
    min=1,
    help="Maximum number of retries for failed requests.",
    show_default=True,
)
wait_time: int = typer.Option(
    2,
    "--wait-time",
    "-wt",
    min=1,
    help="Time to wait between retries in seconds.",
    show_default=True,
)
version: Optional[bool] = typer.Option(
    None,
    "--version",
    help="Show the version and exit.",
    is_flag=True,
)
num_pages: Optional[int] = typer.Option(
    1,
    "--num-pages",
    "-np",
    min=0,
    help="For paginated endpoints, the number of pages to fetch. If 0, fetches all pages.",
    show_default=True,
)
from_page: Optional[int] = typer.Option(
    0,
    "--from-page",
    "-fp",
    min=0,
    help="Page number to start fetching from. If 0, starts from the first page.",
    show_default=True,
)
pageSize: Optional[int] = typer.Option(
    10000,
    "--pageSize",
    "-ps",
    min=1,
    max=10000,
    help="Number of results per page. The maximum allowed is 10000.",
    show_default=True,
)
order: Optional[Order] = typer.Option(
    None,
    "--order",
    "-ord",
    help="Order of the results. Can be 'nivel1', 'nivel2', 'nivel3', 'codConcesion', 'numeroConvocatoria', 'convocatoria', 'descripcionCooficial', 'instrumento', 'urlBR', 'fechaConcesion', 'beneficiario', 'importe', 'ayudaEquivalente' or 'tieneProyecto'.",
    show_default=True,
)
direccion: Optional[Direccion] = typer.Option(
    None,
    "--direccion",
    "-d",
    help="Direction of the search. Can be 'asc' or 'desc'.",
    show_default=True,
)
vpd: Optional[str] = typer.Option(
    "GE",
    "--vpd",
    "-vpd",
    help="VPD portal ID.",
    show_default=True,
)
vpd_required: str = typer.Option(
    ...,
    "--vpd",
    "-vpd",
    help="VPD portal ID.",
)
descripcion: Optional[str] = typer.Option(
    None,
    "--descripcion",
    "-desc",
    help="Title or part of it, in Spanish or co-official language.",
    show_default=True,
)
descripcionTipoBusqueda: Optional[DescripcionTipoBusqueda] = typer.Option(
    None,
    "--descripcionTipoBusqueda",
    "-dtb",
    help="Type of search to perform on the title. 1 - all words, 2 - any of the words, 0 - exact phrase. Any other value should not be taken into account.",
    show_default=True,
)
numeroConvocatoria: Optional[str] = typer.Option(
    None,
    "--numeroConvocatoria",
    "-nconv",
    help="BDNS number of the call to search for.",
    show_default=True,
)
mrr: Optional[bool] = typer.Option(
    False,
    "--mrr",
    "-mrr",
    help="Indicates if the search is for the Recovery and Resilience Mechanism (MRR).",
    show_default=True,
)
fechaDesde: Optional[date] = typer.Option(
    None,
    "--fechaDesde",
    "-fd",
    # callback=parse_date,
    metavar="YYYY-MM-DD",
    help="Start date of the period indicated for the search.",
    show_default=True,
)
fechaHasta: Optional[date] = typer.Option(
    None,
    "--fechaHasta",
    "-fh",
    # callback=parse_date,
    metavar="YYYY-MM-DD",
    help="End date of the period indicated for the search.",
    show_default=True,
)
tipoAdministracion: Optional[TipoAdministracion] = typer.Option(
    None,
    "--tipoAdministracion",
    "-ta",
    help="Type of administrative body being searched for 'C' for State Administration, 'A' for Autonomous Community, 'L' for Local Entity and 'O' for other Bodies.",
    show_default=True,
)
organos: Optional[List[int]] = typer.Option(
    None,
    "--organos",
    "-org",
    help="List of identifiers of the administrative bodies.",
    show_default=True,
)
regiones: Optional[List[int]] = typer.Option(
    None,
    "--regiones",
    "-r",
    help="List of identifiers of the selected impact regions, separated by commas.",
    show_default=True,
)
tiposBeneficiario: Optional[List[int]] = typer.Option(
    None,
    "--tiposBeneficiario",
    "-tb",
    help="List of identifiers of the selected beneficiary types, separated by commas.",
    show_default=True,
)
tiposBeneficiario_str: Optional[List[str]] = typer.Option(
    None,
    "--tiposBeneficiario",
    "-tb",
    help="List of beneficiary type codes, separated by commas.",
    show_default=True,
)
instrumentos: Optional[List[int]] = typer.Option(
    None,
    "--instrumentos",
    "-ins",
    help="List of identifiers of the selected aid instruments, separated by commas.",
    show_default=True,
)
finalidad: Optional[int] = typer.Option(
    None,
    "--finalidad",
    "-f",
    help="Identifier of the purpose of the spending policy.",
    show_default=True,
)
ayudaEstado: Optional[str] = typer.Option(
    None,
    "--ayudaEstado",
    "-ae",
    help="SA Number - State aid reference (only for State aid).",
    show_default=True,
)
codConcesion: Optional[str] = typer.Option(
    None,
    "--codConcesion",
    "-cc",
    help="Code of the concession to search for.",
    show_default=True,
)
idDocumento: Optional[int] = typer.Option(
    None,
    "--idDocumento",
    "-iddoc",
    help="Identifier of the document to search for.",
    show_default=True,
)
idDocumento_required: int = typer.Option(
    ...,
    "--idDocumento",
    "-iddoc",
    help="Identifier of the document.",
)
nifCif: Optional[str] = typer.Option(
    None,
    "--nifCif",
    "-n",
    help="NIF/CIF of the beneficiary.",
    show_default=True,
)
beneficiario: Optional[str] = typer.Option(
    None,
    "--beneficiario",
    "-b",
    help="ID of the beneficiary.",
    show_default=True,
)
actividad: Optional[List[int]] = typer.Option(
    None,
    "--actividad",
    "-act",
    help="List of identifiers of the selected activities, separated by commas.",
    show_default=True,
)
id: Optional[int] = typer.Option(
    None,
    "--id",
    "-id",
    help="Identifier of the document to search for.",
    show_default=True,
)
id_required: int = typer.Option(
    ...,
    "--id",
    "-id",
    help="Identifier of the document.",
)
objetivos: Optional[List[int]] = typer.Option(
    None,
    "--objetivos",
    "-obj",
    help="List of identifiers of the objectives of the concession, separated by commas.",
    show_default=True,
)
producto: Optional[List[int]] = typer.Option(
    None,
    "--producto",
    "-p",
    help="List of identifiers of the selected products, separated by commas.",
    show_default=True,
)
codigoAdmin: Optional[str] = typer.Option(
    None,
    "--codigoAdmin",
    "-ca",
    help="Admin code of the body.",
    show_default=True,
)
codigoAdmin_required: str = typer.Option(
    ...,
    "--codigoAdmin",
    "-ca",
    help="Admin code of the organ.",
)
codigo: Optional[str] = typer.Option(
    None,
    "--codigo",
    "-c",
    help="Code of the administrative body.",
    show_default=True,
)
idAdmon: Optional[TipoAdministracion] = typer.Option(
    None,
    "--idAdmon",
    "-ida",
    help="Identifier of the administrative body.",
    show_default=True,
)
idAdmon_required: TipoAdministracion = typer.Option(
    ...,
    "--idAdmon",
    "-ida",
    help="Type of administrative body: C (State), A (Autonomous Community), L (Local Entity), O (Other)",
)
ambito: Optional[Ambito] = typer.Option(
    None,
    "--ambito",
    "-amb",
    help="Indicator of the area where the search will be conducted (Concessions (C), State Aid (A), de Minimis (M), Sanctions (S), Political Parties (P), Large Beneficiaries (G)).",
    show_default=True,
)
busqueda: Optional[str] = typer.Option(
    None,
    "--busqueda",
    "-bus",
    help="Filter for the description field, must have a minimum length of 3.",
    show_default=True,
)
idPersona: Optional[int] = typer.Option(
    None,
    "--idPersona",
    "-idp",
    help="Identifier of the person.",
    show_default=True,
)
reglamento: Optional[List[int]] = typer.Option(
    None,
    "--reglamento",
    "-reg",
    help="List of identifiers of the selected regulations, separated by commas.",
    show_default=True,
)
anios: Optional[List[int]] = typer.Option(
    None,
    "--anios",
    "-an",
    help="List of years in which they have been a large beneficiary.",
    show_default=True,
)
vigenciaDesde: Optional[date] = typer.Option(
    None,
    "--vigenciaDesde",
    "-vd",
    # callback=parse_date,
    metavar="YYYY-MM-DD",
    help="Start date of the validity of the strategic plan.",
    show_default=True,
)
vigenciaHasta: Optional[date] = typer.Option(
    None,
    "--vigenciaHasta",
    "-vh",
    # callback=parse_date,
    metavar="YYYY-MM-DD",
    help="End date of the validity of the strategic plan.",
    show_default=True,
)
numConv: Optional[str] = typer.Option(
    None,
    "--numConv",
    "-nc",
    help="Number of the call.",
    show_default=True,
)
numConv_required: str = typer.Option(
    ...,
    "--numConv",
    "-nc",
    help="Number of the call.",
)
idPES_required: int = typer.Option(
    ...,
    "--idPES",
    "-idpes",
    help="Identifier of the strategic plan.",
)
idPES: Optional[int] = typer.Option(
    None,
    "--idPES",
    "-idpes",
    help="Identifier of the strategic plan.",
    show_default=True,
)
codigo: str = typer.Option(
    ...,
    "--codigo",
    "-cod",
    help="Organ code.",
)

verbose_flag: bool = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Enable verbose logging to show detailed HTTP requests and responses.",
    show_default=True,
)
