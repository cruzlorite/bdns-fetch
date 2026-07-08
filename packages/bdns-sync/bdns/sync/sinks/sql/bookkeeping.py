# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared plumbing every `sync_*` function runs through: create tables,
log the run in `_sync_runs`, apply the entity's own fetch and SCD2 logic,
record the outcome, and bump the `_sync_state` watermark.

Bookkeeping events are committed in their own short transactions, separate
from the data transaction. Inside the data transaction they would inherit
its fate: on transactional engines (SQLite/Postgres) a failed run would
roll back its own `started`/`failed` records and silently erase every
failed run from the log. Kept separate, the log always tells the truth:
`started` is committed before any data work, the terminal `success` is
written only after the data transaction committed, and `failed` is written
even though the data rolled back.

Per-engine guarantee (documented in the README): on SQLite/Postgres the data
transaction is real, so no terminal `success` event means the target table
is untouched. On BigQuery there is no transaction at all (its DBAPI commit
is a no-op, verified live), so a crash mid-diff can leave partially-applied
changes, but the design converges: staging is cleared and rebuilt at the
start of every run, and re-running the same range heals any intermediate
state (a closed version whose key is still present simply gets its new
current version on the next successful pass). Either way the operational
rule is the same: no `success` event => re-run.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import MetaData, insert, update
from sqlalchemy.engine import Engine

from bdns.sync.sinks.sql.dialects import get_adapter
from bdns.sync.sinks.sql.schema import build_control_tables, build_staging_table, build_sync_table

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def run_with_bookkeeping(
    engine: Engine, endpoint_name: str, run_type: str, apply_fn: Callable
) -> dict[str, int]:
    """`run_type` is a classification label for `_sync_runs`: either "full"
    (full-catalog/swept/discover-then-detail syncs) or a reg-date window name
    (daily/weekly/monthly/annual, for the incremental syncs).
    """
    metadata = MetaData()
    table = build_sync_table(endpoint_name, metadata)
    staging = build_staging_table(endpoint_name, metadata)
    sync_state, sync_runs, sync_errors = build_control_tables(metadata)
    get_adapter(engine).prepare_metadata(metadata)
    metadata.create_all(engine, checkfirst=True)

    started_at = datetime.now(timezone.utc)
    # App-generated id (epoch microseconds) instead of DB autoincrement:
    # BigQuery has none, and this key is read back (it links `_sync_errors`
    # and the terminal event). One id per run and runs are sequential per
    # orchestrator, so microseconds can't collide.
    run_id = time.time_ns() // 1_000
    logger.info("%s: run %s (%s) starting", endpoint_name, run_id, run_type)

    def record_event(event: str, **extra) -> None:
        with engine.begin() as event_conn:
            event_conn.execute(
                insert(sync_runs).values(
                    run_id=run_id,
                    table_name=endpoint_name,
                    run_type=run_type,
                    event=event,
                    occurred_at=datetime.now(timezone.utc),
                    **extra,
                )
            )

    record_event("started")

    try:
        with engine.begin() as conn:
            stats = apply_fn(conn, table, staging)
    except Exception as exc:
        logger.error("%s: run %s failed after %.1fs: %s", endpoint_name, run_id,
                     (datetime.now(timezone.utc) - started_at).total_seconds(), exc)
        record_event("failed", error=str(exc))
        raise

    # Terminal bookkeeping runs AFTER the data transaction committed, so a
    # `success` event can never describe rolled-back data.
    finished_at = datetime.now(timezone.utc)
    skip_details = stats.pop("_skip_details", [])
    record_event(
        "success",
        rows_fetched=stats["fetched"],
        rows_inserted=stats["inserted"] + stats["updated"],
        rows_soft_deleted=stats.get("soft_deleted", 0),
        rows_skipped=stats.get("skipped", 0),
    )
    with engine.begin() as conn:
        if skip_details:
            conn.execute(
                insert(sync_errors),
                [
                    {
                        "error_id": run_id + i,
                        "run_id": run_id,
                        "table_name": endpoint_name,
                        "context": detail["context"],
                        "content": detail["content"],
                        "occurred_at": finished_at,
                    }
                    for i, detail in enumerate(skip_details)
                ],
            )
        _upsert_sync_state(conn, sync_state, endpoint_name, finished_at, run_id)

    logger.info(
        "%s: run %s done in %.1fs (fetched=%d inserted=%d updated=%d touched=%d soft_deleted=%d skipped=%d)",
        endpoint_name, run_id, (finished_at - started_at).total_seconds(),
        stats["fetched"], stats["inserted"], stats["updated"], stats["touched"],
        stats.get("soft_deleted", 0), stats.get("skipped", 0),
    )
    return stats


def _upsert_sync_state(conn, sync_state, table_name: str, synced_at: datetime, run_id: int) -> None:
    """Dialect-agnostic upsert: update if the row exists, insert otherwise."""
    result = conn.execute(
        update(sync_state)
        .where(sync_state.c.table_name == table_name)
        .values(last_synced_at=synced_at, last_run_id=run_id)
    )
    if result.rowcount == 0:
        conn.execute(
            insert(sync_state).values(
                table_name=table_name, last_synced_at=synced_at, last_run_id=run_id
            )
        )
