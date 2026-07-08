from datetime import date

import pytest
from sqlalchemy import MetaData, create_engine, select

from bdns.sync.sinks.sql.scd2 import apply_full_reconciliation, apply_incremental
from bdns.sync.sinks.sql.schema import build_staging_table, build_sync_table


@pytest.fixture
def table():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    tbl = build_sync_table("things", metadata)
    staging = build_staging_table("things", metadata)
    metadata.create_all(engine)
    return engine, tbl, staging


def current_rows(conn, table):
    return conn.execute(
        select(table).where(table.c._is_current.is_(True))
    ).mappings().all()


def test_first_pass_inserts_all_rows(table):
    engine, tbl, staging = table
    rows = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    with engine.begin() as conn:
        stats = apply_full_reconciliation(conn, tbl, staging, rows, ("id",))
        assert stats == {"fetched": 2, "inserted": 2, "updated": 0, "touched": 0, "soft_deleted": 0}
        assert len(current_rows(conn, tbl)) == 2


def test_second_pass_with_no_changes_only_touches(table):
    engine, tbl, staging = table
    rows = [{"id": 1, "name": "a"}]
    with engine.begin() as conn:
        apply_full_reconciliation(conn, tbl, staging, rows, ("id",))
    with engine.begin() as conn:
        stats = apply_full_reconciliation(conn, tbl, staging, rows, ("id",))
        assert stats == {"fetched": 1, "inserted": 0, "updated": 0, "touched": 1, "soft_deleted": 0}
        assert len(current_rows(conn, tbl)) == 1


def test_changed_row_closes_old_version_and_inserts_new(table):
    engine, tbl, staging = table
    with engine.begin() as conn:
        apply_full_reconciliation(conn, tbl, staging, [{"id": 1, "name": "a"}], ("id",))
    with engine.begin() as conn:
        stats = apply_full_reconciliation(conn, tbl, staging, [{"id": 1, "name": "b"}], ("id",))
        assert stats == {"fetched": 1, "inserted": 0, "updated": 1, "touched": 0, "soft_deleted": 0}

    with engine.begin() as conn:
        all_rows = conn.execute(select(tbl)).mappings().all()
        assert len(all_rows) == 2  # old closed version + new current version
        current = [r for r in all_rows if r["_is_current"]]
        closed = [r for r in all_rows if not r["_is_current"]]
        assert len(current) == 1
        assert current[0]["payload"]["name"] == "b"
        assert len(closed) == 1
        assert closed[0]["_valid_to"] is not None


def test_missing_row_is_closed_out_as_deletion(table):
    engine, tbl, staging = table
    with engine.begin() as conn:
        apply_full_reconciliation(conn, tbl, staging, [{"id": 1}, {"id": 2}], ("id",))
    with engine.begin() as conn:
        stats = apply_full_reconciliation(conn, tbl, staging, [{"id": 1}], ("id",))
        assert stats == {"fetched": 1, "inserted": 0, "updated": 0, "touched": 1, "soft_deleted": 1}
        current = current_rows(conn, tbl)
        assert len(current) == 1
        assert current[0]["_natural_key"] == "[1]"


def test_composite_natural_key(table):
    engine, tbl, staging = table
    rows = [{"ambito": "M", "id": 1}, {"ambito": "N", "id": 1}]
    with engine.begin() as conn:
        stats = apply_full_reconciliation(conn, tbl, staging, rows, ("ambito", "id"))
        assert stats["inserted"] == 2
        assert len(current_rows(conn, tbl)) == 2


def test_incremental_never_closes_out_absent_keys(table):
    """A reg-date window is a subset of the table, so absence isn't deletion."""
    engine, tbl, staging = table
    with engine.begin() as conn:
        apply_full_reconciliation(conn, tbl, staging, [{"id": 1}, {"id": 2}], ("id",))
    with engine.begin() as conn:
        stats = apply_incremental(conn, tbl, staging, [{"id": 1}], ("id",))
        assert stats == {"fetched": 1, "inserted": 0, "updated": 0, "touched": 1}
        assert len(current_rows(conn, tbl)) == 2  # id=2 untouched, not closed


