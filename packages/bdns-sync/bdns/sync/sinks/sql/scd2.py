# SPDX-License-Identifier: GPL-3.0-or-later

"""Core SCD2 apply logic: stage the fetched batch, then diff it against
the target table with a fixed number of bulk SQL statements, never a
per-row UPDATE/INSERT loop.

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
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, cast, exists, func, insert, literal, null, or_, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.sql.schema import Table

from bdns.sync.hashing import natural_key, row_hash
from bdns.sync.pipeline import chunked, prefetch
from bdns.sync.sinks.sql.dialects import DialectAdapter, get_adapter

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# A batch where most records were rejected is not a batch with a few bad
# records in it, it is a batch whose shape the source changed. Applying it
# would be destructive rather than merely wrong: staging would be near
# empty, and on an entity with window-scoped deletion detection that closes
# the whole window as withdrawals. Above this share the run fails instead,
# leaving the table untouched and the reasons in `_sync_errors`.
MAX_REJECT_RATIO = 0.10

# ...but individual broken records are a documented, permanent trait of this
# source (see section 8 of docs/bdns-api-behavior.md), and a narrow window
# can legitimately hold only a handful of records, where one bad one is
# already a large share. So the ratio only bites once there are at least
# this many rejects. A batch left completely empty by rejects always fails,
# whatever the count: there is nothing to apply and plenty to destroy.
MIN_REJECTS_TO_ENFORCE_RATIO = 5


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
    exclude_from_hash: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
    chunk_size: int = 5000,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    """
    Diff a full batch of currently-fetched rows against the table's current rows.

    - Natural key not seen before -> insert new current row.
    - Natural key seen, hash changed -> close out old version, insert new one.
    - Natural key seen, hash unchanged -> just touch `_synced_at`.
    - Natural key was current but absent from `rows` -> close it out.

    The last case is what detects deletions (grants withdrawn, retired
    codes). Incremental passes alone can't see removals; only a full-set
    diff can.
    """
    return _apply(
        conn, table, staging, rows, key_fields, exclude_from_hash, delimited_lists, chunk_size,
        detect_deletions=True, skipped=skipped,
    )


def apply_incremental(
    conn: Connection,
    table: Table,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    exclude_from_hash: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
    chunk_size: int = 5000,
    reg_date_field: Optional[str] = None,
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    """
    Apply a partial/windowed batch of fetched rows (one reg-date window pass).

    By default this never closes out keys absent from `rows`. A reg-date
    window is a subset of the table, not the full current state, so absence
    here says nothing about deletion on its own.

    Pass `reg_date_field`, along with `window_start` and `window_end` (the
    same bounds used to fetch `rows`), to opt into window-scoped deletion
    detection: a current row is closed only if its own stored `_reg_date`
    falls inside `[window_start, window_end]` and it's missing from `rows`.
    Scoping the comparison to rows that themselves belong to this window,
    rather than rows that were simply in the previous run's fetch, avoids
    the false-positive trap of a plain window-vs-window diff. Every row
    ages out of a rolling window eventually regardless of deletion, so that
    kind of comparison can't tell the two apart. This one can, because both
    sides of the comparison use the same fixed date range.
    """
    window = (reg_date_field, window_start, window_end) if reg_date_field else None
    return _apply(
        conn, table, staging, rows, key_fields, exclude_from_hash, delimited_lists, chunk_size,
        detect_deletions=False, window=window, skipped=skipped,
    )


def _apply(
    conn: Connection,
    table: Table,
    staging: Table,
    rows: Iterable[dict[str, Any]],
    key_fields: Sequence[str],
    exclude_from_hash: Optional[Iterable[str]],
    delimited_lists: Optional[Mapping[str, str]],
    chunk_size: int,
    detect_deletions: bool,
    window: Optional[tuple] = None,
    skipped: Optional[list[dict[str, str]]] = None,
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    reg_date_field = window[0] if window else None
    adapter = get_adapter(conn.engine)
    rejected = skipped if skipped is not None else []

    adapter.clear_table(conn, staging)
    fetched = _load_staging(
        conn, staging, rows, key_fields, exclude_from_hash, delimited_lists, chunk_size,
        reg_date_field, adapter, rejected,
    )
    _check_reject_ratio(table.name, fetched, len(rejected))
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
    exclude_from_hash: Optional[Iterable[str]],
    delimited_lists: Optional[Mapping[str, str]],
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
        """Returns the staged row, or None if the record cannot be versioned.

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
        staged = {
            "_natural_key": natural_key(payload, key_fields),
            "_row_hash": row_hash(payload, exclude_from_hash, delimited_lists),
            "payload": payload,
        }
        if reg_date_field:
            staged["_reg_date"] = datetime.strptime(payload[reg_date_field], "%Y-%m-%d").date()
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


def _check_reject_ratio(table_name: str, fetched: int, rejected: int) -> None:
    if not rejected:
        return
    share = rejected / (fetched + rejected)
    logger.warning("%s: %d record(s) rejected, %.1f%% of the batch", table_name, rejected, share * 100)
    too_many = share > MAX_REJECT_RATIO and rejected >= MIN_REJECTS_TO_ENFORCE_RATIO
    if fetched == 0 or too_many:
        raise BatchRejected(
            f"{table_name}: {rejected} of {fetched + rejected} records could not be versioned "
            f"({share:.0%}); refusing to apply the batch. See _sync_errors for the reasons."
        )


def _matches(table: Table, staging: Table):
    return staging.c._natural_key == table.c._natural_key


def _missing_in_window(table: Table, staging: Table, window: tuple):
    """A current row is eligible to close under window-scoped deletion only
    if its own `_reg_date` says it belongs to this exact window, regardless
    of whether it was in a previous run's fetch. Both sides of the
    comparison use the same range, so aging out of a rolling window is
    never mistaken for deletion.
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
