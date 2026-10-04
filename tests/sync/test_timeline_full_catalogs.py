"""Multi-day scenarios for every full-replace-every-run entity (the "Simple"
row of the endpoint table in docs/sync/explanation/endpoint-types.md): sectores, actividades, finalidades,
beneficiarios, instrumentos, objetivos, regiones,
sanciones_busqueda. Real anonymized payloads, real key fields, one shared
day-by-day script covering insert / touch / rewrite / deletion / new-arrival.

Deletion detection is the interesting case here: these are exactly the
entities where a full-reconciliation pass sees the whole current state each
run, so a row missing from the fetch means "withdrawn". That's unlike the
incremental window entities in test_timeline_incremental_windows.py.
"""

from copy import deepcopy
from functools import partial

import pytest
from sqlalchemy import create_engine

from bdns.sync.entities import sync_entity
from bdns.sync.sinks import SyncStats
from bdns.sync.sinks.sql import SQLSink
from tests.sync.fake_client import FakeBDNSClient
from tests.sync.timeline_helpers import all_rows, current_rows, fresh_copy_with_new_key

# (sync_fn, client attribute holding the fixture list, table name, key
# fields matching the syncer's own key_fields, a non-key field safe to
# mutate for the "rewrite" day)
FULL_CATALOG_CASES = [
    (partial(sync_entity, "sectores"), "sectores", "sectores", ("id",), "descripcion"),
    (partial(sync_entity, "actividades"), "actividades", "actividades", ("id",), "descripcion"),
    (partial(sync_entity, "finalidades"), "finalidades", "finalidades", ("id",), "descripcion"),
    (
        partial(sync_entity, "beneficiarios"),
        "beneficiarios",
        "beneficiarios",
        ("id",),
        "descripcion",
    ),
    (partial(sync_entity, "instrumentos"), "instrumentos", "instrumentos", ("id",), "descripcion"),
    (partial(sync_entity, "objetivos"), "objetivos", "objetivos", ("id",), "descripcion"),
    (partial(sync_entity, "regiones"), "regiones", "regiones", ("id",), "descripcion"),
    (
        partial(sync_entity, "grandesbeneficiarios_anios"),
        "grandesbeneficiarios_anios",
        "grandesbeneficiarios_anios",
        ("id",),
        "descripcion",
    ),
    (
        partial(sync_entity, "planesestrategicos_busqueda"),
        "planesestrategicos_busqueda",
        "planesestrategicos_busqueda",
        ("id",),
        "descripcion",
    ),
    (
        partial(sync_entity, "sanciones_busqueda"),
        "sanciones_busqueda",
        "sanciones_busqueda",
        ("numeroConvocatoria", "sancionado", "fechaSancion"),
        "importeMulta",
    ),
]

CASE_IDS = [case[2] for case in FULL_CATALOG_CASES]


@pytest.mark.parametrize(
    "sync_fn,attr,table,key_fields,mutate_field", FULL_CATALOG_CASES, ids=CASE_IDS
)
def test_full_catalog_day_by_day_timeline(sync_fn, attr, table, key_fields, mutate_field):
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    baseline = deepcopy(getattr(client, attr))
    assert len(baseline) >= 2, "fixture needs >=2 rows to exercise update and delete independently"

    # Day 1: first run, every fetched row is new
    stats = sync_fn(SQLSink(engine), client)
    assert stats.fetched == len(baseline)
    assert stats.new == len(baseline)
    assert stats.changed == 0
    assert stats.removed == 0
    assert len(current_rows(engine, table)) == len(baseline)

    # Day 2: identical re-fetch, a pure no-op that only touches `_synced_at`
    stats = sync_fn(SQLSink(engine), client)
    assert stats == SyncStats(fetched=len(baseline), unchanged=len(baseline))

    # Day 3: upstream edits one field on one row. SCD2 rewrite: the old
    # version is closed out and the new version becomes current.
    getattr(client, attr)[0][mutate_field] = "__MUTATED__"
    stats = sync_fn(SQLSink(engine), client)
    assert stats.changed == 1
    assert stats.new == 0
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
    assert stats.removed == 1
    assert len(current_rows(engine, table)) == len(baseline) - 1

    # Day 5: a brand-new row is registered, a plain insert
    new_row = fresh_copy_with_new_key(baseline[1], key_fields)
    getattr(client, attr).append(new_row)
    stats = sync_fn(SQLSink(engine), client)
    assert stats.new == 1
    assert len(current_rows(engine, table)) == len(baseline)
