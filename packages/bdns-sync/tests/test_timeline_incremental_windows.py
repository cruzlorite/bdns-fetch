"""Multi-day scenarios for the reg-date incremental "big search" endpoints:
concesiones_busqueda, ayudasestado_busqueda, minimis_busqueda, and
partidospoliticos_busqueda. Runs through every cascade window
(daily/weekly/monthly/annual).

The interesting behavior here isn't insert/touch/rewrite in isolation,
which is covered generically in test_scd2.py. It's the cascade: daily only
looks at yesterday, so a correction to a record registered 20 days ago is
invisible to daily and weekly, and only a monthly (or annual) pass catches
it. That's the whole reason the official BDNS guidance recommends running
all four cadences instead of just daily, and it's what these tests prove
end to end against real-shaped payloads.

It's also where window-scoped deletion detection is exercised end to end
(the unit-level proof lives in test_scd2.py). concesiones_busqueda,
ayudasestado_busqueda, and minimis_busqueda each expose their own
registration-date field in the payload, confirmed live against the real
API, so they detect a real deletion the moment it falls inside the
currently-run window. partidospoliticos_busqueda doesn't expose that field
(also confirmed live, despite the official doc claiming otherwise), so it
never detects deletions, same as before this feature existed.

Each fixture record carries `reg_days_ago` (see tests/fake_client.py):
0 means inside daily; 5 means inside weekly but outside daily; 20 means
inside monthly but outside weekly; 100 means inside annual but outside
monthly.
"""

from copy import deepcopy
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine

from bdns.sync.generic import CHUNK_DAYS, WINDOWS
from bdns.sync.sinks.sql import SQLSink
from bdns.sync.syncers import SEARCH_SYNCERS
from tests.fake_client import FakeBDNSClient
from tests.timeline_helpers import current_rows

# (endpoint name, key fields). The endpoint name doubles as the fixture
# file name, the client attribute, and the sync table name.
INCREMENTAL_CASES = [
    ("concesiones_busqueda", ("id",)),
    ("ayudasestado_busqueda", ("idConcesion",)),
    ("minimis_busqueda", ("idConcesion",)),
    ("partidospoliticos_busqueda", ("id",)),
    ("convocatorias_busqueda", ("numeroConvocatoria",)),
]

CASE_IDS = [name for name, _ in INCREMENTAL_CASES]

# Only these expose their own registration-date field in the payload, so
# window-scoped deletion detection is only possible for them.
SCOPED_DELETION_CASES = [
    ("concesiones_busqueda", ("id",)),
    ("ayudasestado_busqueda", ("idConcesion",)),
    ("minimis_busqueda", ("idConcesion",)),
    ("convocatorias_busqueda", ("numeroConvocatoria",)),
]
SCOPED_CASE_IDS = [name for name, _ in SCOPED_DELETION_CASES]


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
def test_cascade_progressively_reveals_older_registrations(endpoint, key_fields):
    """Running daily->weekly->monthly->annual in sequence (same as a real
    day's cron dispatch) picks up one more reg_days_ago tier each time.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]

    stats = sync_fn(SQLSink(engine), client, "daily")
    assert stats["inserted"] == 1  # only reg_days_ago=0
    assert len(current_rows(engine, endpoint)) == 1

    stats = sync_fn(SQLSink(engine), client, "weekly")
    assert stats["inserted"] == 1  # reg_days_ago=5 newly in range
    assert stats["touched"] == 1  # reg_days_ago=0 re-seen, unchanged
    assert len(current_rows(engine, endpoint)) == 2

    stats = sync_fn(SQLSink(engine), client, "monthly")
    assert stats["inserted"] == 1  # reg_days_ago=20
    assert stats["touched"] == 2
    assert len(current_rows(engine, endpoint)) == 3

    stats = sync_fn(SQLSink(engine), client, "annual")
    assert stats["inserted"] == 1  # reg_days_ago=100
    assert stats["touched"] == 3
    assert len(current_rows(engine, endpoint)) == 4


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
def test_daily_and_weekly_miss_a_correction_only_monthly_catches(endpoint, key_fields):
    """A record registered 20 days ago gets corrected upstream. Daily
    (window=1) and weekly (window=7) never look far back enough to see it;
    monthly (window=30) does. This is the cascade's whole reason to exist.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]

    # seed the table with all four tiers first (one full cascade)
    for window in ("daily", "weekly", "monthly", "annual"):
        sync_fn(SQLSink(engine), client, window)
    assert len(current_rows(engine, endpoint)) == 4

    # upstream corrects the reg_days_ago=20 record (mutate a non-key field)
    records = getattr(client, endpoint)
    target = next(r for r in records if r["reg_days_ago"] == 20)
    payload_field = next(k for k in target["payload"] if k not in key_fields and isinstance(target["payload"][k], str))
    target["payload"][payload_field] = "__CORRECTED__"

    stats = sync_fn(SQLSink(engine), client, "daily")
    assert stats.get("updated", 0) == 0  # correction is 20 days back, daily can't see it

    stats = sync_fn(SQLSink(engine), client, "weekly")
    assert stats.get("updated", 0) == 0  # still can't see it, 20 > 7

    stats = sync_fn(SQLSink(engine), client, "monthly")
    assert stats["updated"] == 1  # 20 <= 30, caught

    current = current_rows(engine, endpoint)
    updated_row = next(r for r in current if r["payload"].get(payload_field) == "__CORRECTED__")
    assert updated_row is not None


