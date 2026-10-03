# SPDX-License-Identifier: GPL-3.0-or-later

"""Command-line flags and help texts for the client's parameters.

This is the CLI's catalog, and only that. Types, defaults and which
parameters are required come from the client method signatures, so the
library and the CLI cannot disagree about them. A parameter appears here
once, however many endpoints take it.

Naming rule: flags of the tool itself are kebab-case (`--max-retries`);
flags that map to an API query parameter keep the API's spelling
(`--fechaDesde`), so the official documentation reads unchanged. Only the
two most used global flags have a short form (`-o`, `-v`).
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import click

__all__ = ["CLI_DEFAULTS", "DATE", "PARAMETERS", "DateParamType", "ParameterSpec"]


class DateParamType(click.ParamType):
    """A date as ISO (`2024-01-31`) or day first (`31/01/2024`, `31-01-2024`).

    Day first is the convention in Spain, so `01/02/2024` is the 1st of
    February. Nothing else is guessed at: an ambiguous date is worse than
    an error.
    """

    name = "date"
    _DAY_FIRST = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> date:
        """Parse `value` into a `date`, failing with a usage error."""
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
        match = self._DAY_FIRST.match(value)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        self.fail(f"{value!r} is not a date. Use YYYY-MM-DD or DD/MM/YYYY.", param, ctx)


DATE = DateParamType()
"""The parser every date option uses."""
_DATE_HELP = " YYYY-MM-DD or DD/MM/YYYY."


@dataclass(frozen=True)
class ParameterSpec:
    """How one client parameter is exposed on the command line.

    Attributes:
        flag: The option name.
        help: Help text.
        extra: Further keyword arguments for `typer.Option`.
    """

    flag: str
    help: str
    extra: dict[str, Any] = field(default_factory=dict)


def _spec(flag: str, help: str, **extra: Any) -> ParameterSpec:
    """Build a spec; shorthand that keeps the catalog readable."""
    return ParameterSpec(flag, help, extra)


def _date_spec(flag: str, help: str) -> ParameterSpec:
    """Build the spec of a date parameter, parsed by [`DATE`][bdns.fetch.options.DATE]."""
    return _spec(flag, help + _DATE_HELP, click_type=DATE, metavar="DATE")


CLI_DEFAULTS: dict[str, Any] = {"num_pages": 1}
"""CLI defaults that differ from the library's. Fetching every page is the right default for a program; typed at a prompt against an endpoint with millions of rows, it is not. The client warns when it stops early."""

PARAMETERS: dict[str, ParameterSpec] = {
    # Pagination
    "num_pages": _spec("--num-pages", "Number of pages to fetch. 0 fetches all pages.", min=0),
    "from_page": _spec("--from-page", "First page to fetch (0-based).", min=0),
    "pageSize": _spec(
        "--pageSize", "Results per page. The API allows at most 10000.", min=1, max=10000
    ),
    "order": _spec("--order", "Field to sort the results by."),
    "direccion": _spec("--direccion", "Sort direction."),
    # Portal and free-text search
    "vpd": _spec("--vpd", "Portal identifier (VPD). 'GE' is the national portal."),
    "descripcion": _spec(
        "--descripcion", "Title or part of it, in Spanish or a co-official language."
    ),
    "descripcionTipoBusqueda": _spec(
        "--descripcionTipoBusqueda",
        "How --descripcion matches: 0 exact phrase, 1 all words, 2 any word.",
    ),
    "busqueda": _spec("--busqueda", "Filter on the description, at least 3 characters."),
    # Dates
    "fechaDesde": _date_spec("--fechaDesde", "Start of the search period, inclusive."),
    "fechaHasta": _date_spec("--fechaHasta", "End of the search period, inclusive."),
    "fechaRegInicio": _date_spec(
        "--fechaRegInicio", "Start of the registration-date period, inclusive."
    ),
    "fechaRegFin": _date_spec(
        "--fechaRegFin",
        "End of the registration-date period, EXCLUSIVE: to include a day, pass the next one.",
    ),
    # Identifiers
    "id": _spec("--id", "Identifier of the call for applications."),
    "idDocumento": _spec("--idDocumento", "Identifier of the document."),
    "idPES": _spec("--idPES", "Identifier of the strategic plan."),
    "idPersona": _spec("--idPersona", "Identifier of the person."),
    "numConv": _spec("--numConv", "BDNS number of the call for applications."),
    "numeroConvocatoria": _spec("--numeroConvocatoria", "BDNS number of the call to search for."),
    "codConcesion": _spec("--codConcesion", "Code of the award to search for."),
    "codigo": _spec("--codigo", "Code of the administrative body."),
    "codigoAdmin": _spec("--codigoAdmin", "Admin code of the administrative body."),
    "nifCif": _spec("--nifCif", "NIF/CIF of the beneficiary."),
    "beneficiario": _spec("--beneficiario", "Identifier of the beneficiary."),
    "ayudaEstado": _spec("--ayudaEstado", "State aid reference (SA number). State aid only."),
    # Administrative scope
    "idAdmon": _spec(
        "--idAdmon",
        "Type of administrative body: C State, A Autonomous Community, L Local, O Other.",
    ),
    "tipoAdministracion": _spec(
        "--tipoAdministracion",
        "Type of administrative body: C State, A Autonomous Community, L Local, O Other.",
    ),
    "ambito": _spec(
        "--ambito",
        "Area: C awards, A state aid, M de minimis, S sanctions, P political parties, G large beneficiaries.",
    ),
    # Repeatable filters
    "organos": _spec("--organos", "Administrative body identifier. Repeatable."),
    "regiones": _spec("--regiones", "Impact region identifier. Repeatable."),
    "tiposBeneficiario": _spec("--tiposBeneficiario", "Beneficiary type. Repeatable."),
    "instrumentos": _spec("--instrumentos", "Aid instrument identifier. Repeatable."),
    "actividad": _spec("--actividad", "Economic activity identifier. Repeatable."),
    "objetivos": _spec("--objetivos", "Objective identifier. Repeatable."),
    "producto": _spec("--producto", "Product identifier. Repeatable."),
    "reglamento": _spec("--reglamento", "Regulation identifier. Repeatable."),
    "anios": _spec("--anios", "Year as a large beneficiary. Repeatable."),
    "finalidad": _spec("--finalidad", "Spending-policy purpose identifier."),
    "mrr": _spec("--mrr", "Restrict to the Recovery and Resilience Facility (MRR)."),
}
