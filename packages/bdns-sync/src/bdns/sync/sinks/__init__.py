# SPDX-License-Identifier: GPL-3.0-or-later

"""The storage abstraction: everything above this package fetches rows, a sink persists them.

The interface is batch-oriented on purpose. A sink receives the complete
batch of rows one sync run fetched, plus the context needed to version
them (key fields, and the date range for windowed runs), and owns
everything storage-side from there: table creation, SCD2 versioning,
deletion detection, run logging, error records. A per-row CRUD interface
would assume an UPDATE-capable SQL engine; the batch contract can also be
implemented by an append-only target such as a future Parquet sink.

The only implementation today is `sql.SQLSink`, which covers every target
with a SQLAlchemy dialect (SQLite, PostgreSQL, BigQuery). Engine
quirks stay inside that package (see `sql.dialects`) and never leak
through this interface.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy

__all__ = ["DEFAULT_LIMITS", "RejectLimits", "Sink", "get_sink"]


@dataclass(frozen=True)
class RejectLimits:
    """How much of a batch may be unusable before the run refuses it.

    Dropping the odd broken record is right: they are a documented,
    permanent trait of this source, and losing a multi-hour backfill to
    one of them helps nobody. Dropping most of a batch is not the same
    event at all. It means the shape of what the source returns changed,
    and applying what survived is actively destructive: staging ends up
    near empty, and to a full reconciliation, or to window-scoped
    deletion detection, an empty batch is indistinguishable from
    "everything here was withdrawn".

    These are operational tolerances, not statements about the data, so
    unlike the payload policy they carry no per-entity defaults and can be
    set per run.

    Attributes:
        max_ratio: Share of the batch that may be rejected. Above it the
            run fails.
        max_count: Optional absolute cap. Above this many rejects the run
            fails whatever the share, which is what catches a shape change
            in a batch large enough to hide it: 200,000 bad records out of
            20 million is 1%, well under any sane ratio, and still means
            something broke.
        min_to_enforce_ratio: Below this many rejects the ratio never
            fires. A narrow window can hold three records, where one bad
            one is already a third of the batch.
    """

    max_ratio: float = 0.10
    max_count: Optional[int] = None
    min_to_enforce_ratio: int = 5

    def rejection(self, fetched: int, rejected: int) -> Optional[str]:
        """Return why this batch must not be applied, or None if it may be.

        Args:
            fetched: Records that were versioned successfully.
            rejected: Records that could not be versioned.

        Returns:
            A sentence naming the count, the share and the limit that was
            crossed, suitable for the run log. None when the batch is
            within tolerance, including when nothing was rejected.
        """
        if not rejected:
            return None
        total = fetched + rejected
        share = rejected / total
        preamble = f"{rejected} of {total} records could not be versioned ({share:.0%})"
        if fetched == 0:
            return f"{preamble}, leaving nothing to apply"
        if self.max_count is not None and rejected > self.max_count:
            return f"{preamble}, over the limit of {self.max_count}"
        if share > self.max_ratio and rejected >= self.min_to_enforce_ratio:
            return f"{preamble}, over the limit of {self.max_ratio:.0%}"
        return None

    def describe(self) -> str:
        """Return one canonical line naming the limits in force.

        Recorded per run, so a run that was refused can be read back
        against the tolerances that refused it.
        """
        cap = "none" if self.max_count is None else str(self.max_count)
        return (
            f"max_ratio={self.max_ratio:.0%} max_count={cap} "
            f"min_to_enforce_ratio={self.min_to_enforce_ratio}"
        )


DEFAULT_LIMITS = RejectLimits()


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
        policy: PayloadPolicy = DEFAULT_POLICY,
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
            policy: What to do to each record before storing and
                versioning it: which fields to drop from the stored
                payload, and which differences stop counting as changes
                (see `bdns.sync.policy`). The sink applies it through
                `PayloadPolicy.prepare`, which returns the payload and
                its hash together, so what is hashed is always what is
                stored. A policy may not drop a key field or the
                registration-date field; the sink rejects one that tries.
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
        policy: PayloadPolicy = DEFAULT_POLICY,
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
            policy: Same as in `sync_full`.
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


def get_sink(url: str, limits: RejectLimits = DEFAULT_LIMITS) -> Sink:
    """Build the sink for a target URL.

    The URL scheme picks the implementation. Today every scheme is a
    SQLAlchemy dialect and maps to `sql.SQLSink` (`sqlite:///...`,
    `postgresql://...`, `bigquery://project/dataset`). A future file-based
    sink would claim its own scheme here, e.g. `parquet:///path`.
    """
    from bdns.sync.sinks.sql import SQLSink

    return SQLSink.from_url(url, limits)
