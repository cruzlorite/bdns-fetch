"""Multi-day scenarios for `convocatorias`: discover codes in a reg-date
window, then one real detail call per discovered code (per the official
doc: "aqui cada Convocatoria te costara una llamada"). Same cascade
semantics as the other incremental entities, plus the two things unique to
this shape: exactly one detail call per discovered code, and malformed
detail responses must be skipped rather than crash the run.
"""

from copy import deepcopy
from datetime import timedelta

from sqlalchemy import create_engine

from bdns.sync.generic import CHUNK_DAYS
from bdns.sync.sinks.sql import SQLSink
from bdns.sync.syncers import sync_convocatorias
from tests.fake_client import FakeBDNSClient
from tests.timeline_helpers import current_rows, last_sync_run, sync_errors_for


def test_convocatorias_cascade_progressively_reveals_older_registrations():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()

    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats["inserted"] == 1  # only reg_days_ago=0 -> code 927266
    assert client.calls_to("fetch_convocatorias") == [{"numConv": "927266"}]

    stats = sync_convocatorias(SQLSink(engine), client, "weekly")
    assert stats["inserted"] == 1  # code 927267 (reg_days_ago=5) newly in range
    assert stats["touched"] == 1  # code 927266 re-discovered, unchanged
    assert len(current_rows(engine, "convocatorias")) == 2

    stats = sync_convocatorias(SQLSink(engine), client, "monthly")
    assert stats["inserted"] == 1  # code 927268 (reg_days_ago=20)
    assert stats["touched"] == 2
    assert len(current_rows(engine, "convocatorias")) == 3


def test_convocatorias_discovery_is_chunked_for_wide_windows():
    """`monthly` (30 days) discovery must be split into <=CHUNK_DAYS-wide,
    contiguous pieces. A single 30-day call is exactly the range that
    proved unreliable against the real API (see README "Limitaciones
    conocidas").
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "monthly")

    # convocatorias' fechaHasta is INCLUSIVE, so a chunk spanning days [s, e]
    # is sent as (s, e) directly, with no +1, unlike the fechaRegFin endpoints
    calls = sorted(client.calls_to("fetch_convocatorias_busqueda"), key=lambda c: c["start"])
    assert len(calls) > 1
    for call in calls:
        assert (call["end"] - call["start"]).days < CHUNK_DAYS
    for prev, nxt in zip(calls, calls[1:]):
        assert nxt["start"] == prev["end"] + timedelta(days=1)


def test_convocatorias_one_detail_call_per_discovered_code():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "monthly")
    calls = client.calls_to("fetch_convocatorias")
    assert sorted(c["numConv"] for c in calls) == ["927266", "927267", "927268"]


def test_convocatorias_detail_rewrite_produces_new_version():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "weekly")

    client.convocatorias_detail["927267"]["presupuestoTotal"] = 999999
    stats = sync_convocatorias(SQLSink(engine), client, "weekly")
    assert stats["updated"] == 1
    assert stats["touched"] == 1  # 927266 unchanged

    current = current_rows(engine, "convocatorias")
    rewritten = next(r for r in current if r["_natural_key"] == '["927267"]')
    assert rewritten["payload"]["presupuestoTotal"] == 999999


def test_convocatorias_malformed_detail_is_skipped_not_crashed():
    """Live-confirmed failure mode: BDNS occasionally returns an HTML error
    page instead of JSON for one specific record. That code's detail must
    be skipped, not blow up the whole run.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    client.convocatorias_detail["927266"] = "<html>not json</html>"

    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats["fetched"] == 0  # the only discovered code was malformed
    assert stats["inserted"] == 0
    assert len(current_rows(engine, "convocatorias")) == 0

    # the skip is durable, not just a transient log line
    assert last_sync_run(engine, "convocatorias")["rows_skipped"] == 1
    [error] = sync_errors_for(engine, "convocatorias")
    assert error["context"] == "convocatorias numConv=927266"
    assert error["content"] == "<html>not json</html>"


def test_convocatorias_detects_a_real_deletion_within_the_current_window():
    """`fechaRecepcion` (the detail record's own registration date, confirmed
    live) is inside daily's [yesterday, yesterday] range for the
    reg_days_ago=0 code. So if it's genuinely missing from today's
    discovery, that's a real deletion and must be closed.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "daily")
    before = len(current_rows(engine, "convocatorias"))

    client.convocatorias_busqueda = [
        rec for rec in client.convocatorias_busqueda if rec["reg_days_ago"] != 0
    ]
    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, "convocatorias")) == before - 1


def test_convocatorias_ignores_codes_outside_the_current_window():
    """The reg_days_ago=20 code's own fechaRecepcion isn't inside daily's
    range, so missing from today's daily discovery says nothing about it.
    It must not be closed; this is the aging-vs-deletion distinction.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "monthly")  # seeds reg_days_ago 0, 5, 20
    before = len(current_rows(engine, "convocatorias"))

    client.convocatorias_busqueda = [
        rec for rec in client.convocatorias_busqueda if rec["reg_days_ago"] != 20
    ]
    stats = sync_convocatorias(SQLSink(engine), client, "daily")  # only covers reg_days_ago=0
    assert stats.get("soft_deleted", 0) == 0
    assert len(current_rows(engine, "convocatorias")) == before


def test_convocatorias_new_registration_caught_by_daily():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_convocatorias(SQLSink(engine), client, "daily")

    new_discovery = deepcopy(client.convocatorias_busqueda[0])
    new_discovery["payload"] = dict(new_discovery["payload"], numeroConvocatoria="927270")
    client.convocatorias_busqueda.append(new_discovery)
    client.convocatorias_detail["927270"] = dict(
        client.convocatorias_detail["927266"], codigoBDNS="927270"
    )

    stats = sync_convocatorias(SQLSink(engine), client, "daily")
    assert stats["inserted"] == 1
