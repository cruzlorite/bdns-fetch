"""What the data model records beyond the payload: who wrote and closed each
version and why, key conflicts, the run log's counters, and the additive
migration that brings an older target up to date. Runs on every engine
`BDNS_SYNC_TEST_URL` selects."""

from datetime import date

import pytest
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    MetaData,
    String,
    Table,
    inspect,
    select,
)
from sqlalchemy.types import Text

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.migrate import add_missing_columns
from bdns.sync.sinks.sql.scd2 import NaturalKeyConflict
from bdns.sync.sinks.sql.schema import build_control_tables, build_sync_table


def versions(engine, name):
    table = build_sync_table(name, MetaData())
    with engine.begin() as conn:
        return conn.execute(select(table).order_by(table.c._valid_from)).mappings().all()


def run_events(engine, name):
    _, runs, _ = build_control_tables(MetaData())
    with engine.begin() as conn:
        return (
            conn.execute(select(runs).where(runs.c.table_name == name).order_by(runs.c.occurred_at))
            .mappings()
            .all()
        )


def success_run_ids(engine, name):
    return [e["run_id"] for e in run_events(engine, name) if e["event"] == "success"]


def test_versions_name_the_run_that_wrote_and_closed_them(engine, table_name):
    sink = SQLSink(engine)
    sink.sync_full(table_name, [{"id": 1, "v": "a"}, {"id": 2}], ("id",))
    sink.sync_full(table_name, [{"id": 1, "v": "b"}], ("id",))
    first_run, second_run = success_run_ids(engine, table_name)

    rows = versions(engine, table_name)
    by_state = {(r["_natural_key"], r["_is_current"]): r for r in rows}
    superseded = by_state[("[1]", False)]
    removed = by_state[("[2]", False)]
    current = by_state[("[1]", True)]

    assert superseded["_created_run_id"] == first_run
    assert (superseded["_closed_run_id"], superseded["_closed_reason"]) == (
        second_run,
        "superseded",
    )
    assert (removed["_closed_run_id"], removed["_closed_reason"]) == (second_run, "removed")
    assert current["_created_run_id"] == second_run
    assert current["_closed_run_id"] is None and current["_closed_reason"] is None


def test_windowed_deletion_is_recorded_as_removed(engine, table_name):
    sink = SQLSink(engine)
    window = {
        "window_start": date(2024, 1, 1),
        "window_end": date(2024, 1, 31),
        "run_type": "monthly",
    }
    sink.sync_window(
        table_name,
        [{"id": 1, "f": "2024-01-10"}, {"id": 2, "f": "2024-01-11"}],
        ("id",),
        reg_date_field="f",
        **window,
    )
    sink.sync_window(
        table_name, [{"id": 1, "f": "2024-01-10"}], ("id",), reg_date_field="f", **window
    )
    closed = [r for r in versions(engine, table_name) if not r["_is_current"]]
    assert [(r["_natural_key"], r["_closed_reason"]) for r in closed] == [("[2]", "removed")]


def test_a_key_carrying_two_payloads_fails_the_run(engine, table_name):
    sink = SQLSink(engine)
    with pytest.raises(NaturalKeyConflict, match=r"\[1\]"):
        sink.sync_full(table_name, [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}], ("id",))
    assert [e["event"] for e in run_events(engine, table_name)] == ["started", "failed"]
    assert versions(engine, table_name) == []


def test_byte_identical_duplicates_are_not_a_conflict(engine, table_name):
    stats = SQLSink(engine).sync_full(table_name, [{"id": 1}, {"id": 1}], ("id",))
    assert stats.new == 1
    assert len(versions(engine, table_name)) == 1


def test_run_log_records_every_counter_and_the_window(engine, table_name):
    sink = SQLSink(engine)
    window = {
        "window_start": date(2024, 1, 1),
        "window_end": date(2024, 1, 7),
        "run_type": "weekly",
    }
    sink.sync_window(table_name, [{"id": 1}, {"id": 2}], ("id",), **window)
    sink.sync_window(table_name, [{"id": 1}, {"id": 2, "v": "x"}, {"id": 3}], ("id",), **window)
    last = run_events(engine, table_name)[-1]
    assert last["event"] == "success"
    assert (
        last["rows_fetched"],
        last["rows_inserted"],
        last["rows_changed"],
        last["rows_unchanged"],
    ) == (
        3,
        2,
        1,
        1,
    )
    assert (last["window_start"], last["window_end"]) == (date(2024, 1, 1), date(2024, 1, 7))


def _old_entity_table(name, metadata):
    """The entity table as the first releases created it."""
    return Table(
        name,
        metadata,
        Column("_natural_key", String, nullable=False),
        Column("_row_hash", String(64), nullable=False),
        Column("_valid_from", DateTime(timezone=True), nullable=False),
        Column("_valid_to", DateTime(timezone=True), nullable=True),
        Column("_is_current", Boolean, nullable=False),
        Column("_synced_at", DateTime(timezone=True), nullable=False),
        Column("_reg_date", Date, nullable=True),
        Column("payload", Text, nullable=False),
    )


def test_an_older_target_is_upgraded_in_place(engine, table_name):
    old = MetaData()
    _old_entity_table(table_name, old).create(engine)
    try:
        stats = SQLSink(engine).sync_full(table_name, [{"id": 1}], ("id",))
        assert stats.new == 1
        columns = {c["name"] for c in inspect(engine).get_columns(table_name)}
        assert {"_created_run_id", "_closed_run_id", "_closed_reason"} <= columns
    finally:
        old.drop_all(engine)


def test_migration_adds_nothing_to_an_up_to_date_table(engine, table_name):
    metadata = MetaData()
    table = build_sync_table(table_name, metadata)
    metadata.create_all(engine)
    try:
        assert add_missing_columns(engine, [table]) == []
    finally:
        metadata.drop_all(engine)


def test_migration_refuses_a_missing_not_null_column(engine, table_name):
    old = MetaData()
    Table(table_name, old, Column("a", BigInteger)).create(engine)
    try:
        new = Table(
            table_name, MetaData(), Column("a", BigInteger), Column("b", BigInteger, nullable=False)
        )
        with pytest.raises(ValueError, match="NOT NULL"):
            add_missing_columns(engine, [new])
    finally:
        old.drop_all(engine)
