"""Idempotency, asserted as a property rather than inferred from counters.

This is the promise the documentation makes to operators and that the whole
recovery story rests on: no `success` event means re-run, and re-running
anything is safe. Other tests check that a second pass reports `touched`;
these check the stronger thing, that the stored history is byte-identical
afterwards. A bug that closed and reinserted an unchanged row would still
report sensible-looking counters while doubling the table on every run.
"""

from datetime import date

from sqlalchemy import select

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.schema import build_sync_table


def history(engine, metadata, name):
    """Every version of every key, minus `_synced_at`.

    `_synced_at` is the one column a repeat run is meant to move: it
    records that the row was seen again. Everything else defines the
    history and must not budge.
    """
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        rows = conn.execute(
            select(
                table.c._natural_key,
                table.c._row_hash,
                table.c._valid_from,
                table.c._valid_to,
                table.c._is_current,
                table.c._reg_date,
            )
        ).all()
    return sorted(rows, key=lambda r: (r._natural_key, r._valid_from))


CATALOG = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 3, "v": "c"}]


def test_repeating_a_full_sync_never_changes_the_history(engine, metadata, table_name):
    sink = SQLSink(engine)
    sink.sync_full(table_name, list(CATALOG), ("id",))
    after_first = history(engine, metadata, table_name)

    for _ in range(2):
        stats = sink.sync_full(table_name, list(CATALOG), ("id",))
        assert stats["inserted"] == 0
        assert stats["updated"] == 0
        assert stats["soft_deleted"] == 0
        assert history(engine, metadata, table_name) == after_first

    assert len(after_first) == 3


def test_repeating_a_sync_after_a_real_change_is_also_stable(engine, metadata, table_name):
    """The version created by a genuine edit must settle: one closed
    version, one current, and no further churn however often it re-runs.
    """
    sink = SQLSink(engine)
    sink.sync_full(table_name, list(CATALOG), ("id",))

    changed = [dict(row, v="EDITED") if row["id"] == 2 else row for row in CATALOG]
    sink.sync_full(table_name, list(changed), ("id",))
    after_change = history(engine, metadata, table_name)
    assert len(after_change) == 4  # 3 keys, one of them with a closed old version

    for _ in range(2):
        sink.sync_full(table_name, list(changed), ("id",))
        assert history(engine, metadata, table_name) == after_change


def test_repeating_a_sync_after_a_deletion_does_not_reclose_or_resurrect(engine, metadata, table_name):
    sink = SQLSink(engine)
    sink.sync_full(table_name, list(CATALOG), ("id",))

    remaining = [row for row in CATALOG if row["id"] != 3]
    stats = sink.sync_full(table_name, list(remaining), ("id",))
    assert stats["soft_deleted"] == 1
    after_deletion = history(engine, metadata, table_name)

    for _ in range(2):
        stats = sink.sync_full(table_name, list(remaining), ("id",))
        assert stats["soft_deleted"] == 0
        assert stats["inserted"] == 0
        assert history(engine, metadata, table_name) == after_deletion


WINDOW_ROWS = [
    {"id": 1, "fecha": "2026-03-02"},
    {"id": 2, "fecha": "2026-03-05"},
]
WINDOW = {"window_start": date(2026, 3, 1), "window_end": date(2026, 3, 31), "run_type": "monthly"}


def test_repeating_a_windowed_sync_never_changes_the_history(engine, metadata, table_name):
    """Same property on the incremental path, where a re-run also re-runs
    window-scoped deletion detection. A row present in both passes must
    not be closed the second time.
    """
    sink = SQLSink(engine)
    sink.sync_window(table_name, list(WINDOW_ROWS), ("id",), reg_date_field="fecha", **WINDOW)
    after_first = history(engine, metadata, table_name)

    for _ in range(2):
        stats = sink.sync_window(
            table_name, list(WINDOW_ROWS), ("id",), reg_date_field="fecha", **WINDOW
        )
        assert stats["inserted"] == 0
        assert stats["soft_deleted"] == 0
        assert history(engine, metadata, table_name) == after_first


def test_rerunning_a_window_that_closed_a_row_stays_settled(engine, metadata, table_name):
    sink = SQLSink(engine)
    sink.sync_window(table_name, list(WINDOW_ROWS), ("id",), reg_date_field="fecha", **WINDOW)

    withdrawn = WINDOW_ROWS[:1]
    stats = sink.sync_window(table_name, list(withdrawn), ("id",), reg_date_field="fecha", **WINDOW)
    assert stats["soft_deleted"] == 1
    after_deletion = history(engine, metadata, table_name)

    for _ in range(2):
        stats = sink.sync_window(
            table_name, list(withdrawn), ("id",), reg_date_field="fecha", **WINDOW
        )
        assert stats["soft_deleted"] == 0
        assert history(engine, metadata, table_name) == after_deletion


def test_a_wider_window_over_the_same_data_adds_nothing(engine, metadata, table_name):
    """The cascade runs annual over ground that weekly already covered.
    A wider window must recognize what the narrower one stored, not
    re-version it.
    """
    sink = SQLSink(engine)
    sink.sync_window(table_name, list(WINDOW_ROWS), ("id",), reg_date_field="fecha", **WINDOW)
    after_narrow = history(engine, metadata, table_name)

    stats = sink.sync_window(
        table_name,
        list(WINDOW_ROWS),
        ("id",),
        window_start=date(2026, 1, 1),
        window_end=date(2026, 12, 31),
        run_type="annual",
        reg_date_field="fecha",
    )
    assert stats["inserted"] == 0
    assert stats["updated"] == 0
    assert stats["soft_deleted"] == 0
    assert history(engine, metadata, table_name) == after_narrow