def test_incremental_inserts_and_versions(table):
    engine, tbl, staging = table
    with engine.begin() as conn:
        stats = apply_incremental(conn, tbl, staging, [{"id": 1, "v": "a"}], ("id",))
        assert stats == {"fetched": 1, "inserted": 1, "updated": 0, "touched": 0}
    with engine.begin() as conn:
        stats = apply_incremental(conn, tbl, staging, [{"id": 1, "v": "b"}], ("id",))
        assert stats == {"fetched": 1, "inserted": 0, "updated": 1, "touched": 0}
        current = current_rows(conn, tbl)
        assert len(current) == 1
        assert current[0]["payload"]["v"] == "b"


def test_incremental_respects_chunk_size_across_batches(table):
    engine, tbl, staging = table
    rows = [{"id": i} for i in range(10)]
    with engine.begin() as conn:
        stats = apply_incremental(conn, tbl, staging, rows, ("id",), chunk_size=3)
        assert stats == {"fetched": 10, "inserted": 10, "updated": 0, "touched": 0}
        assert len(current_rows(conn, tbl)) == 10


# Window-scoped deletion detection.
#
# The core claim this design rests on: comparing a window's fetch against
# only the DB rows whose own registration date falls in that same window
# tells real deletions apart from rows that simply aged out of a rolling
# window. A plain "missing since last run's fetch" diff cannot do that,
# because every row ages out of its window eventually, regardless of
# deletion.


def test_window_scoped_deletion_closes_a_row_whose_reg_date_is_in_window(table):
    engine, tbl, staging = table
    start, end = date(2024, 1, 1), date(2024, 1, 31)
    row = {"id": 1, "fecha": "2024-01-15"}
    with engine.begin() as conn:
        apply_incremental(
            conn, tbl, staging, [row], ("id",),
            reg_date_field="fecha", window_start=start, window_end=end,
        )
    with engine.begin() as conn:
        stats = apply_incremental(
            conn, tbl, staging, [], ("id",),
            reg_date_field="fecha", window_start=start, window_end=end,
        )
        assert stats["soft_deleted"] == 1
        assert len(current_rows(conn, tbl)) == 0


def test_window_scoped_deletion_ignores_a_row_whose_reg_date_is_outside_window(table):
    """The row's own reg_date (2023-01-01) isn't inside the next run's
    window (2024), so missing from that run's batch says nothing about it:
    it was never in scope for that window to begin with. This is the aging
    case a naive window-vs-window diff would get wrong.
    """
    engine, tbl, staging = table
    row = {"id": 1, "fecha": "2023-01-01"}
    with engine.begin() as conn:
        apply_incremental(
            conn, tbl, staging, [row], ("id",),
            reg_date_field="fecha", window_start=date(2023, 1, 1), window_end=date(2023, 1, 1),
        )
    with engine.begin() as conn:
        stats = apply_incremental(
            conn, tbl, staging, [], ("id",),
            reg_date_field="fecha", window_start=date(2024, 1, 1), window_end=date(2024, 1, 31),
        )
        assert stats.get("soft_deleted", 0) == 0
        assert len(current_rows(conn, tbl)) == 1


def test_window_scoped_deletion_still_touches_and_versions_normally(table):
    """Window-scoped deletion only changes what happens to missing rows.
    Unchanged or changed rows already present in the batch still just touch
    or version as usual.
    """
    engine, tbl, staging = table
    start, end = date(2024, 1, 1), date(2024, 1, 31)
    with engine.begin() as conn:
        apply_incremental(
            conn, tbl, staging, [{"id": 1, "fecha": "2024-01-10", "v": "a"}], ("id",),
            reg_date_field="fecha", window_start=start, window_end=end,
        )
    with engine.begin() as conn:
        stats = apply_incremental(
            conn, tbl, staging, [{"id": 1, "fecha": "2024-01-10", "v": "b"}], ("id",),
            reg_date_field="fecha", window_start=start, window_end=end,
        )
        assert stats["updated"] == 1
        assert stats.get("soft_deleted", 0) == 0
        current = current_rows(conn, tbl)
        assert len(current) == 1
        assert current[0]["payload"]["v"] == "b"


def test_apply_incremental_without_reg_date_field_is_unchanged(table):
    """Default behavior (no opt-in) must stay exactly as before: no
    `reg_date_field` means no `soft_deleted` key at all, nothing gets closed.
    """
    engine, tbl, staging = table
    with engine.begin() as conn:
        apply_incremental(conn, tbl, staging, [{"id": 1}, {"id": 2}], ("id",))
    with engine.begin() as conn:
        stats = apply_incremental(conn, tbl, staging, [{"id": 1}], ("id",))
        assert "soft_deleted" not in stats
        assert len(current_rows(conn, tbl)) == 2
