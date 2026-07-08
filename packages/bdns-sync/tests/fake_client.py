"""Duck-typed stand-in for `bdns.fetch.BDNSClient`, used by the timeline
scenario tests instead of hitting the network.

`bdns.sync.syncers` never imports or type-checks against the real
`BDNSClient` class. Every `sync_*` function just calls `fetch_*` methods on
whatever `client` object it's given, so a plain Python object exposing the
same method names and keyword arguments is a complete substitute. No
mocking library is required.

Backing data is loaded from tests/fixtures/*.json: real records captured
live from the BDNS API, with names, NIF/CIF, and other identifying values
replaced by fake ones. Fields are otherwise untouched, so the tests
exercise the real payload shape.

Each fixture list or dict is copied onto `self` at construction time and is
meant to be mutated directly between simulated "days" in a test, for
example `client.concesiones_busqueda.append(...)`, `del client.sectores[0]`,
or editing a field on one row, to script insert/update/touch/delete
scenarios.
"""

import json
from collections.abc import Iterable
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_CACHE: dict[str, Any] = {}


def load_fixture(name: str):
    """Fixtures are read once per process and deep-copied per call so tests
    mutating their client's copy never leak state into other tests.
    """
    if name not in _CACHE:
        with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
            _CACHE[name] = json.load(f)
    return deepcopy(_CACHE[name])


# Maps each entity to the payload field that holds its own registration
# date, confirmed live against the real API (see bdns/sync/syncers.py).
# Fixture records store an offset (`reg_days_ago`) instead of this field's
# value, so it has to be patched in dynamically. Otherwise it would be
# whatever absolute date was true when the fixture was captured, which
# would break window-scoped deletion checks as soon as time passes.
REG_DATE_FIELDS = {
    "concesiones_busqueda": "fechaAlta",
    "ayudasestado_busqueda": "fechaAlta",
    "minimis_busqueda": "fechaRegistro",
    "convocatorias_busqueda": "fechaRecepcion",
}


def _patch_reg_dates(records: list[dict], field: str) -> None:
    for rec in records:
        rec["payload"][field] = reg_date(rec["reg_days_ago"]).isoformat()


def reg_date(days_ago: int) -> date:
    """Fixtures store ages in days-ago rather than absolute dates, so they
    never go stale. This is relative to yesterday, not today: every window,
    daily included, ends at `date.today() - 1` (see bdns.sync.generic.WINDOWS),
    since data for "today" isn't final until the run the following morning.
    So `days_ago=0` means "yesterday", which is always inside the daily
    window.
    """
    return date.today() - timedelta(days=1) - timedelta(days=days_ago)


