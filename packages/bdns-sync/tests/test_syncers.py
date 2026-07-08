from datetime import date, timedelta

from sqlalchemy import MetaData, create_engine, select

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.schema import build_sync_table
from bdns.sync.syncers import (
    sync_convocatorias,
    sync_grandesbeneficiarios_busqueda,
    sync_planesestrategicos,
    sync_planesestrategicos_vigencia,
)


def current_rows(engine, name):
    metadata = MetaData()
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(table).where(table.c._is_current.is_(True))
        ).mappings().all()


# --- convocatorias: two-step discover-then-detail -------------------------


class FakeConvocatoriasClient:
    def __init__(self, search_results, details_by_code):
        self._search_results = search_results
        self._details_by_code = details_by_code
        self.detail_calls = []

    def fetch_convocatorias_busqueda(self, fechaDesde, fechaHasta):
        self.last_search_window = (fechaDesde, fechaHasta)
        yield from self._search_results

    def fetch_convocatorias(self, numConv):
        self.detail_calls.append(numConv)
        yield self._details_by_code[numConv]


def test_convocatorias_discover_then_detail_end_to_end():
    engine = create_engine("sqlite:///:memory:")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client = FakeConvocatoriasClient(
        search_results=[{"numeroConvocatoria": "A1"}, {"numeroConvocatoria": "A2"}],
        details_by_code={
            "A1": {"codigoBDNS": "A1", "titulo": "one", "fechaRecepcion": yesterday},
            "A2": {"codigoBDNS": "A2", "titulo": "two", "fechaRecepcion": yesterday},
        },
    )
    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats == {"fetched": 2, "inserted": 2, "updated": 0, "touched": 0, "soft_deleted": 0, "skipped": 0}
    assert sorted(client.detail_calls) == ["A1", "A2"]

    # daily covers just yesterday; convocatorias' fechaHasta is inclusive,
    # so it's sent as yesterday directly (no +1, unlike the fechaReg endpoints)
    yesterday = date.today() - timedelta(days=1)
    assert client.last_search_window == (yesterday, yesterday)

    rows = current_rows(engine, "convocatorias")
    assert {r["_natural_key"] for r in rows} == {'["A1"]', '["A2"]'}


def test_convocatorias_one_detail_call_per_discovered_code_only():
    """N codes discovered -> exactly N detail calls, no per-record fan-out beyond that."""
    engine = create_engine("sqlite:///:memory:")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client = FakeConvocatoriasClient(
        search_results=[{"numeroConvocatoria": "A1"}],
        details_by_code={"A1": {"codigoBDNS": "A1", "fechaRecepcion": yesterday}},
    )
    sync_convocatorias(SQLSink(engine), client, "weekly")
    assert client.detail_calls == ["A1"]


def test_convocatorias_closes_out_a_code_missing_from_the_same_window():
    """Window-scoped deletion: A2's own `fechaRecepcion` is inside daily's
    range both times, so if it's genuinely missing from the second daily
    run, that's a real deletion (see tests/test_timeline_convocatorias.py
    for the aging-vs-deletion distinction this relies on).
    """
    engine = create_engine("sqlite:///:memory:")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client = FakeConvocatoriasClient(
        search_results=[{"numeroConvocatoria": "A1"}, {"numeroConvocatoria": "A2"}],
        details_by_code={
            "A1": {"codigoBDNS": "A1", "fechaRecepcion": yesterday},
            "A2": {"codigoBDNS": "A2", "fechaRecepcion": yesterday},
        },
    )
    sync_convocatorias(SQLSink(engine), client, "daily")

    client._search_results = [{"numeroConvocatoria": "A1"}]
    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, "convocatorias")) == 1  # A2 closed out


# --- grandesbeneficiarios --------------------------------------------------


class FakeGrandesClient:
    def __init__(self, anios, grandes):
        self._anios = anios
        self._grandes = grandes
        self.anios_used = None

    def fetch_grandesbeneficiarios_anios(self):
        yield from self._anios

    def fetch_grandesbeneficiarios_busqueda(self, anios):
        self.anios_used = anios
        yield from self._grandes


def test_grandesbeneficiarios_sweeps_anios_dynamically():
    engine = create_engine("sqlite:///:memory:")
    client = FakeGrandesClient(
        anios=[{"id": 2022}, {"id": 2023}],
        grandes=[{"idPersona": 1, "ejercicio": 2022}, {"idPersona": 1, "ejercicio": 2023}],
    )
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert client.anios_used == [2022, 2023]
    assert stats["inserted"] == 2

    rows = current_rows(engine, "grandesbeneficiarios_busqueda")
    assert {r["_natural_key"] for r in rows} == {"[1,2022]", "[1,2023]"}


# --- planesestrategicos -----------------------------------------------------


class FakePesClient:
    def __init__(self, ids, details_by_id=None, vigencias_by_id=None):
        self._ids = ids
        self._details_by_id = details_by_id or {}
        self._vigencias_by_id = vigencias_by_id or {}

    def fetch_planesestrategicos_busqueda(self):
        for id_pes in self._ids:
            yield {"id": id_pes}

    def fetch_planesestrategicos(self, idPES):
        # real API does not echo idPES back in the detail payload
        yield self._details_by_id[idPES]

    def fetch_planesestrategicos_vigencia(self, idPES):
        yield self._vigencias_by_id[idPES]


def test_planesestrategicos_detail_tags_idpes_since_api_does_not_echo_it():
    engine = create_engine("sqlite:///:memory:")
    client = FakePesClient(ids=[2078], details_by_id={2078: {"descripcion": "PES test"}})
    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["inserted"] == 1

    rows = current_rows(engine, "planesestrategicos")
    assert rows[0]["_natural_key"] == "[2078]"
    assert rows[0]["payload"]["idPES"] == 2078
    assert rows[0]["payload"]["descripcion"] == "PES test"


def test_planesestrategicos_vigencia_synced_as_separate_table():
    engine = create_engine("sqlite:///:memory:")
    client = FakePesClient(
        ids=[2078],
        vigencias_by_id={2078: {"vigDesde": [{"id": 2020}], "vigHasta": [{"id": 2028}]}},
    )
    stats = sync_planesestrategicos_vigencia(SQLSink(engine), client)
    assert stats["inserted"] == 1
    rows = current_rows(engine, "planesestrategicos_vigencia")
    assert rows[0]["_natural_key"] == "[2078]"
