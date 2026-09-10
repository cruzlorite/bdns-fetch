# SPDX-License-Identifier: GPL-3.0-or-later

"""Core SCD2 apply logic.

Stage the fetched batch, then diff it against the target table with a
fixed number of bulk SQL statements, never a per-row UPDATE/INSERT loop.

Bulk statements are a requirement, not just an optimization. On BigQuery
every DML statement pays per-statement latency and cost regardless of how
many rows it touches, so a loop of thousands of single-row UPDATEs does
not scale to the volumes involved (concesiones_busqueda alone is 20M+
rows). Staging plus a handful of bulk statements costs the same number of
statements whether the batch is 20 rows or 2 million.

Only portable SQL is used: correlated EXISTS/NOT EXISTS subqueries, no
vendor-specific UPDATE...FROM or MERGE. The same code path runs unchanged
on SQLite, PostgreSQL, and BigQuery.
"""

import logging
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, cast, exists, func, insert, literal, null, or_, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.sql.schema import Table

from bdns.sync.hashing import natural_key
from bdns.sync.pipeline import chunked, prefetch
from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy
from bdns.sync.sinks import DEFAULT_LIMITS, RejectLimits
from bdns.sync.sinks.sql.dialects import DialectAdapter, get_adapter

__all__ = ["BatchRejected", "apply_full_reconciliation", "apply_incremental"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BatchRejected(RuntimeError):
    """Too much of the batch could not be versioned to apply it safely."""


def rejection_reason(
    payload: Any, key_fields: Sequence[str], reg_date_field: Optional[str]
) -> Optional[str]:
    """Why this record cannot be versioned, or None if it can.

    A record without a usable natural key has no identity, so there is
    nothing to version it as. Rejecting it here, in the sink, covers every
    entity: `syncers._skip_malformed` only guards the two-step detail
    fetches, and it only catches responses that are not JSON objects at
    all.

    A null key is the case worth spelling out. It does not raise: it
    serializes to the literal key `[null]`, so every record missing that
    field collapses onto one key and they overwrite each other run after
    run, reporting success throughout.

    The registration date is checked only where the entity declares one,
    since that is where it is read. `%Y-%m-%d` is required rather than
    accepted loosely: if the source starts sending datetimes, that is a
    change worth surfacing in `_sync_errors`, not one to absorb silently.
    """
    if not isinstance(payload, dict):
        return "record is not a JSON object"
    for field in key_fields:
        if field not in payload:
            return f"missing key field {field}"
        if payload[field] is None:
            return f"null key field {field}"
    if reg_date_field:
        raw = payload.get(reg_date_field)
        if raw is None:
            return f"missing or null registration date {reg_date_field}"
        try:
            datetime.strptime(raw, "%Y-%m-%d")
        except (TypeError, ValueError):
            return f"unparseable registration date {reg_date_field}={raw!r}"
    return None


def apply_full_reconciliation(
    conn: Connection,
    table: Table,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    policy: PayloadPolicy = DEFAULT_POLICY,
    limits: RejectLimits = DEFAULT_LIMITS,
    chunk_size: int = 5000,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    """Diff a complete batch against the table's current rows.

    Four cases, one bulk statement each:

    - Natural key not seen before: insert a new current row.
    - Natural key seen, hash changed: close the old version, insert a new
      current one.
    - Natural key seen, hash unchanged: touch `_synced_at`.
    - Natural key was current but absent from `rows`: close it out.

    The last case is what detects deletions, such as grants withdrawn or
    codes retired. Incremental passes cannot see removals; only a
    full-set diff can.

    Args:
        conn: Open connection, inside the run's transaction.
        table: The endpoint's SCD2 table.
        staging: Its staging table. Cleared before and after use.
        rows: The complete current state, as fetched. Consumed once.
        key_fields: Fields forming the natural key.
        policy: Rules applied to each record before storing and hashing.
        limits: How much of the batch may be unusable before the run
            refuses it.
        chunk_size: Rows buffered per staging insert, before the
            dialect adapter gets to raise it.
        skipped: List that malformed-record descriptors are appended to.

    Returns:
        The run's counters: `fetched`, `inserted`, `updated`, `touched`,
        `soft_deleted`.

    Raises:
        BatchRejected: If the share of unusable records crosses `limits`.
    """
    return _apply(
        conn, table, staging, rows, key_fields, policy, limits, chunk_size,
        detect_deletions=True, skipped=skipped,
    )


def apply_incremental(
    conn: Connection,
    table: Table,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    policy: PayloadPolicy = DEFAULT_POLICY,
    limits: RejectLimits = DEFAULT_LIMITS,
    chunk_size: int = 5000,
    reg_date_field: Optional[str] = None,
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    """Apply a windowed batch: one reg-date window pass.

    Versioning of the keys present works exactly as in
    `apply_full_reconciliation`. What differs is deletion: by default no
    key is ever closed, because a reg-date window is a subset of the
    table rather than its full current state, so absence says nothing.

    Args:
        conn: Open connection, inside the run's transaction.
        table: The endpoint's SCD2 table.
        staging: Its staging table. Cleared before and after use.
        rows: Records registered in the window, as fetched. Consumed
            once.
        key_fields: Fields forming the natural key.
        policy: Rules applied to each record before storing and hashing.
        limits: How much of the batch may be unusable before the run
            refuses it.
        chunk_size: Rows buffered per staging insert.
        reg_date_field: Payload field holding the record's own
            registration date, as an ISO date string. Opts into
            window-scoped deletion detection, which closes a current row
            only when its own stored `_reg_date` falls inside the window
            and its key is missing from `rows`. Scoping both sides of the
            comparison to the same fixed range is what makes absence
            meaningful: every row ages out of a rolling window eventually
            whether or not it was deleted, so a plain window-vs-window
            diff cannot tell the two apart. This one can.
        window_start: First day of the fetched range, inclusive.
        window_end: Last day of the fetched range, inclusive. Must be the
            same bounds `rows` was fetched with.
        skipped: List that malformed-record descriptors are appended to.

    Returns:
        The run's counters. `soft_deleted` can only be non-zero when
        `reg_date_field` was given.

    Raises:
        BatchRejected: If the share of unusable records crosses `limits`.
    """
    window = (reg_date_field, window_start, window_end) if reg_date_field else None
    return _apply(
        conn, table, staging, rows, key_fields, policy, limits, chunk_size,
        detect_deletions=False, window=window, skipped=skipped,
    )


def _apply(
    conn: Connection,
    table: Table,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    policy: PayloadPolicy,
    limits: RejectLimits,
    chunk_size: int,
    detect_deletions: bool,
    window: Optional[tuple] = None,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    """Stage the batch, then apply the diff. The engine both entry points share.

    The sequence is fixed: clear staging, load the batch into it, count
    what the diff will do, then insert, touch and close in that order.
    Counting first matters, because each statement changes what the next
    one would have counted.

    Args:
        conn: Open connection, inside the run's transaction.
        table: The endpoint's SCD2 table.
        staging: Its staging table.
        rows: The fetched batch. Consumed once.
        key_fields: Fields forming the natural key.
        policy: Rules applied before storing and hashing.
        limits: How much of the batch may be unusable.
        chunk_size: Rows per staging insert, before the adapter raises it.
        detect_deletions: Close keys absent from the batch. Only true for
            a full reconciliation, where absence actually proves removal.
        window: `(reg_date_field, start, end)` for window-scoped deletion
            detection, or None for no deletion detection at all.
        skipped: List that rejected records are appended to.

    Returns:
        The run's counters.

    Raises:
        BatchRejected: If the rejects cross `limits`.
    """
    now = datetime.now(timezone.utc)
    reg_date_field = window[0] if window else None
    policy.check_identity(key_fields, reg_date_field)
    adapter = get_adapter(conn.engine)
    rejected = skipped if skipped is not None else []

    adapter.clear_table(conn, staging)
    fetched = _load_staging(
        conn, staging, rows, key_fields, policy, chunk_size, reg_date_field, adapter, rejected,
    )
    _check_rejects(table.name, fetched, len(rejected), limits)
    logger.info("%s: fetch done, %d rows staged, applying diff", table.name, fetched)
    stats = _diff_stats(conn, table, staging, detect_deletions, window)
    stats["fetched"] = fetched

    _touch_unchanged(conn, table, staging, now)
    _close_stale(conn, table, staging, now, detect_deletions, window)
    _insert_new_versions(conn, table, staging, now)

    adapter.clear_table(conn, staging)
    return stats


def _load_staging(
    conn: Connection,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    policy: PayloadPolicy,
    chunk_size: int,
    reg_date_field: Optional[str],
    adapter: DialectAdapter,
    rejected: list[dict[str, str]],
) -> int:
    """Write `rows` into the staging table in chunks.

    `prefetch` builds the next chunk on a helper thread while this thread
    writes the current one. Writes have to stay on this thread:
    `conn` must not leave the thread that created it (SQLite requires
    this). They also stay serial on purpose: BigQuery caps table update
    operations at a low fixed rate, and concurrent writes trip a hard 429
    (see `dialects.BigQueryAdapter.insert_rows`).
    """
    chunk_size = adapter.staging_chunk_size(chunk_size)

    def stage(payload):
        """Build the staged row, or None if the record cannot be versioned.

        A rejected record is dropped and recorded rather than raised on:
        one malformed record out of millions should not cost a multi-hour
        backfill. `_check_reject_ratio` is what still fails the run when
        the rejects stop looking like noise.
        """
        reason = rejection_reason(payload, key_fields, reg_date_field)
        if reason is not None:
            logger.warning("%s: rejecting record (%s): %.200r", staging.name, reason, payload)
            rejected.append({"context": reason, "content": str(payload)[:200]})
            return None
        # One call for both, so what is hashed is always what is stored.
        stored, digest = policy.prepare(payload)
        staged = {
            "_natural_key": natural_key(stored, key_fields),
            "_row_hash": digest,
            "payload": stored,
        }
        if reg_date_field:
            staged["_reg_date"] = datetime.strptime(stored[reg_date_field], "%Y-%m-%d").date()
        return staged

    staged_rows = (row for row in map(stage, rows) if row is not None)
    fetched = 0
    for chunk in prefetch(chunked(staged_rows, chunk_size)):
        adapter.insert_rows(conn, staging, chunk)
        fetched += len(chunk)
        # Staging a multi-million-row backfill takes hours; log every
        # ~10 chunks so there is no silent gap between the per-chunk
        # fetch logs and the final "fetch done" line.
        if fetched % (chunk_size * 10) == 0:
            logger.info("%s: %d rows staged so far", staging.name, fetched)
    return fetched


def _check_rejects(table_name: str, fetched: int, rejected: int, limits: RejectLimits) -> None:
    """Log the rejects, and refuse the batch if there are too many of them.

    Raises:
        BatchRejected: If `limits` says this many rejects is no longer
            noise but a change in what the source returns.
    """
    if not rejected:
        return
    logger.warning(
        "%s: %d record(s) rejected of %d fetched", table_name, rejected, fetched
    )
    reason = limits.rejection(fetched, rejected)
    if reason:
        raise BatchRejected(
            f"{table_name}: {reason}; refusing to apply the batch. "
            f"See _sync_errors for the reasons."
        )


def _matches(table: Table, staging: Table):
    """Build the natural-key join predicate every diff statement shares."""
    return staging.c._natural_key == table.c._natural_key


def _missing_in_window(table: Table, staging: Table, window: tuple):
    """Build the predicate selecting current rows this window may close.

    A row is eligible only if its own `_reg_date` says it belongs to this
    exact window, regardless of whether it was in a previous run's fetch.
    Both sides of the comparison then use the same range, so aging out of
    a rolling window is never mistaken for deletion.
    """
    _, start, end = window
    return and_(
        table.c._reg_date.isnot(None),
        table.c._reg_date >= start,
        table.c._reg_date <= end,
        ~exists(select(1).where(_matches(table, staging))),
    )


def _diff_stats(
    conn: Connection, table: Table, staging: Table, detect_deletions: bool, window: Optional[tuple] = None
) -> dict[str, int]:
    """Count what the diff is about to do, before any statement changes it.

    Every counter is a separate COUNT over the same staging/table join.
    They have to run before the writes: once rows are inserted or closed,
    the queries would no longer see the state they are meant to measure.
    """
    touched = conn.execute(
        select(func.count())
        .select_from(table)
        .where(
            table.c._is_current.is_(True),
            exists(select(1).where(_matches(table, staging), staging.c._row_hash == table.c._row_hash)),
        )
    ).scalar_one()

    updated = conn.execute(
        select(func.count())
        .select_from(table)
        .where(
            table.c._is_current.is_(True),
            exists(select(1).where(_matches(table, staging), staging.c._row_hash != table.c._row_hash)),
        )
    ).scalar_one()

    # count distinct keys, matching the DISTINCT dedup in _insert_new_versions
    inserted = conn.execute(
        select(func.count(func.distinct(staging.c._natural_key)))
        .select_from(staging)
        .where(
            ~exists(
                select(1).where(_matches(table, staging), table.c._is_current.is_(True))
            )
        )
    ).scalar_one()

    stats = {"inserted": inserted, "updated": updated, "touched": touched}

    if detect_deletions:
        closed = conn.execute(
            select(func.count())
            .select_from(table)
            .where(table.c._is_current.is_(True), ~exists(select(1).where(_matches(table, staging))))
        ).scalar_one()
        stats["soft_deleted"] = closed
    elif window:
        closed = conn.execute(
            select(func.count())
            .select_from(table)
            .where(table.c._is_current.is_(True), _missing_in_window(table, staging, window))
        ).scalar_one()
        stats["soft_deleted"] = closed

    return stats


def _touch_unchanged(conn: Connection, table: Table, staging: Table, now: datetime) -> None:
    """Refresh `_synced_at` on current rows whose hash the batch confirms.

    No new version: the record was seen again and is unchanged, so only
    the last-seen timestamp moves.
    """
    conn.execute(
        update(table)
        .where(
            table.c._is_current.is_(True),
            exists(select(1).where(_matches(table, staging), staging.c._row_hash == table.c._row_hash)),
        )
        .values(_synced_at=now)
    )


def _close_stale(
    conn: Connection,
    table: Table,
    staging: Table,
    now: datetime,
    detect_deletions: bool,
    window: Optional[tuple] = None,
) -> None:
    """Close every current version this batch supersedes or proves gone.

    A changed hash always closes the old version. Absence closes one only
    when the batch is entitled to conclude removal: a full reconciliation
    always is, a windowed run only for rows whose own `_reg_date` puts
    them inside the window, and a plain windowed run never is.
    """
    changed = exists(
        select(1).where(_matches(table, staging), staging.c._row_hash != table.c._row_hash)
    )
    condition = changed
    if detect_deletions:
        missing = ~exists(select(1).where(_matches(table, staging)))
        condition = or_(changed, missing)
    elif window:
        condition = or_(changed, _missing_in_window(table, staging, window))

    conn.execute(
        update(table)
        .where(table.c._is_current.is_(True), condition)
        .values(_valid_to=now, _is_current=False)
    )


def _insert_new_versions(conn: Connection, table: Table, staging: Table, now: datetime) -> None:
    """Insert a current version for every staged key with no current row left.

    Runs after `_close_stale`, so it covers both cases at once: keys
    never seen before, and keys whose previous version was just closed
    because their hash changed.
    """
    no_current_match = ~exists(
        select(1).where(_matches(table, staging), table.c._is_current.is_(True))
    )
    # DISTINCT: if the same record was fetched twice into staging (e.g. a
    # stray concurrent writer), collapse the identical copies instead of
    # inserting two current versions of the same natural key.
    select_new_versions = (
        select(
            staging.c._natural_key,
            staging.c._row_hash,
            literal(now),
            # CAST(NULL AS ...), not a bare NULL: PostgreSQL types an
            # untyped NULL in a SELECT as `text` and then refuses the
            # INSERT into a timestamptz column, failing every run with
            # `column _valid_to is of type timestamp with time zone but
            # expression is of type text`. The cast is portable, and
            # BigQuery needs an explicit type on a NULL literal too.
            cast(null(), table.c._valid_to.type),
            literal(True),
            literal(now),
            staging.c._reg_date,
            staging.c.payload,
        )
        .where(no_current_match)
        .distinct()
    )

    conn.execute(
        insert(table).from_select(
            [
                "_natural_key",
                "_row_hash",
                "_valid_from",
                "_valid_to",
                "_is_current",
                "_synced_at",
                "_reg_date",
                "payload",
            ],
            select_new_versions,
        )
    )
