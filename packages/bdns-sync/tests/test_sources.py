"""How each kind of row source fetches, exercised through sync_entity."""

from datetime import date, timedelta

from sqlalchemy import MetaData, create_engine, select

from bdns.fetch.dates import period_range, registration_range
from bdns.sync.entities import (
    Entity,
    catalog,
    period_window,
    registration_window,
    swept,
    sync_entity,
)
from bdns.sync.sinks import SyncStats
from bdns.sync.sinks.sql import SQLSink
from bdns.sync.sinks.sql.schema import build_control_tables, build_sync_table
from tests.fake_client import FakeBDNSClient, reg_date


def current_rows(engine, name):
    table = build_sync_table(name, MetaData())
    with engine.begin() as conn:
        return conn.execute(select(table).where(table.c._is_current.is_(True))).mappings().all()


# --- full: one call -----------------------------------------------------------


class FakeFullClient:
    def __init__(self, rows):
        self._rows = rows

    def fetch_widgets(self):
        yield from self._rows


WIDGETS = Entity("widgets", "full", ("id",), catalog("fetch_widgets"))


def test_full_catalog_writes_rows_and_run_log():
    engine = create_engine("sqlite:///:memory:")
    client = FakeFullClient([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}])

    stats = sync_entity(WIDGETS, SQLSink(engine), client)
    assert stats == SyncStats(fetched=2, new=2)

    sync_state, sync_runs, _ = build_control_tables(MetaData())
    with engine.begin() as conn:
        assert len(current_rows(engine, "widgets")) == 2
        state_row = (
            conn.execute(select(sync_state).where(sync_state.c.table_name == "widgets"))
            .mappings()
            .one()
        )
        # append-only event log: exactly one started + one success event
        events = conn.execute(select(sync_runs).order_by(sync_runs.c.occurred_at)).mappings().all()
        assert [e["event"] for e in events] == ["started", "success"]
        assert events[1]["rows_inserted"] == 2
        assert state_row["last_run_id"] == events[1]["run_id"] == events[0]["run_id"]


def test_full_catalog_second_run_detects_deletion():
    engine = create_engine("sqlite:///:memory:")
    client = FakeFullClient([{"id": 1}, {"id": 2}])
    sync_entity(WIDGETS, SQLSink(engine), client)

    client._rows = [{"id": 1}]
    stats = sync_entity(WIDGETS, SQLSink(engine), client)
    assert stats.removed == 1
    assert len(current_rows(engine, "widgets")) == 1


# --- full: swept across a parameter -------------------------------------------


class FakeSweptClient:
    def __init__(self, by_value):
        self._by_value = by_value

    def fetch_widgets(self, region):
        yield from self._by_value.get(region, [])


SWEPT = Entity(
    "widgets", "full", ("region", "id"), swept("fetch_widgets", "region", ("X", "Y", "Z"))
)


def test_swept_catalog_merges_sweep_values_and_tags_payload():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSweptClient(by_value={"X": [{"id": 1}], "Y": [{"id": 1}], "Z": []})

    stats = sync_entity(SWEPT, SQLSink(engine), client)
    assert stats.new == 2  # (X,1) and (Y,1) are distinct records

    rows = current_rows(engine, "widgets")
    assert {r["_natural_key"] for r in rows} == {'["X",1]', '["Y",1]'}
    assert {r["payload"]["region"] for r in rows} == {"X", "Y"}


def test_swept_catalog_does_not_close_other_sweep_values_as_missing():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSweptClient(by_value={"X": [{"id": 1}], "Y": [{"id": 2}], "Z": []})
    sync_entity(SWEPT, SQLSink(engine), client)

    client._by_value["X"] = [{"id": 1, "v": "changed"}]
    stats = sync_entity(SWEPT, SQLSink(engine), client)
    assert stats.removed == 0
    assert len(current_rows(engine, "widgets")) == 2


# --- windowed: by registration date or by period -----------------------------


class FakeSearchClient:
    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def fetch_widgets_busqueda(self, **kwargs):
        self.calls.append(kwargs)
        yield from self._rows


BY_REGISTRATION = Entity(
    "widgets_busqueda", "windowed", ("id",), registration_window("fetch_widgets_busqueda")
)
BY_PERIOD = Entity("widgets_busqueda", "windowed", ("id",), period_window("fetch_widgets_busqueda"))


