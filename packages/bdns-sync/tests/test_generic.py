from datetime import date, timedelta

import pytest
from sqlalchemy import MetaData, create_engine, select

from bdns.sync.generic import (
    iter_date_chunks,
    resolve_when,
    sync_full_catalog,
    sync_search_range,
    sync_swept_catalog,
    to_api_upper_bound,
    window_bounds,
)
from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.schema import build_control_tables, build_sync_table
from tests.fake_client import FakeBDNSClient, reg_date


def current_rows(engine, name):
    metadata = MetaData()
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(table).where(table.c._is_current.is_(True))
        ).mappings().all()


# --- iter_date_chunks -------------------------------------------------------


def test_iter_date_chunks_splits_a_long_range_into_7_day_pieces():
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)  # 31 days: 4 full weeks + a 3-day remainder
    chunks = list(iter_date_chunks(start, end, chunk_days=7))

    assert chunks == [
        (date(2024, 1, 1), date(2024, 1, 7)),
        (date(2024, 1, 8), date(2024, 1, 14)),
        (date(2024, 1, 15), date(2024, 1, 21)),
        (date(2024, 1, 22), date(2024, 1, 28)),
        (date(2024, 1, 29), date(2024, 1, 31)),
    ]


def test_iter_date_chunks_single_day_range_is_one_chunk():
    d = date(2024, 1, 1)
    assert list(iter_date_chunks(d, d, chunk_days=7)) == [(d, d)]


def test_iter_date_chunks_range_shorter_than_chunk_size_is_one_chunk():
    start, end = date(2024, 1, 1), date(2024, 1, 5)
    assert list(iter_date_chunks(start, end, chunk_days=7)) == [(start, end)]


def test_iter_date_chunks_range_exactly_one_chunk_wide():
    start, end = date(2024, 1, 1), date(2024, 1, 7)
    assert list(iter_date_chunks(start, end, chunk_days=7)) == [(start, end)]


def test_iter_date_chunks_are_contiguous_with_no_gaps_or_overlaps():
    start, end = date(2024, 1, 1), date(2024, 3, 1)
    chunks = list(iter_date_chunks(start, end, chunk_days=7))

    assert chunks[0][0] == start
    assert chunks[-1][1] == end
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:]):
        assert next_start == prev_end + timedelta(days=1)
    for chunk_start, chunk_end in chunks:
        assert (chunk_end - chunk_start).days < 7


# --- to_api_upper_bound + chunk coverage ------------------------------------


def test_to_api_upper_bound_is_the_day_after():
    assert to_api_upper_bound(date(2024, 1, 15)) == date(2024, 1, 16)


def test_chunked_api_intervals_tile_the_range_exactly_regardless_of_chunk_size():
    """The regression this locks in: the API's upper bound is exclusive, so a
    bare `fechaRegFin=chunk_end` drops each chunk's last day, and more chunks
    meant more lost days (a 28-day range fetched in 1-day chunks returned 8
    rows instead of 1.2M, confirmed live). Routing every chunk end through
    `to_api_upper_bound` makes the half-open intervals
    [chunk_start, to_api_upper_bound(chunk_end)) tile the full inclusive
    range exactly once (every day covered, no gaps, no overlaps) for any
    chunk size. That's what makes row totals independent of how the range was
    split.
    """
    start, end = date(2024, 1, 1), date(2024, 3, 31)  # 91 inclusive days
    expected_days = {start + timedelta(days=i) for i in range((end - start).days + 1)}

    for chunk_days in (1, 2, 7, 14, 30, 91, 200):
        covered = []
        for chunk_start, chunk_end in iter_date_chunks(start, end, chunk_days=chunk_days):
            day = chunk_start
            while day < to_api_upper_bound(chunk_end):  # exclusive upper bound
                covered.append(day)
                day += timedelta(days=1)
        # set equality proves no gaps; equal length proves no overlaps/dupes
        assert set(covered) == expected_days
        assert len(covered) == len(expected_days)


# --- belt-and-suspenders: adjacent days are disjoint and additive ----------


def _reg_fam_ids(fetch, key, day_lo, day_hi):
    """Fetch natural keys for [day_lo, day_hi] the way production does for the
    four fechaRegFin endpoints: upper bound is exclusive, so +1 via the bridge.
    """
    return {row[key] for row in fetch(fechaRegInicio=day_lo, fechaRegFin=to_api_upper_bound(day_hi))}


def _convo_codes(client, day_lo, day_hi):
    """Fetch codes the way production does for convocatorias discovery:
    fechaHasta is inclusive, so NO +1.
    """
    return {r["numeroConvocatoria"] for r in client.fetch_convocatorias_busqueda(fechaDesde=day_lo, fechaHasta=day_hi)}


