"""Shared plumbing for the multi-day scenario tests (test_timeline_*.py).

Every scenario test scripts a sequence of simulated sync runs ("days")
against a `FakeBDNSClient` seeded from real, anonymized BDNS payloads
(tests/fixtures/), mutating the client's in-memory data between runs the
same way the real upstream data changes between cron runs: a field edited,
a row withdrawn, a new row registered.
"""

from collections.abc import Sequence
from copy import deepcopy
from typing import Any

from sqlalchemy import MetaData, desc, select

from bdns.sync.sinks.sql.schema import build_control_tables, build_sync_table


def current_rows(engine, name):
    metadata = MetaData()
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        return conn.execute(select(table).where(table.c._is_current.is_(True))).mappings().all()


def last_sync_run(engine, table_name):
    """Latest EVENT of the most recent `_sync_runs` run for `table_name`
    (the run log is append-only: started + terminal success/failed events;
    a run's state is its latest event). This is the durable record of what
    a run did (rows fetched, inserted, soft-deleted, skipped), independent
    of the transient stats dict the sync_* function happens to return.
    """
    metadata = MetaData()
    _, sync_runs, _ = build_control_tables(metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(sync_runs)
            .where(sync_runs.c.table_name == table_name)
            .order_by(desc(sync_runs.c.run_id), desc(sync_runs.c.occurred_at))
            .limit(1)
        ).mappings().one()


def sync_errors_for(engine, table_name):
    """All `_sync_errors` rows for `table_name`, most recent first. This is
    the durable, queryable record of which malformed records were skipped,
    not just how many.
    """
    metadata = MetaData()
    _, _, sync_errors = build_control_tables(metadata)
    with engine.begin() as conn:
        return conn.execute(
            select(sync_errors)
            .where(sync_errors.c.table_name == table_name)
            .order_by(desc(sync_errors.c.error_id))
        ).mappings().all()


def all_rows(engine, name):
    metadata = MetaData()
    table = build_sync_table(name, metadata)
    with engine.begin() as conn:
        return conn.execute(select(table)).mappings().all()


def fresh_copy_with_new_key(row: dict[str, Any], key_fields: Sequence[str]) -> dict[str, Any]:
    """Deep-copy `row` and perturb its key field(s) so it reads as a brand
    new natural key. Used to simulate a newly-registered record appearing.
    """
    new_row = deepcopy(row)
    for field in key_fields:
        value = new_row[field]
        new_row[field] = value + 999000 if isinstance(value, int) else f"{value}-NEW"
    return new_row