def test_windowed_run_without_reg_date_field_never_closes_absent_keys():
    engine = create_engine("sqlite:///:memory:")
    client = FakeSearchClient([{"id": 1}, {"id": 2}])
    day = date(2024, 1, 1)
    sync_entity(BY_REGISTRATION, SQLSink(engine), client, since=day, until=day)

    client._rows = [{"id": 1}]
    stats = sync_entity(BY_REGISTRATION, SQLSink(engine), client, since=day, until=day)
    assert stats == SyncStats(fetched=1, unchanged=1)
    assert client.calls[-1] == registration_range(day, day)  # exclusive bound: day + 1
    assert len(current_rows(engine, "widgets_busqueda")) == 2


def test_registration_window_chunks_a_multi_week_span_by_7_days():
    client = FakeSearchClient([])
    start, end = date(2020, 1, 1), date(2020, 1, 31)  # 31 days -> 5 weekly chunks
    sync_entity(
        BY_REGISTRATION, SQLSink(create_engine("sqlite://")), client, since=start, until=end
    )

    assert len(client.calls) == 5
    assert client.calls[0]["fechaRegInicio"] == start
    assert client.calls[-1]["fechaRegFin"] == end + timedelta(days=1)
    for call in client.calls:
        assert (call["fechaRegFin"] - call["fechaRegInicio"]).days <= 7


def test_period_window_sends_the_inclusive_bound_as_is():
    client = FakeSearchClient([])
    day = date(2024, 1, 1)
    sync_entity(BY_PERIOD, SQLSink(create_engine("sqlite://")), client, since=day, until=day)
    assert client.calls == [period_range(day, day)]


def test_windowed_run_records_its_range_in_the_run_log():
    engine = create_engine("sqlite:///:memory:")
    start, end = date(2024, 1, 1), date(2024, 1, 9)
    sync_entity(BY_REGISTRATION, SQLSink(engine), FakeSearchClient([]), since=start, until=end)
    _, sync_runs, _ = build_control_tables(MetaData())
    with engine.begin() as conn:
        events = conn.execute(select(sync_runs)).mappings().all()
    assert {(e["window_start"], e["window_end"]) for e in events} == {(start, end)}


# --- adjacent days through the real date helpers --------------------------------


def test_adjacent_single_days_are_disjoint_and_their_union_is_the_two_day_range():
    """Two adjacent days, fetched through the same helpers production uses,
    are disjoint and add up to the two-day range, for both date families.
    The live API is checked for the same property by `bdns-fetch check-api`.
    """
    client = FakeBDNSClient()
    day_a, day_b = reg_date(11), reg_date(10)
    assert day_b == day_a + timedelta(days=1)

    cases = [
        (client.fetch_concesiones_busqueda, "id", client.concesiones_busqueda),
        (client.fetch_ayudasestado_busqueda, "idConcesion", client.ayudasestado_busqueda),
        (client.fetch_minimis_busqueda, "idConcesion", client.minimis_busqueda),
        (client.fetch_partidospoliticos_busqueda, "id", client.partidospoliticos_busqueda),
    ]
    for fetch, key, records in cases:
        records.clear()
        records.append({"reg_days_ago": 11, "payload": {key: 1}})
        records.append({"reg_days_ago": 10, "payload": {key: 2}})

        def ids(first, last, fetch=fetch, key=key):
            return {row[key] for row in fetch(**registration_range(first, last))}

        a, b, both = ids(day_a, day_a), ids(day_b, day_b), ids(day_a, day_b)
        assert a == {1} and b == {2}
        assert a & b == set()
        assert a | b == both

    client.convocatorias_busqueda = [
        {"reg_days_ago": 11, "payload": {"numeroConvocatoria": "C-A"}},
        {"reg_days_ago": 10, "payload": {"numeroConvocatoria": "C-B"}},
    ]

    def codes(first, last):
        return {
            r["numeroConvocatoria"]
            for r in client.fetch_convocatorias_busqueda(**period_range(first, last))
        }

    a, b, both = codes(day_a, day_a), codes(day_b, day_b), codes(day_a, day_b)
    assert a == {"C-A"} and b == {"C-B"}
    assert a & b == set()
    assert a | b == both
