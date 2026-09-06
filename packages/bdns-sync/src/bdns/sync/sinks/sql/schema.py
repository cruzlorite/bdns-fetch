# SPDX-License-Identifier: GPL-3.0-or-later

"""Generic SCD2 table shape shared by every synced endpoint, plus control tables."""

import json
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.types import TypeDecorator

__all__ = ["PortableJSON", "build_control_tables", "build_staging_table", "build_sync_table"]


class PortableJSON(TypeDecorator):
    """JSON stored as text, serialized in Python rather than by the dialect.

    `sqlalchemy.JSON` hits real gaps on BigQuery: no bind-parameter type
    for JSON, and missing serializer wiring. Plain text is uniformly
    supported everywhere, and `payload` is never queried in SQL by this
    codebase, only read back as a dict in Python.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[str]:
        """Serialize a Python value to the JSON text stored in the column."""
        if value is None:
            return None
        return json.dumps(value, default=str, ensure_ascii=False)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[Any]:
        """Deserialize the stored JSON text back into a Python value."""
        if value is None:
            return None
        return json.loads(value)


def build_sync_table(name: str, metadata: MetaData) -> Table:
    """Build the fixed generic SCD2 table for one synced endpoint.

    There is no per-field schema: the record is stored whole in
    `payload`, and every other column is versioning metadata. `_reg_date`
    is generic too, populated only for entities that opt into
    window-scoped deletion detection; everything else leaves it NULL
    forever.

    Args:
        name: Table name, which is also the endpoint name.
        metadata: MetaData the table is attached to.

    Returns:
        The table. Not created here; the caller emits the DDL.
    """
    return Table(
        name,
        metadata,
        # No surrogate key on purpose: identity is (_natural_key, _valid_from),
        # nothing ever joins on a row id, and DB autoincrement isn't portable
        # (BigQuery has none).
        Column("_natural_key", String, nullable=False, index=True),
        Column("_row_hash", String(64), nullable=False),
        Column("_valid_from", DateTime(timezone=True), nullable=False),
        Column("_valid_to", DateTime(timezone=True), nullable=True),
        Column("_is_current", Boolean, nullable=False),
        Column("_synced_at", DateTime(timezone=True), nullable=False),
        Column("_reg_date", Date, nullable=True),
        Column("payload", PortableJSON, nullable=False),
        extend_existing=True,
        # No-op outside BigQuery (dialect-namespaced kwarg, silently ignored
        # elsewhere). Every SCD2 diff query equality-joins on `_natural_key`
        # (scd2._matches) and most also filter `_is_current`; BigQuery has
        # no secondary indexes (see dialects.py), clustering is its
        # equivalent for pruning scans on these columns.
        bigquery_clustering_fields=["_natural_key", "_is_current"],
    )


def build_staging_table(name: str, metadata: MetaData) -> Table:
    """Build the scratch table holding one run's fetched batch.

    Cleared before use, then diffed against the real table with bulk SQL
    rather than per-row loops.

    Args:
        name: Endpoint name. The table is `_staging_<name>`.
        metadata: MetaData the table is attached to.

    Returns:
        The staging table. Not created here; the caller emits the DDL.
    """
    return Table(
        f"_staging_{name}",
        metadata,
        Column("_natural_key", String, nullable=False, index=True),
        Column("_row_hash", String(64), nullable=False),
        Column("_reg_date", Date, nullable=True),
        Column("payload", PortableJSON, nullable=False),
        extend_existing=True,
        bigquery_clustering_fields=["_natural_key"],
    )


def build_control_tables(metadata: MetaData) -> tuple[Table, Table, Table]:
    """Build the three tables that record what the engine did.

    `_sync_runs` is an event log, never updated in place: one `started`
    row when a run begins, committed immediately and outside the data
    transaction, and one terminal `success`/`failed` row when it ends. A
    run's state is its latest event, so a `started` with no terminal
    event means the process died mid-run. A mutable status column could
    never record that, since a dead process cannot update its own row.
    Row counters travel on the terminal event.

    `_sync_errors` is separate from the synced tables on purpose: a
    malformed record has no natural key and no real payload, so it cannot
    be versioned the way a normal row is. Its own table keeps the synced
    tables free of anything that is not real business data.

    Args:
        metadata: MetaData the tables are attached to.

    Returns:
        `(_sync_state, _sync_runs, _sync_errors)`: the per-table
        watermark, the append-only run log, and one row per skipped
        malformed record.
    """
    sync_state = Table(
        "_sync_state",
        metadata,
        Column("table_name", String, primary_key=True),
        Column("last_synced_at", DateTime(timezone=True), nullable=True),
        Column("last_run_id", BigInteger, nullable=True),
        extend_existing=True,
    )
    sync_runs = Table(
        "_sync_runs",
        metadata,
        # App-generated (epoch microseconds, see bookkeeping): DB autoincrement
        # isn't portable (BigQuery has none) and this key is read back.
        # BigInteger, not Integer: epoch microseconds (~1.7e15) overflow the
        # 32-bit INTEGER that PostgreSQL maps Integer to.
        Column("run_id", BigInteger, nullable=False, index=True),
        Column("table_name", String, nullable=False, index=True),
        Column("run_type", String, nullable=False),
        Column("event", String, nullable=False),  # started | success | failed
        Column("occurred_at", DateTime(timezone=True), nullable=False),
        Column("rows_fetched", Integer, nullable=True),
        Column("rows_inserted", Integer, nullable=True),
        Column("rows_soft_deleted", Integer, nullable=True),
        Column("rows_skipped", Integer, nullable=True),
        Column("error", String, nullable=True),
        extend_existing=True,
    )
    sync_errors = Table(
        "_sync_errors",
        metadata,
        Column("error_id", BigInteger, primary_key=True, autoincrement=False),
        Column("run_id", BigInteger, nullable=False, index=True),
        Column("table_name", String, nullable=False, index=True),
        Column("context", String, nullable=False),
        Column("content", String, nullable=False),
        Column("occurred_at", DateTime(timezone=True), nullable=False),
        extend_existing=True,
    )
    return sync_state, sync_runs, sync_errors