class FakeBDNSClient:
    def __init__(self):
        # Simple full-replace catalogs.
        self.sectores = load_fixture("sectores")
        self.actividades = load_fixture("actividades")
        self.finalidades = load_fixture("finalidades")
        self.beneficiarios = load_fixture("beneficiarios")
        self.instrumentos = load_fixture("instrumentos")
        self.objetivos = load_fixture("objetivos")
        self.convocatorias_ultimas = load_fixture("convocatorias_ultimas")
        self.regiones = load_fixture("regiones")
        self.sanciones_busqueda = load_fixture("sanciones_busqueda")

        # Swept catalogs: sweep value -> rows. Only "C" is populated, since
        # that's the sample pulled from the real capture. Other admin types
        # and ambitos are legitimately empty for most real organs too, and
        # what's under test is the merge-without-cross-closing behavior, not
        # the exact row count per value.
        self.organos = {"C": load_fixture("organos"), "A": [], "L": [], "O": []}
        self.organos_agrupacion = {"C": load_fixture("organos_agrupacion"), "A": [], "L": [], "O": []}
        self.reglamentos = {"C": load_fixture("reglamentos"), "A": [], "M": [], "S": [], "P": [], "G": []}

        # Windowed search entities: [{"reg_days_ago": int, "payload": {...}}].
        # partidospoliticos_busqueda has no registration-date field in its
        # payload, confirmed live, so there's nothing to patch there.
        self.concesiones_busqueda = load_fixture("concesiones_busqueda")
        _patch_reg_dates(self.concesiones_busqueda, REG_DATE_FIELDS["concesiones_busqueda"])
        self.ayudasestado_busqueda = load_fixture("ayudasestado_busqueda")
        _patch_reg_dates(self.ayudasestado_busqueda, REG_DATE_FIELDS["ayudasestado_busqueda"])
        self.minimis_busqueda = load_fixture("minimis_busqueda")
        _patch_reg_dates(self.minimis_busqueda, REG_DATE_FIELDS["minimis_busqueda"])
        self.partidospoliticos_busqueda = load_fixture("partidospoliticos_busqueda")
        self.convocatorias_busqueda = load_fixture("convocatorias_busqueda")
        _patch_reg_dates(self.convocatorias_busqueda, REG_DATE_FIELDS["convocatorias_busqueda"])

        # numeroConvocatoria/idPES -> detail payload (or a non-dict, to
        # simulate the live "malformed record" case _skip_malformed guards
        # against). Keep each detail's fechaRecepcion in sync with its
        # discovery entry's freshly patched date, since they're the same
        # record.
        self.convocatorias_detail = load_fixture("convocatorias_detail")
        for rec in self.convocatorias_busqueda:
            detail = self.convocatorias_detail.get(rec["payload"]["numeroConvocatoria"])
            if isinstance(detail, dict):
                detail["fechaRecepcion"] = rec["payload"]["fechaRecepcion"]

        self.grandesbeneficiarios_anios = load_fixture("grandesbeneficiarios_anios")
        self.grandesbeneficiarios_busqueda = load_fixture("grandesbeneficiarios_busqueda")

        self.planesestrategicos_busqueda = load_fixture("planesestrategicos_busqueda")
        self.planesestrategicos_detail = load_fixture("planesestrategicos_detail")
        self.planesestrategicos_vigencia = load_fixture("planesestrategicos_vigencia")

        self.calls: list[tuple] = []  # (method_name, kwargs) audit log

    # Simple full-replace catalogs, no arguments.

    def fetch_sectores(self):
        yield from self.sectores

    def fetch_actividades(self):
        yield from self.actividades

    def fetch_finalidades(self):
        yield from self.finalidades

    def fetch_beneficiarios(self):
        yield from self.beneficiarios

    def fetch_instrumentos(self):
        yield from self.instrumentos

    def fetch_objetivos(self):
        yield from self.objetivos

    def fetch_convocatorias_ultimas(self):
        yield from self.convocatorias_ultimas

    def fetch_regiones(self):
        yield from self.regiones

    def fetch_sanciones_busqueda(self):
        yield from self.sanciones_busqueda

    # Swept catalogs.

    def fetch_organos(self, idAdmon):
        self.calls.append(("fetch_organos", {"idAdmon": idAdmon}))
        yield from self.organos.get(idAdmon, [])

    def fetch_organos_agrupacion(self, idAdmon):
        self.calls.append(("fetch_organos_agrupacion", {"idAdmon": idAdmon}))
        yield from self.organos_agrupacion.get(idAdmon, [])

    def fetch_reglamentos(self, ambito):
        self.calls.append(("fetch_reglamentos", {"ambito": ambito}))
        yield from self.reglamentos.get(ambito, [])

    # Windowed search entities (reg-date cascade).

    def _windowed(
        self, method: str, records: Iterable[dict], start: date, end: date, upper_inclusive: bool = False
    ):
        """Models the real API's date filtering, which differs by endpoint:

        - The four `fechaRegFin` search endpoints use a HALF-OPEN range: the
          upper bound is exclusive, so a record on day `end` is NOT returned
          (`upper_inclusive=False`). That's why those callers must pass
          `generic.to_api_upper_bound(chunk_end)`; if they forget, this drops
          the boundary day exactly like the live API does, so the regression
          tests catch it instead of silently passing.
        - convocatorias' `fechaHasta` is INCLUSIVE (`upper_inclusive=True`):
          a record on day `end` IS returned, so its caller must NOT add a day.

        Both behaviors confirmed live; see `generic.to_api_upper_bound` and
        `syncers.discover_convocatoria_codes`.
        """
        self.calls.append((method, {"start": start, "end": end}))
        for rec in records:
            d = reg_date(rec["reg_days_ago"])
            if start <= d <= end if upper_inclusive else start <= d < end:
                yield rec["payload"]

    def fetch_concesiones_busqueda(self, fechaRegInicio, fechaRegFin):
        yield from self._windowed(
            "fetch_concesiones_busqueda", self.concesiones_busqueda, fechaRegInicio, fechaRegFin
        )

    def fetch_ayudasestado_busqueda(self, fechaRegInicio, fechaRegFin):
        yield from self._windowed(
            "fetch_ayudasestado_busqueda", self.ayudasestado_busqueda, fechaRegInicio, fechaRegFin
        )

    def fetch_minimis_busqueda(self, fechaRegInicio, fechaRegFin):
        yield from self._windowed(
            "fetch_minimis_busqueda", self.minimis_busqueda, fechaRegInicio, fechaRegFin
        )

    def fetch_partidospoliticos_busqueda(self, fechaRegInicio, fechaRegFin):
        yield from self._windowed(
            "fetch_partidospoliticos_busqueda", self.partidospoliticos_busqueda, fechaRegInicio, fechaRegFin
        )

    def fetch_convocatorias_busqueda(self, fechaDesde, fechaHasta):
        # convocatorias' fechaHasta is inclusive, unlike the fechaRegFin endpoints
        yield from self._windowed(
            "fetch_convocatorias_busqueda",
            self.convocatorias_busqueda,
            fechaDesde,
            fechaHasta,
            upper_inclusive=True,
        )

    # Discover-then-detail.

    def fetch_convocatorias(self, numConv):
        self.calls.append(("fetch_convocatorias", {"numConv": numConv}))
        detail = self.convocatorias_detail.get(numConv)
        if detail is None:
            return
        yield detail

    # grandesbeneficiarios: dynamic anios sweep.

    def fetch_grandesbeneficiarios_anios(self):
        yield from self.grandesbeneficiarios_anios

    def fetch_grandesbeneficiarios_busqueda(self, anios):
        self.calls.append(("fetch_grandesbeneficiarios_busqueda", {"anios": list(anios)}))
        for rec in self.grandesbeneficiarios_busqueda:
            if rec["ejercicio"] in anios:
                yield rec

    # planesestrategicos: discovery, detail, and vigencia.

    def fetch_planesestrategicos_busqueda(self):
        yield from self.planesestrategicos_busqueda

    def fetch_planesestrategicos(self, idPES):
        self.calls.append(("fetch_planesestrategicos", {"idPES": idPES}))
        detail = self.planesestrategicos_detail.get(str(idPES))
        if detail is None:
            return
        yield detail

    def fetch_planesestrategicos_vigencia(self, idPES):
        self.calls.append(("fetch_planesestrategicos_vigencia", {"idPES": idPES}))
        vig = self.planesestrategicos_vigencia.get(str(idPES))
        if vig is None:
            return
        yield vig

    # Test helpers.

    def calls_to(self, method: str) -> list[dict]:
        return [kwargs for name, kwargs in self.calls if name == method]
