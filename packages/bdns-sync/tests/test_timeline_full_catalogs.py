"""Multi-day scenarios for every full-replace-every-run entity (the "Simple"
row of the README endpoint table): sectores, actividades, finalidades,
beneficiarios, instrumentos, objetivos, convocatorias_ultimas, regiones,
sanciones_busqueda. Real anonymized payloads, real key fields, one shared
day-by-day script covering insert / touch / rewrite / deletion / new-arrival.

Deletion detection is the interesting case here: these are exactly the
entities where a full-reconciliation pass sees the whole current state each
run, so a row missing from the fetch means "withdrawn". That's unlike the
incremental window entities in test_timeline_incremental_windows.py.
"""

from copy import deepcopy

import pytest
from sqlalchemy import create_engine

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.syncers import (
    sync_actividades,
    sync_beneficiarios,
    sync_convocatorias_ultimas,
    sync_finalidades,
    sync_grandesbeneficiarios_anios,
    sync_instrumentos,
    sync_objetivos,
    sync_planesestrategicos_busqueda,
    sync_regiones,
    sync_sanciones_busqueda,
    sync_sectores,
)
from tests.fake_client import FakeBDNSClient
from tests.timeline_helpers import all_rows, current_rows, fresh_copy_with_new_key

# (sync_fn, client attribute holding the fixture list, table name, key
# fields matching the syncer's own key_fields, a non-key field safe to
# mutate for the "rewrite" day)
FULL_CATALOG_CASES = [
    (sync_sectores, "sectores", "sectores", ("id",), "descripcion"),
    (sync_actividades, "actividades", "actividades", ("id",), "descripcion"),
    (sync_finalidades, "finalidades", "finalidades", ("id",), "descripcion"),
    (sync_beneficiarios, "beneficiarios", "beneficiarios", ("id",), "descripcion"),
    (sync_instrumentos, "instrumentos", "instrumentos", ("id",), "descripcion"),
    (sync_objetivos, "objetivos", "objetivos", ("id",), "descripcion"),
    (sync_convocatorias_ultimas, "convocatorias_ultimas", "convocatorias_ultimas", ("id",), "descripcion"),
    (sync_regiones, "regiones", "regiones", ("id",), "descripcion"),
    (
        sync_grandesbeneficiarios_anios,
        "grandesbeneficiarios_anios",
        "grandesbeneficiarios_anios",
        ("id",),
        "descripcion",
    ),
    (
        sync_planesestrategicos_busqueda,
        "planesestrategicos_busqueda",
        "planesestrategicos_busqueda",
        ("id",),
        "descripcion",
    ),
    (
        sync_sanciones_busqueda,
        "sanciones_busqueda",
        "sanciones_busqueda",
        ("numeroConvocatoria", "sancionado", "fechaSancion"),
        "importeMulta",
    ),
]

CASE_IDS = [case[2] for case in FULL_CATALOG_CASES]


@pytest.mark.parametrize("sync_fn,attr,table,key_fields,mutate_field", FULL_CATALOG_CASES, ids=CASE_IDS)
def test_full_catalog_day_by_day_timeline(sync_fn, attr, table, key_fields, mutate_field):
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    baseline = deepcopy(getattr(client, attr))
    assert len(baseline) >= 2, "fixture needs >=2 rows to exercise update and delete independently"

    # Day 1: first run, every fetched row is new
    stats = sync_fn(SQLSink(engine), client)
    assert stats["fetched"] == len(baseline)
    assert stats["inserted"] == len(baseline)
    assert stats["updated"] == 0
    assert stats["soft_deleted"] == 0
    assert len(current_rows(engine, table)) == len(baseline)

    # Day 2: identical re-fetch, a pure no-op that only touches `_synced_at`
    stats = sync_fn(SQLSink(engine), client)
    assert stats == {"fetched": len(baseline), "inserted": 0, "updated": 0, "touched": len(baseline), "soft_deleted": 0}

    # Day 3: upstream edits one field on one row. SCD2 rewrite: the old
    # version is closed out and the new version becomes current.
    getattr(client, attr)[0][mutate_field] = "__MUTATED__"
    stats = sync_fn(SQLSink(engine), client)
    assert stats["updated"] == 1
    assert stats["inserted"] == 0
    history = all_rows(engine, table)
    closed = [r for r in history if not r["_is_current"]]
    assert len(closed) == 1
    assert closed[0]["_valid_to"] is not None
    current = current_rows(engine, table)
    assert len(current) == len(baseline)  # same key set, versioned in place
    mutated_key = closed[0]["_natural_key"]
    new_version = next(r for r in current if r["_natural_key"] == mutated_key)
    assert new_version["payload"][mutate_field] == "__MUTATED__"

    # Day 4: upstream withdraws the last row. Full reconciliation must
    # detect it as a deletion; no incremental pass could see this.
    getattr(client, attr).pop()
    stats = sync_fn(SQLSink(engine), client)
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, table)) == len(baseline) - 1

    # Day 5: a brand-new row is registered, a plain insert
    new_row = fresh_copy_with_new_key(baseline[1], key_fields)
    getattr(client, attr).append(new_row)
    stats = sync_fn(SQLSink(engine), client)
    assert stats["inserted"] == 1
    assert len(current_rows(engine, table)) == len(baseline)
