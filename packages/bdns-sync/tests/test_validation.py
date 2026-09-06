"""Record validation in the sink: what happens when the source sends
something that cannot be versioned.

The sink is the backstop for every entity. `syncers._skip_malformed` only
guards the two-step detail fetches and only catches responses that are not
JSON objects, so the twenty entities that go through a plain search or
catalog fetch had nothing at all before this.

The null key is the case these tests exist for. It never raised: it
serialized to the literal key `[null]`, so every record missing that field
landed on one key, overwriting each other run after run under a `success`
event.
"""

from datetime import date

import pytest
from sqlalchemy import select

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.scd2 import BatchRejected
from bdns.sync.sinks.sql.schema import build_control_tables, build_sync_table


def current(engine, metadata, name):
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        return conn.execute(select(table).where(table.c._is_current.is_(True))).mappings().all()


def errors(engine, metadata, name):
    _, _, sync_errors = build_control_tables(metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(sync_errors).where(sync_errors.c.table_name == name)
        ).mappings().all()


GOOD = [{"id": i, "v": "x"} for i in range(1, 12)]


def test_a_record_missing_the_key_field_is_rejected_not_raised(engine, metadata, table_name):
    stats = SQLSink(engine).sync_full(table_name, GOOD + [{"v": "no key"}], ("id",))
    assert stats["fetched"] == 11
    assert stats["inserted"] == 11
    assert stats["skipped"] == 1
    assert len(current(engine, metadata, table_name)) == 11

    [err] = errors(engine, metadata, table_name)
    assert err["context"] == "missing key field id"
    assert "no key" in err["content"]


def test_a_null_key_is_rejected_instead_of_collapsing_onto_one_key(engine, metadata, table_name):
    """Before this, two records with a null key both serialized to `[null]`
    and both were written as current versions of that single key.
    """
    rows = GOOD + [{"id": None, "v": "a"}, {"id": None, "v": "b"}]
    stats = SQLSink(engine).sync_full(table_name, rows, ("id",))

    assert stats["skipped"] == 2
    stored = current(engine, metadata, table_name)
    assert len(stored) == 11
    assert "[null]" not in {row["_natural_key"] for row in stored}
    assert {err["context"] for err in errors(engine, metadata, table_name)} == {"null key field id"}


def test_a_response_that_is_not_a_json_object_is_rejected(engine, metadata, table_name):
    """An HTML error page reaching a plain search endpoint used to raise
    `TypeError: string indices must be integers` and kill the run.
    """
    stats = SQLSink(engine).sync_full(table_name, GOOD + ["<html>error</html>"], ("id",))
    assert stats["fetched"] == 11
    assert stats["skipped"] == 1
    [err] = errors(engine, metadata, table_name)
    assert err["context"] == "record is not a JSON object"


def test_a_composite_key_is_rejected_when_any_part_is_missing(engine, metadata, table_name):
    rows = [{"a": i, "b": i} for i in range(11)] + [{"a": 99}]
    stats = SQLSink(engine).sync_full(table_name, rows, ("a", "b"))
    assert stats["skipped"] == 1
    assert errors(engine, metadata, table_name)[0]["context"] == "missing key field b"


# --- registration date -----------------------------------------------------


def windowed(engine, table_name, rows, **kwargs):
    return SQLSink(engine).sync_window(
        table_name,
        rows,
        ("id",),
        window_start=date(2026, 3, 1),
        window_end=date(2026, 3, 31),
        run_type="monthly",
        **kwargs,
    )


def test_a_missing_registration_date_is_rejected_where_the_entity_uses_one(
    engine, metadata, table_name
):
    rows = [{"id": i, "fecha": "2026-03-02"} for i in range(11)] + [{"id": 99}]
    stats = windowed(engine, table_name, rows, reg_date_field="fecha")
    assert stats["skipped"] == 1
    assert errors(engine, metadata, table_name)[0]["context"] == (
        "missing or null registration date fecha"
    )


def test_a_registration_date_carrying_a_time_is_rejected(engine, metadata, table_name):
    """Strict `%Y-%m-%d` on purpose. If the source starts sending
    datetimes, that belongs in `_sync_errors` as a visible change, not
    absorbed by a lenient parser.
    """
    rows = [{"id": i, "fecha": "2026-03-02"} for i in range(11)]
    rows.append({"id": 99, "fecha": "2026-03-02T00:00:00"})
    stats = windowed(engine, table_name, rows, reg_date_field="fecha")
    assert stats["skipped"] == 1
    assert "unparseable registration date" in errors(engine, metadata, table_name)[0]["context"]


def test_a_missing_date_field_is_fine_where_the_entity_declares_none(engine, metadata, table_name):
    """partidospoliticos_busqueda carries no registration date at all, so
    nothing about dates may be required of it.
    """
    stats = windowed(engine, table_name, [{"id": 1}, {"id": 2}])
    assert stats["skipped"] == 0
    assert stats["inserted"] == 2


# --- the ceiling -----------------------------------------------------------


def test_a_batch_rejected_wholesale_fails_instead_of_emptying_the_window(
    engine, metadata, table_name
):
    """The destructive shape: staging left empty by rejects looks exactly
    like "everything in this window was withdrawn".
    """
    windowed(engine, table_name, [{"id": 1, "fecha": "2026-03-02"}], reg_date_field="fecha")
    before = current(engine, metadata, table_name)
    assert len(before) == 1

    with pytest.raises(BatchRejected, match="refusing to apply"):
        windowed(engine, table_name, [{"id": None, "fecha": "2026-03-02"}], reg_date_field="fecha")

    assert current(engine, metadata, table_name) == before


def test_many_rejects_over_the_ratio_fail_the_run(engine, metadata, table_name):
    rows = [{"id": i} for i in range(20)] + [{"v": "bad"} for _ in range(20)]
    with pytest.raises(BatchRejected, match="could not be versioned"):
        SQLSink(engine).sync_full(table_name, rows, ("id",))
    assert current(engine, metadata, table_name) == []


def test_a_few_rejects_in_a_small_batch_do_not_fail_the_run(engine, metadata, table_name):
    """One bad record out of three is a third of the batch, but individual
    broken records are a permanent trait of this source and a narrow window
    holds few records. The ratio only bites once there are several.
    """
    stats = SQLSink(engine).sync_full(table_name, [{"id": 1}, {"id": 2}, {"v": "bad"}], ("id",))
    assert stats["inserted"] == 2
    assert stats["skipped"] == 1


def test_a_low_share_of_rejects_in_a_large_batch_does_not_fail_the_run(
    engine, metadata, table_name
):
    """planesestrategicos skips about eleven records out of two thousand on
    every run and must keep syncing.
    """
    rows = [{"id": i} for i in range(200)] + [{"v": "bad"} for _ in range(11)]
    stats = SQLSink(engine).sync_full(table_name, rows, ("id",))
    assert stats["inserted"] == 200
    assert stats["skipped"] == 11
    assert len(errors(engine, metadata, table_name)) == 11
