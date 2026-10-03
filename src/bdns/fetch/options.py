# SPDX-License-Identifier: GPL-3.0-or-later

"""Command-line flags and help texts for the client's parameters.

This is the CLI's catalog, and only that. Types, defaults and which
parameters are required come from the client method signatures, so the
library and the CLI cannot disagree about them. A parameter appears here
once, however many endpoints take it.

Naming rule: flags of the tool itself are kebab-case (`--max-retries`);
flags that map to an API query parameter keep the API's spelling
(`--fechaDesde`), so the official documentation reads unchanged.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import click
import dateparser

__all__ = ["CLI_DEFAULTS", "PARAMETERS", "DateParamType", "ParameterSpec"]


class DateParamType(click.ParamType):
    """A date given as ISO (`2024-01-31`) or in natural language (`two weeks ago`).

    ISO is tried first, so it is never ambiguous. Anything else goes to
    `dateparser` with day-first ordering, the convention in Spain:
    `01/02/2024` is the 1st of February.
    """

    name = "date"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> date:
        """Parse `value` into a `date`, failing with a usage error."""
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
        parsed = dateparser.parse(value, settings={"DATE_ORDER": "DMY"})
        if parsed is None:
            self.fail(f"Could not parse date: {value}", param, ctx)
        return parsed.date()


DATE = DateParamType()
_DATE_HELP = " ISO (YYYY-MM-DD) or natural language, e.g. 'two weeks ago'."


@dataclass(frozen=True)
class ParameterSpec:
    """How one client parameter is exposed on the command line.

    Attributes:
        decls: Flag names, long first.
        help: Help text.
        extra: Further keyword arguments for `typer.Option`.
    """

    decls: tuple[str, ...]
    help: str
    extra: dict[str, Any] = field(default_factory=dict)


def _spec(*decls: str, help: str, **extra: Any) -> ParameterSpec:
    return ParameterSpec(decls, help, extra)


def _date_spec(*decls: str, help: str) -> ParameterSpec:
    return _spec(*decls, help=help + _DATE_HELP, click_type=DATE, metavar="DATE")


#: CLI defaults that differ from the library's. Fetching every page is the
#: right default for a program; typed at a prompt against an endpoint with
#: millions of rows, it is not. The client warns when it stops early.
CLI_DEFAULTS: dict[str, Any] = {"num_pages": 1}

PARAMETERS: dict[str, ParameterSpec] = {
    # Pagination
    "num_pages": _spec(
        "--num-pages",
        "-np",
        help="Number of pages to fetch. 0 fetches all pages.",
        min=0,
    ),
    "from_page": _spec("--from-page", "-fp", help="First page to fetch (0-based).", min=0),
    "pageSize": _spec(
        "--pageSize",
        "-ps",
        help="Results per page. The API allows at most 10000.",
        min=1,
        max=10000,
    ),
    "order": _spec("--order", "-ord", help="Field to sort the results by."),
    "direccion": _spec("--direccion", "-d", help="Sort direction."),
    # Portal and free-text search
    "vpd": _spec("--vpd", "-vpd", help="Portal identifier (VPD). 'GE' is the national portal."),
    "descripcion": _spec(
        "--descripcion", "-desc", help="Title or part of it, in Spanish or a co-official language."
    ),
    "descripcionTipoBusqueda": _spec(
        "--descripcionTipoBusqueda",
        "-dtb",
        help="How --descripcion matches: 0 exact phrase, 1 all words, 2 any word.",
    ),
    "busqueda": _spec(
        "--busqueda", "-bus", help="Filter on the description, at least 3 characters."
    ),
    # Dates
    "fechaDesde": _date_spec("--fechaDesde", "-fd", help="Start of the search period."),
    "fechaHasta": _date_spec("--fechaHasta", "-fh", help="End of the search period."),
    "fechaRegInicio": _date_spec(
        "--fechaRegInicio",
        "-fri",
        help="Start of the registration-date period, independent of the award date.",
    ),
    "fechaRegFin": _date_spec(
        "--fechaRegFin",
        "-frf",
        help="End of the registration-date period, independent of the award date.",
    ),
    # Identifiers
    "id": _spec("--id", "-id", help="Identifier of the call for applications."),
    "idDocumento": _spec("--idDocumento", "-iddoc", help="Identifier of the document."),
    "idPES": _spec("--idPES", "-idpes", help="Identifier of the strategic plan."),
    "idPersona": _spec("--idPersona", "-idp", help="Identifier of the person."),
    "numConv": _spec("--numConv", "-nc", help="BDNS number of the call for applications."),
    "numeroConvocatoria": _spec(
        "--numeroConvocatoria", "-nconv", help="BDNS number of the call to search for."
    ),
    "codConcesion": _spec("--codConcesion", "-cc", help="Code of the award to search for."),
    "codigo": _spec("--codigo", "-cod", help="Code of the administrative body."),
    "codigoAdmin": _spec("--codigoAdmin", "-ca", help="Admin code of the administrative body."),
    "nifCif": _spec("--nifCif", "-n", help="NIF/CIF of the beneficiary."),
    "beneficiario": _spec("--beneficiario", "-b", help="Identifier of the beneficiary."),
    "ayudaEstado": _spec(
        "--ayudaEstado", "-ae", help="State aid reference (SA number). State aid only."
    ),
    # Administrative scope
    "idAdmon": _spec(
        "--idAdmon",
        "-ida",
        help="Type of administrative body: C State, A Autonomous Community, L Local, O Other.",
    ),
    "tipoAdministracion": _spec(
        "--tipoAdministracion",
        "-ta",
        help="Type of administrative body: C State, A Autonomous Community, L Local, O Other.",
    ),
    "ambito": _spec(
        "--ambito",
        "-amb",
        help="Area: C awards, A state aid, M de minimis, S sanctions, P political parties, G large beneficiaries.",
    ),
    # Repeatable filters
    "organos": _spec("--organos", "-org", help="Administrative body identifier. Repeatable."),
    "regiones": _spec("--regiones", "-r", help="Impact region identifier. Repeatable."),
    "tiposBeneficiario": _spec("--tiposBeneficiario", "-tb", help="Beneficiary type. Repeatable."),
    "instrumentos": _spec("--instrumentos", "-ins", help="Aid instrument identifier. Repeatable."),
    "actividad": _spec("--actividad", "-act", help="Economic activity identifier. Repeatable."),
    "objetivos": _spec("--objetivos", "-obj", help="Objective identifier. Repeatable."),
    "producto": _spec("--producto", "-p", help="Product identifier. Repeatable."),
    "reglamento": _spec("--reglamento", "-reg", help="Regulation identifier. Repeatable."),
    "anios": _spec("--anios", "-an", help="Year as a large beneficiary. Repeatable."),
    "finalidad": _spec("--finalidad", "-f", help="Spending-policy purpose identifier."),
    "mrr": _spec("--mrr", "-mrr", help="Restrict to the Recovery and Resilience Facility (MRR)."),
}