def test_adjacent_single_days_are_disjoint_and_their_union_is_the_two_day_range():
    """Belt-and-suspenders mirroring the live check across all 5 endpoints.
    For two adjacent single days X and X+1, fetched through the exact
    per-family bridge production uses, prove both invariants at once:

    - no overlap:  fetch(X) & fetch(X+1) == empty  (proves we don't over-fetch;
      an off-by-one on the exclusive endpoints, or a wrong bound on the
      inclusive one, would double-count the boundary day here)
    - no gap:      fetch(X) | fetch(X+1) == fetch([X, X+1])  (proves we don't
      under-fetch; a dropped boundary day would break this)

    Confirmed live with real data (concesiones: 115,862 + 68,457 = 184,319,
    overlap 0); this locks the same property in against future regressions.
    `dayA` and `dayB` are adjacent calendar days (dayB is one day after dayA).
    """
    client = FakeBDNSClient()
    dayA, dayB = reg_date(11), reg_date(10)  # reg_date(10) is one day after reg_date(11)
    assert dayB == dayA + timedelta(days=1)

    # four fechaRegFin endpoints (exclusive upper bound, +1 bridge)
    reg_cases = [
        (client.fetch_concesiones_busqueda, "id", client.concesiones_busqueda),
        (client.fetch_ayudasestado_busqueda, "idConcesion", client.ayudasestado_busqueda),
        (client.fetch_minimis_busqueda, "idConcesion", client.minimis_busqueda),
        (client.fetch_partidospoliticos_busqueda, "id", client.partidospoliticos_busqueda),
    ]
    for fetch, key, records in reg_cases:
        records.clear()
        records.append({"reg_days_ago": 11, "payload": {key: 1}})
        records.append({"reg_days_ago": 10, "payload": {key: 2}})

        a = _reg_fam_ids(fetch, key, dayA, dayA)
        b = _reg_fam_ids(fetch, key, dayB, dayB)
        both = _reg_fam_ids(fetch, key, dayA, dayB)
        assert a == {1} and b == {2}
        assert a & b == set()  # disjoint, no overlap
        assert a | b == both  # additive, no gap

    # convocatorias discovery (inclusive fechaHasta, no +1)
    client.convocatorias_busqueda = [
        {"reg_days_ago": 11, "payload": {"numeroConvocatoria": "C-A"}},
        {"reg_days_ago": 10, "payload": {"numeroConvocatoria": "C-B"}},
    ]
    a = _convo_codes(client, dayA, dayA)
    b = _convo_codes(client, dayB, dayB)
    both = _convo_codes(client, dayA, dayB)
    assert a == {"C-A"} and b == {"C-B"}
    assert a & b == set()
    assert a | b == both


# --- sync_full_catalog ----------------------------------------------------


class FakeFullClient:
    def __init__(self, rows):
        self._rows = rows

    def fetch_widgets(self):
        yield from self._rows


def test_full_catalog_writes_rows_and_run_log():
    engine = create_engine("sqlite:///:memory:")
    client = FakeFullClient([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}])

    stats = sync_full_catalog(SQLSink(engine), client, "widgets", "fetch_widgets", ("id",))
    assert stats == {"fetched": 2, "inserted": 2, "updated": 0, "touched": 0, "soft_deleted": 0}

    metadata = MetaData()
    sync_state, sync_runs, _ = build_control_tables(metadata)
    with engine.begin() as conn:
        assert len(current_rows(engine, "widgets")) == 2
        state_row = conn.execute(
            select(sync_state).where(sync_state.c.table_name == "widgets")
        ).mappings().one()
        # append-only event log: exactly one started + one success event
        events = conn.execute(
            select(sync_runs).order_by(sync_runs.c.occurred_at)
        ).mappings().all()
        assert [e["event"] for e in events] == ["started", "success"]
        assert events[1]["rows_inserted"] == 2
        # run_id is app-generated (epoch microseconds), not autoincrement;
        # the watermark must point at the run that was just logged.
        assert state_row["last_run_id"] == events[1]["run_id"] == events[0]["run_id"]


def test_full_catalog_second_run_detects_deletion():
    engine = create_engine("sqlite:///:memory:")
    client = FakeFullClient([{"id": 1}, {"id": 2}])
    sync_full_catalog(SQLSink(engine), client, "widgets", "fetch_widgets", ("id",))

    client._rows = [{"id": 1}]
    stats = sync_full_catalog(SQLSink(engine), client, "widgets", "fetch_widgets", ("id",))
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, "widgets")) == 1


# --- sync_swept_catalog ----------------------------------------------------


