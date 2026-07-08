# SPDX-License-Identifier: GPL-3.0-or-later

"""SQL implementation of the Sink interface, covering every target with a
SQLAlchemy dialect (SQLite, PostgreSQL, MySQL, BigQuery, ...).

Module map: `schema.py` (generic SCD2 table shape + control tables),
`scd2.py` (staging + bulk-diff apply logic), `bookkeeping.py` (run log,
watermark, error records), `dialects.py` (per-engine adapters, the only
code allowed to branch on dialect name).
"""

from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from bdns.sync.sinks import Sink
from bdns.sync.sinks.sql.bookkeeping import run_with_bookkeeping
from bdns.sync.sinks.sql.scd2 import apply_full_reconciliation, apply_incremental


class SQLSink(Sink):
    """Sink backed by a SQLAlchemy engine.

    Implements the batch contract with a staging table plus a fixed number
    of bulk SQL statements per run, never a per-row loop (scd2.py explains
    why that matters on BigQuery). Atomicity comes from wrapping each run
    in a single transaction. Run bookkeeping lives in the `_sync_runs` /
    `_sync_state` / `_sync_errors` tables next to the synced data.
    """

    def __init__(self, engine: Engine):
        self.engine = engine

    @classmethod
    def from_url(cls, url: str) -> "SQLSink":
        return cls(create_engine(url))

    def sync_full(
        self,
        endpoint: str,
        rows: Iterable[dict[str, Any]],
        key_fields: Sequence[str],
        *,
        skipped: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, int]:
        def apply_fn(conn, table, staging):
            stats = apply_full_reconciliation(conn, table, staging, rows, key_fields)
            return _attach_skips(stats, skipped)

        return run_with_bookkeeping(self.engine, endpoint, run_type="full", apply_fn=apply_fn)

    def sync_window(
        self,
        endpoint: str,
        rows: Iterable[dict[str, Any]],
        key_fields: Sequence[str],
        *,
        window_start: date,
        window_end: date,
        run_type: str,
        reg_date_field: Optional[str] = None,
        skipped: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, int]:
        def apply_fn(conn, table, staging):
            stats = apply_incremental(
                conn,
                table,
                staging,
                rows,
                key_fields,
                reg_date_field=reg_date_field,
                window_start=window_start,
                window_end=window_end,
            )
            return _attach_skips(stats, skipped)

        return run_with_bookkeeping(self.engine, endpoint, run_type=run_type, apply_fn=apply_fn)


def _attach_skips(stats: dict[str, int], skipped: Optional[list[dict[str, str]]]) -> dict[str, int]:
    """Fold the caller's malformed-record list into the stats AFTER the rows
    generator has been fully consumed (which is what populated it)."""
    if skipped is not None:
        stats["skipped"] = len(skipped)
        stats["_skip_details"] = skipped
    return stats
