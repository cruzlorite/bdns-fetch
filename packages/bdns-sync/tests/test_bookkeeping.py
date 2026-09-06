"""Run bookkeeping and staging lifecycle, against whatever engine
`BDNS_SYNC_TEST_URL` selects (see tests/conftest.py).

These cover the two guarantees the README makes to operators and that no
other test exercised: a failed run is still recorded as failed, and
staging is emptied at both ends of a run so a crashed run cannot leak its
rows into the next one's diff.
"""

import pytest
from sqlalchemy import desc, func, select

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.bookkeeping import run_with_bookkeeping
from bdns.sync.sinks.sql.dialects import get_adapter
from bdns.sync.sinks.sql.schema import build_control_tables, build_staging_table, build_sync_table


def events_for(engine, metadata, table_name):
    _, sync_runs, _ = build_control_tables(metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(sync_runs.c.event, sync_runs.c.error)
            .where(sync_runs.c.table_name == table_name)
            .order_by(sync_runs.c.occurred_at, sync_runs.c.event)
        ).all()


def staging_count(engine, staging):
    with engine.begin() as conn:
        return conn.execute(select(func.count()).select_from(staging)).scalar_one()


def test_failed_run_records_a_failed_event_and_reraises(engine, metadata, table_name):
    """A run that blows up must leave a durable `failed` event carrying the
    error text. The bookkeeping writes it in its own transaction precisely
    so that the data rollback cannot erase the record of the failure.
    """

    def boom(conn, table, staging):
        raise RuntimeError("upstream exploded")

    with pytest.raises(RuntimeError, match="upstream exploded"):
        run_with_bookkeeping(engine, table_name, run_type="full", apply_fn=boom)

    events = events_for(engine, metadata, table_name)
    assert [e.event for e in events] == ["started", "failed"]
    assert "upstream exploded" in events[1].error


def test_failed_run_leaves_no_success_event_and_no_rows(engine, metadata, table_name):
    """The operational rule the README states: no `success` event means
    re-run. The synced table must hold nothing from the failed attempt.
    """

    def boom(conn, table, staging):
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        run_with_bookkeeping(engine, table_name, run_type="full", apply_fn=boom)

    assert "success" not in [e.event for e in events_for(engine, metadata, table_name)]

    table = build_sync_table(table_name, metadata)
    with engine.begin() as conn:
        assert conn.execute(select(func.count()).select_from(table)).scalar_one() == 0


def test_successful_run_records_counters_on_the_terminal_event(engine, metadata, table_name):
    sink = SQLSink(engine)
    stats = sink.sync_full(table_name, [{"id": 1}, {"id": 2}], ("id",))
    assert stats["inserted"] == 2

    _, sync_runs, _ = build_control_tables(metadata)
    with engine.begin() as conn:
        row = conn.execute(
            select(sync_runs)
            .where(sync_runs.c.table_name == table_name, sync_runs.c.event == "success")
            .order_by(desc(sync_runs.c.run_id))
            .limit(1)
        ).mappings().one()
    assert row["rows_fetched"] == 2
    assert row["rows_inserted"] == 2


def test_staging_is_empty_after_a_run(engine, metadata, table_name):
    """Staging is scratch space, not storage. Leaving it populated would
    keep a full copy of the batch around until the next run, and on
    BigQuery that is billed storage for nothing.
    """
    SQLSink(engine).sync_full(table_name, [{"id": i} for i in range(5)], ("id",))
    staging = build_staging_table(table_name, metadata)
    assert staging_count(engine, staging) == 0


def test_leftover_staging_rows_do_not_leak_into_the_next_run(engine, metadata, table_name):
    """The convergence claim for engines without transactions: a run that
    died mid-diff can leave staging populated, and the next run must clear
    it before staging its own batch. Otherwise the stale rows would count
    as fetched and, worse, keep keys alive that the new batch no longer
    contains.
    """
    sink = SQLSink(engine)
    sink.sync_full(table_name, [{"id": 1}], ("id",))

    # Simulate the wreckage of a crashed run: staging left full.
    staging = build_staging_table(table_name, metadata)
    build_sync_table(table_name, metadata)
    metadata.create_all(engine, checkfirst=True)
    with engine.begin() as conn:
        get_adapter(engine).insert_rows(
            conn, staging, [{"_natural_key": "[999]", "_row_hash": "x" * 64, "payload": {"id": 999}}]
        )
    assert staging_count(engine, staging) == 1

    stats = sink.sync_full(table_name, [{"id": 1}], ("id",))
    assert stats["fetched"] == 1  # only the real batch, not the leftover
    assert stats["inserted"] == 0
    assert staging_count(engine, staging) == 0