class FakeSweptClient:
    def __init__(self, by_value):
        self._by_value = by_value

    def fetch_widgets(self, region):
        yield from self._by_value.get(region, [])


def test_swept_catalog_merges_sweep_values_and_tags_payload():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSweptClient(by_value={"X": [{"id": 1}], "Y": [{"id": 1}], "Z": []})

    stats = sync_swept_catalog(
        SQLSink(engine), client, "widgets", "fetch_widgets", "region", ("X", "Y", "Z"), ("region", "id")
    )
    assert stats["inserted"] == 2  # (X,1) and (Y,1) are distinct entities

    rows = current_rows(engine, "widgets")
    assert {r["_natural_key"] for r in rows} == {'["X",1]', '["Y",1]'}
    payloads = {r["payload"]["region"] for r in rows}
    assert payloads == {"X", "Y"}


def test_swept_catalog_does_not_close_other_sweep_values_as_missing():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSweptClient(by_value={"X": [{"id": 1}], "Y": [{"id": 2}], "Z": []})
    sync_swept_catalog(
        SQLSink(engine), client, "widgets", "fetch_widgets", "region", ("X", "Y", "Z"), ("region", "id")
    )

    client._by_value["X"] = [{"id": 1, "v": "changed"}]
    stats = sync_swept_catalog(
        SQLSink(engine), client, "widgets", "fetch_widgets", "region", ("X", "Y", "Z"), ("region", "id")
    )
    assert stats["soft_deleted"] == 0
    assert len(current_rows(engine, "widgets")) == 2


# --- window_bounds / resolve_when ------------------------------------------


def test_window_bounds_span_the_declared_days_ending_yesterday():
    yesterday = date.today() - timedelta(days=1)
    assert window_bounds("daily") == (yesterday, yesterday)
    assert window_bounds("weekly") == (yesterday - timedelta(days=6), yesterday)
    assert window_bounds("annual") == (yesterday - timedelta(days=364), yesterday)


def test_window_bounds_rejects_unknown_window():
    with pytest.raises(KeyError):
        window_bounds("bogus")


def test_resolve_when_from_window_name():
    yesterday = date.today() - timedelta(days=1)
    assert resolve_when("daily", None, None) == (yesterday, yesterday, "daily")


def test_resolve_when_since_overrides_window_and_defaults_until_to_yesterday():
    yesterday = date.today() - timedelta(days=1)
    start, end, run_type = resolve_when("daily", date(2020, 1, 1), None)
    assert (start, end, run_type) == (date(2020, 1, 1), yesterday, "backfill")


def test_resolve_when_explicit_since_and_until():
    assert resolve_when(None, date(2020, 1, 1), date(2020, 6, 30)) == (
        date(2020, 1, 1),
        date(2020, 6, 30),
        "backfill",
    )


def test_resolve_when_needs_window_or_since():
    with pytest.raises(ValueError):
        resolve_when(None, None, None)


# --- sync_search_range ------------------------------------------------------


class FakeSearchClient:
    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def fetch_widgets_busqueda(self, fechaRegInicio=None, fechaRegFin=None):
        self.calls.append((fechaRegInicio, fechaRegFin))
        self.last_window = (fechaRegInicio, fechaRegFin)
        yield from self._rows


def test_search_range_incremental_no_deletion_detection():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSearchClient([{"id": 1}, {"id": 2}])
    start, end = date(2024, 1, 1), date(2024, 1, 1)
    sync_search_range(
        SQLSink(engine), client, "widgets_busqueda", "fetch_widgets_busqueda", ("id",), start, end, "daily"
    )

    client._rows = [{"id": 1}]
    stats = sync_search_range(
        SQLSink(engine), client, "widgets_busqueda", "fetch_widgets_busqueda", ("id",), start, end, "daily"
    )
    assert stats == {"fetched": 1, "inserted": 0, "updated": 0, "touched": 1}

    # single-day range, upper bound sent exclusive (start + 1)
    assert client.last_window == (start, end + timedelta(days=1))
    assert len(current_rows(engine, "widgets_busqueda")) == 2  # id=2 not closed


def test_search_range_backfill_chunks_a_multi_week_span_by_7_days():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSearchClient([])
    start, end = date(2020, 1, 1), date(2020, 1, 31)  # 31 days -> 5 weekly chunks
    sync_search_range(
        SQLSink(engine), client, "widgets_busqueda", "fetch_widgets_busqueda", ("id",), start, end, "backfill"
    )

    calls = sorted(client.calls)
    assert len(calls) == 5
    assert calls[0][0] == start
    assert calls[-1][1] == end + timedelta(days=1)  # last exclusive upper bound
    for lo, hi in calls:
        assert (hi - lo).days <= 7  # each chunk at most a week (exclusive end)