def test_partidospoliticos_never_reports_or_applies_deletions():
    """No registration-date field in this payload (confirmed live) -> no
    window-scoped deletion detection possible. A record missing from a
    window's fetch is never closed, same as before this feature existed.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS["partidospoliticos_busqueda"]
    for window in ("daily", "weekly", "monthly", "annual"):
        sync_fn(SQLSink(engine), client, window)
    before = len(current_rows(engine, "partidospoliticos_busqueda"))

    records = client.partidospoliticos_busqueda
    records.remove(next(r for r in records if r["reg_days_ago"] == 0))

    stats = sync_fn(SQLSink(engine), client, "daily")
    assert "soft_deleted" not in stats
    assert len(current_rows(engine, "partidospoliticos_busqueda")) == before


@pytest.mark.parametrize("endpoint,key_fields", SCOPED_DELETION_CASES, ids=SCOPED_CASE_IDS)
def test_scoped_entities_detect_a_real_deletion_within_the_current_window(endpoint, key_fields):
    """`fechaAlta`/`fechaRegistro` (the payload's own registration date) is
    inside `[window_start, window_end]` for the reg_days_ago=0 record on
    every daily run. So if it's genuinely missing from today's fetch, that's
    a real deletion, not aging, and must be closed.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]
    sync_fn(SQLSink(engine), client, "daily")
    before = len(current_rows(engine, endpoint))

    records = getattr(client, endpoint)
    records.remove(next(r for r in records if r["reg_days_ago"] == 0))

    stats = sync_fn(SQLSink(engine), client, "daily")
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, endpoint)) == before - 1


