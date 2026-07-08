# SPDX-License-Identifier: GPL-3.0-or-later

"""Storage abstraction. Everything above this package fetches rows; a
Sink persists them.

The interface is batch-oriented on purpose. A sink receives the complete
batch of rows one sync run fetched, plus the context needed to version
them (key fields, and the date range for windowed runs), and owns
everything storage-side from there: table creation, SCD2 versioning,
deletion detection, run logging, error records. A per-row CRUD interface
would assume an UPDATE-capable SQL engine; the batch contract can also be
implemented by an append-only target such as a future Parquet sink.

The only implementation today is `sql.SQLSink`, which covers every target
with a SQLAlchemy dialect (SQLite, PostgreSQL, MySQL, BigQuery). Engine
quirks stay inside that package (see `sql.dialects`) and never leak
through this interface.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any, Optional


class Sink(ABC):
    """One sync target (a database, a file store, ...) in SCD2 form.

    Implementations must guarantee, for every synced endpoint:

    - **SCD2 semantics.** Each record is identified by its natural key
      (the JSON-serialized tuple of `key_fields` values). A new key adds a
      current version; a changed payload (detected by content hash) closes
      the old version and adds a new current one; an unchanged payload only
      refreshes its last-seen timestamp. Closed versions are never deleted:
      history is append-only.
    - **Deletion detection scoped to what the batch can prove.** A
      full-catalog batch (`sync_full`) is the complete current state, so a
      key missing from it is a real deletion and its version is closed. A
      windowed batch (`sync_window`) is only a slice, so absence proves
      nothing by default; if `reg_date_field` is given, a stored row is
      closed only when its own registration date falls inside the window
      and it is absent from the batch (see `sync_window`).
    - **Atomicity per run.** Either the whole batch is applied and the run
      is recorded as successful, or the target's synced data is left
      untouched and the run is recorded as failed. No partially-applied
      batch may ever be visible to readers.
    - **Run bookkeeping.** Every call is logged storage-side (identifier,
      endpoint, run type, timestamps, row counters, final status, error
      text on failure), along with a per-endpoint watermark of the last
      successful run, and one record per skipped malformed row. How that
      log is stored is the sink's business; callers never see it.

    Stats contract: both methods return a dict with at least the keys
    `fetched` (rows consumed from `rows`), `inserted` (new versions
    written, whether for new keys or changed payloads), `updated` (changed
    payloads, i.e. the subset of `inserted` that closed a previous
    version), `touched` (unchanged rows re-seen), and `soft_deleted`
    (versions closed due to detected deletion). `skipped` is present when
    a `skipped` list was passed.
    """

    @abstractmethod
    def sync_full(
        self,
        endpoint: str,
        rows: Iterable[dict[str, Any]],
        key_fields: Sequence[str],
        *,
        skipped: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, int]:
        """Reconcile `endpoint` against `rows` as its COMPLETE current state.

        Args:
            endpoint: Logical entity name, also used as the storage-side
                name (table, file prefix) for this entity.
            rows: The full set of currently-existing records, as returned
                by the API. May be a lazy generator; it is consumed exactly
                once. Records are stored whole; the sink never reads
                payload fields beyond extracting `key_fields`.
            key_fields: Payload field names whose values form the natural
                key. Order matters; it is part of the serialized key.
            skipped: Optional list of malformed-record descriptors (dicts
                with `context` and `content` keys). The caller may keep
                appending to it while `rows` is being consumed; the sink
                reads it only after `rows` is exhausted, persists each
                entry to its error log linked to this run, and reports the
                count as `skipped` in the returned stats.

        Returns:
            Stats dict (see class docstring). Because `rows` is the complete
            state, keys absent from it are closed and counted in
            `soft_deleted`.
        """

    @abstractmethod
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
        """Apply `rows` as the slice of `endpoint` registered in a date range.

        Unlike `sync_full`, absence from `rows` proves nothing on its own:
        the batch is a window over the entity, not its full state, so by
        default no version is ever closed. Versioning of the keys that ARE
        present works exactly as in `sync_full`.

        Args:
            endpoint: Same as in `sync_full`.
            rows: Every record whose registration date falls in
                `[window_start, window_end]` (both inclusive), as fetched
                from the API. May be a lazy generator; consumed once.
            key_fields: Same as in `sync_full`.
            window_start: First day of the fetched range, inclusive.
            window_end: Last day of the fetched range, inclusive. Both bounds
                are recorded so windowed deletion detection can compare like
                with like (see `reg_date_field`).
            run_type: Label for the run log distinguishing cadence runs
                ("daily", "weekly", "monthly", "annual") from historical
                loads ("backfill"). The sink stores it verbatim.
            reg_date_field: Opt-in for window-scoped deletion detection: the
                payload field (ISO date string) holding the record's OWN
                registration date. When given, a stored current version is
                closed if its registration date falls inside
                `[window_start, window_end]` and its key is absent from
                `rows`. Both sides of the comparison then cover the same
                fixed range, which is what makes absence meaningful. Entities
                whose payload exposes no such field must leave this None and
                get no deletion detection on windowed runs.
            skipped: Same contract as in `sync_full`.

        Returns:
            Stats dict (see class docstring). `soft_deleted` can only be
            non-zero when `reg_date_field` was given.
        """


def get_sink(url: str) -> Sink:
    """Build the sink for a target URL.

    The URL scheme picks the implementation. Today every scheme is a
    SQLAlchemy dialect and maps to `sql.SQLSink` (`sqlite:///...`,
    `postgresql://...`, `bigquery://project/dataset`). A future file-based
    sink would claim its own scheme here, e.g. `parquet:///path`.
    """
    from bdns.sync.sinks.sql import SQLSink

    return SQLSink.from_url(url)
