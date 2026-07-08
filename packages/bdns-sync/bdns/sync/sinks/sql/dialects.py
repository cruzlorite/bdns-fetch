# SPDX-License-Identifier: GPL-3.0-or-later

"""Per-engine adapters. The rest of the codebase writes portable SQL (see
scd2.py) that runs unchanged on SQLite, Postgres, MySQL, and BigQuery.
This module is the only place allowed to know a specific engine's name
and quirks; nothing outside it should branch on `dialect.name`.

BigQuery is a first-class target and, so far, the only one that needs an
adapter. SQLite, Postgres, and MySQL are covered by the DialectAdapter
default.

To handle a new quirk, add a method to DialectAdapter with a portable
default (usually a no-op), override it in the engine's adapter, and call
it from the module that hits the difference. `prepare_metadata` is the
existing example: BigQuery rejects CREATE INDEX, so its adapter strips
indexes from the metadata before create_all, while every other target
keeps them through the inherited no-op.

This abstraction covers SQL engines only. Anything that speaks SQLAlchemy
Engine (Redshift, Snowflake, DuckDB) would slot in as an adapter.
File-based targets (Parquet, Delta) have no connection, no UPDATE, and no
transaction, so the staging-plus-diff design in scd2.py does not apply to
them; such a target would need its own Sink implementation, not an
adapter.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import MetaData, insert
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql.schema import Table


class DialectAdapter:
    """Default adapter: assumes standard SQL support. Used for SQLite,
    Postgres, MySQL, and anything else without its own adapter below.
    """

    def prepare_metadata(self, metadata: MetaData) -> None:
        """Adjust a freshly-built MetaData for this target before create_all."""

    def insert_rows(self, conn: Connection, table: Table, rows: Sequence[dict[str, Any]]) -> None:
        """Bulk-insert one batch of rows (scd2 staging load)."""
        conn.execute(insert(table), rows)

    def staging_chunk_size(self, default: int) -> int:
        """How many rows to buffer per `insert_rows` call. The default
        (5,000, set by the scd2 apply functions) suits per-statement
        engines; targets whose write cost is dominated by fixed per-call
        overhead rather than row count override this upward.
        """
        return default


class BigQueryAdapter(DialectAdapter):
    def prepare_metadata(self, metadata: MetaData) -> None:
        for table in metadata.tables.values():
            table.indexes.clear()

    def staging_chunk_size(self, default: int) -> int:
        """50,000: a load job costs seconds regardless of row count, so
        bigger batches amortize the fixed cost (and mean FEWER table-update
        operations, i.e. more margin under BigQuery's hard 429 rate limit).
        50,000 keeps the bounded queue's worst-case in-memory footprint
        (3 chunks: 2 queued + 1 in flight) in the low hundreds of MB.
        Measured figures in section 7 of docs/bdns-api-behavior.md.
        """
        return 50_000

    def insert_rows(self, conn: Connection, table: Table, rows: Sequence[dict[str, Any]]) -> None:
        """Load job instead of DML INSERT: ~3-4x faster than batched DML and
        free (load jobs don't count against the query/DML byte quota).
        Measured figures in section 7 of docs/bdns-api-behavior.md.

        Blocks on `.result()` deliberately: BigQuery caps table *update*
        operations (loads count) at a low rate regardless of whether
        earlier ones finished, and unblocked submission trips `429 too
        many table update operations for this table`, a hard platform
        limit (tried live), not a raisable quota. The blocking call is
        what keeps submissions naturally paced under it; it stays.

        Bypasses SQLAlchemy's INSERT compilation and bind processors
        entirely, so payload serialization is done by hand here, reusing
        the staging table's own `payload` column type (`PortableJSON`) so
        the two paths can never drift out of sync with each other.
        """
        from google.cloud import bigquery

        client = conn.connection.driver_connection._client
        table_ref = bigquery.DatasetReference(client.project, conn.engine.url.database).table(table.name)
        payload_type = table.c.payload.type

        json_rows = []
        for row in rows:
            json_row = {
                "_natural_key": row["_natural_key"],
                "_row_hash": row["_row_hash"],
                "payload": payload_type.process_bind_param(row["payload"], None),
            }
            if "_reg_date" in row:
                json_row["_reg_date"] = row["_reg_date"].isoformat()
            json_rows.append(json_row)

        client.load_table_from_json(json_rows, table_ref).result()


_ADAPTERS: dict[str, type[DialectAdapter]] = {
    "bigquery": BigQueryAdapter,
}


def get_adapter(engine: Engine) -> DialectAdapter:
    return _ADAPTERS.get(engine.dialect.name, DialectAdapter)()
