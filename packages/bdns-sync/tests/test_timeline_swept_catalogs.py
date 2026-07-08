"""Multi-day scenarios for the "Barrido" (swept) endpoints: organos,
organos_agrupacion, reglamentos. These sweep a parameter (idAdmon/ambito)
across a fixed set of values and merge every value's rows into one table
before diffing. Beyond the plain insert/touch/rewrite/delete cycle already
covered for full catalogs, the thing worth proving here is that the merge
is real: populating one sweep value never closes out another value's rows
as "missing".
"""

from copy import deepcopy

import pytest
from sqlalchemy import create_engine

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.syncers import sync_organos, sync_organos_agrupacion, sync_reglamentos
from tests.fake_client import FakeBDNSClient
from tests.timeline_helpers import all_rows, current_rows

# (sync_fn, client dict attribute, table name, sweep value populated by the
# fixture, a second sweep value that starts empty, a field safe to mutate)
SWEPT_CASES = [
    (sync_organos, "organos", "organos", "C", "A", "descripcion"),
    (sync_organos_agrupacion, "organos_agrupacion", "organos_agrupacion", "C", "A", "descripcion"),
    (sync_reglamentos, "reglamentos", "reglamentos", "C", "A", "descripcion"),
]

CASE_IDS = [case[2] for case in SWEPT_CASES]


@pytest.mark.parametrize("sync_fn,attr,table,populated_value,empty_value,mutate_field", SWEPT_CASES, ids=CASE_IDS)
def test_swept_catalog_day_by_day_timeline(sync_fn, attr, table, populated_value, empty_value, mutate_field):
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    baseline = deepcopy(getattr(client, attr)[populated_value])
    assert len(baseline) >= 2

    # Day 1: first run. Every sweep value is fetched (asserted below), but
    # only the populated one contributes rows.
    stats = sync_fn(SQLSink(engine), client)
    assert stats["inserted"] == len(baseline)
    assert len(current_rows(engine, table)) == len(baseline)

    # Day 2: no change, touch only
    stats = sync_fn(SQLSink(engine), client)
    assert stats["inserted"] == 0
    assert stats["updated"] == 0
    assert stats["touched"] == len(baseline)

    # Day 3: rewrite, one field changes on one row in the populated value
    getattr(client, attr)[populated_value][0][mutate_field] = "__MUTATED__"
    stats = sync_fn(SQLSink(engine), client)
    assert stats["updated"] == 1
    closed = [r for r in all_rows(engine, table) if not r["_is_current"]]
    assert len(closed) == 1

    # Day 4: deletion. Withdrawing a row from the populated value is a
    # full-reconciliation deletion like any other full-catalog entity.
    getattr(client, attr)[populated_value].pop()
    stats = sync_fn(SQLSink(engine), client)
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, table)) == len(baseline) - 1

    # Day 5: a previously-empty sweep value gets its first row, which is
    # inserted, and critically does not close out the other value's rows.
    before = len(current_rows(engine, table))
    new_row = deepcopy(baseline[0])
    new_row["id"] = new_row["id"] + 999000
    getattr(client, attr)[empty_value].append(new_row)
    stats = sync_fn(SQLSink(engine), client)
    assert stats["inserted"] == 1
    assert stats["soft_deleted"] == 0  # the populated value's rows must be untouched
    assert len(current_rows(engine, table)) == before + 1


@pytest.mark.parametrize("sync_fn,attr,table,populated_value,empty_value,mutate_field", SWEPT_CASES, ids=CASE_IDS)
def test_swept_catalog_sweeps_every_declared_value(sync_fn, attr, table, populated_value, empty_value, mutate_field):
    """Every registered sweep value is actually requested, not just the one
    the fixture happens to populate. This is the "additional filters and
    options actually get used" check for the swept entities.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn(SQLSink(engine), client)

    method = {
        "organos": "fetch_organos",
        "organos_agrupacion": "fetch_organos_agrupacion",
        "reglamentos": "fetch_reglamentos",
    }[table]
    param = "idAdmon" if table != "reglamentos" else "ambito"
    requested = {call[param] for call in client.calls_to(method)}
    assert requested == set(getattr(client, attr).keys())