@pytest.mark.parametrize("endpoint,key_fields", SCOPED_DELETION_CASES, ids=SCOPED_CASE_IDS)
def test_scoped_entities_ignore_records_outside_the_current_window(endpoint, key_fields):
    """The reg_days_ago=20 record's own registration date isn't inside
    daily's [yesterday, yesterday] range. So even though it's genuinely
    missing from today's daily fetch, it was never in scope to begin with,
    and window-scoped deletion must leave it alone. This is the case a
    naive "missing from this run's fetch" diff would have gotten wrong.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]
    sync_fn(SQLSink(engine), client, "monthly")  # seeds reg_days_ago 0, 5, 20
    before = len(current_rows(engine, endpoint))

    records = getattr(client, endpoint)
    records.remove(next(r for r in records if r["reg_days_ago"] == 20))

    stats = sync_fn(SQLSink(engine), client, "daily")  # only covers reg_days_ago=0
    assert stats.get("soft_deleted", 0) == 0
    assert len(current_rows(engine, endpoint)) == before


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
def test_new_registration_is_caught_by_the_next_daily_run(endpoint, key_fields):
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]
    sync_fn(SQLSink(engine), client, "daily")

    records = getattr(client, endpoint)
    new_record = deepcopy(next(r for r in records if r["reg_days_ago"] == 0))
    for field in key_fields:
        new_record["payload"][field] = (
            new_record["payload"][field] + 999000
            if isinstance(new_record["payload"][field], int)
            else f"{new_record['payload'][field]}-NEW"
        )
    records.append(new_record)

    stats = sync_fn(SQLSink(engine), client, "daily")
    assert stats["inserted"] == 1


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
@pytest.mark.parametrize("window,days", list(WINDOWS.items()))
def test_window_date_bounds_match_the_declared_cadence(endpoint, key_fields, window, days):
    """`--window daily/weekly/monthly/annual` must translate into the exact
    reg-date range the README documents: ending yesterday, spanning `days`
    days back. This is the "does the CLI option actually change API request
    behavior" check.

    The fetch is chunked into `CHUNK_DAYS`-wide pieces (see generic.py), so
    for `monthly`/`annual` this is several calls, not one. For the four
    `fechaRegFin` endpoints, each call's `end` in the log is the API's
    *exclusive* upper bound (inclusive chunk end + 1, see
    `to_api_upper_bound`), so a chunk covering days [s, e] is recorded as
    (s, e + 1). `convocatorias_busqueda` is the opposite family
    (`fechaHasta`, inclusive, see `sync_search_range_inclusive`): its `end`
    is recorded as the inclusive chunk end itself, with no +1. What matters
    either way: chunks are contiguous, none spans more than `CHUNK_DAYS`
    days, and together they cover exactly the documented range.
    """
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]
    sync_fn(SQLSink(engine), client, window)

    inclusive = endpoint == "convocatorias_busqueda"
    method = f"fetch_{endpoint}"
    calls = sorted(client.calls_to(method), key=lambda c: c["start"])
    expected_end = date.today() - timedelta(days=1)
    expected_start = expected_end - timedelta(days=days - 1)

    for call in calls:
        span = (call["end"] - call["start"]).days
        assert span <= (CHUNK_DAYS - 1 if inclusive else CHUNK_DAYS)

    assert calls[0]["start"] == expected_start
    assert calls[-1]["end"] == (expected_end if inclusive else expected_end + timedelta(days=1))
    for prev, nxt in zip(calls, calls[1:]):
        # next chunk starts right after the previous chunk's own end
        gap = timedelta(days=1) if inclusive else timedelta(days=0)
        assert nxt["start"] == prev["end"] + gap


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
def test_no_day_is_dropped_at_chunk_boundaries(endpoint, key_fields):
    """End-to-end guard for the exclusive-upper-bound bug: seed a distinct
    record on every single day of a monthly window (0..29 days ago),
    including the days that fall on chunk boundaries, and assert every one is
    fetched. Before the fix, a bare `fechaRegFin=chunk_end` dropped each
    chunk's last day, so the boundary-day records went missing.
    """
    from tests.fake_client import REG_DATE_FIELDS, reg_date

    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]

    records = getattr(client, endpoint)
    records.clear()
    reg_field = REG_DATE_FIELDS.get(endpoint)
    for days_ago in range(30):  # every day of the monthly window
        payload = {key_fields[0]: 500000 + days_ago}
        if reg_field:
            payload[reg_field] = reg_date(days_ago).isoformat()
        records.append({"reg_days_ago": days_ago, "payload": payload})

    stats = sync_fn(SQLSink(engine), client, "monthly")
    assert stats["inserted"] == 30  # not one day lost at any chunk boundary
    assert len(current_rows(engine, endpoint)) == 30


@pytest.mark.parametrize("endpoint,key_fields", INCREMENTAL_CASES, ids=CASE_IDS)
def test_backfill_since_until_range_fetches_the_whole_span(endpoint, key_fields):
    """A `since`/`until` backfill syncs an explicit historical range instead
    of a rolling window. Seed records across ~5 weeks and confirm a backfill
    over that span fetches them all, chunked, and logs the run as "backfill".
    """
    from tests.fake_client import REG_DATE_FIELDS, reg_date
    from tests.timeline_helpers import last_sync_run

    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    sync_fn = SEARCH_SYNCERS[endpoint]

    records = getattr(client, endpoint)
    records.clear()
    reg_field = REG_DATE_FIELDS.get(endpoint)
    for days_ago in (2, 12, 20, 33):  # spread across a multi-week span
        payload = {key_fields[0]: 700000 + days_ago}
        if reg_field:
            payload[reg_field] = reg_date(days_ago).isoformat()
        records.append({"reg_days_ago": days_ago, "payload": payload})

    until = reg_date(1)  # yesterday
    since = reg_date(40)  # 40 days back, covers all four records
    stats = sync_fn(SQLSink(engine), client, since=since, until=until)

    assert stats["inserted"] == 4
    assert len(current_rows(engine, endpoint)) == 4
    assert last_sync_run(engine, endpoint)["run_type"] == "backfill"


def test_search_syncers_registry_covers_every_incremental_entity():
    # convocatorias (two-step discover-then-detail, covered by its own
    # timeline test file) shares the registry with the plain search entities.
    assert set(SEARCH_SYNCERS) == {name for name, _ in INCREMENTAL_CASES} | {"convocatorias"}
