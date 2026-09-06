# SPDX-License-Identifier: GPL-3.0-or-later

"""Per-engine adapters. The rest of the codebase writes portable SQL (see
scd2.py) that runs unchanged on SQLite, PostgreSQL, and BigQuery.
This module is the only place allowed to know a specific engine's name
and quirks; nothing outside it should branch on `dialect.name`.

BigQuery is a first-class target and, so far, the only one that needs an
adapter, and PostgreSQL needs one only to truncate staging. SQLite is
covered by the DialectAdapter default.

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

from sqlalchemy import MetaData, delete, insert, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql.schema import Table


def _truncate(conn: Connection, table: Table) -> None:
    """`TRUNCATE TABLE`, for engines where it is a metadata operation.

    The table name goes through the dialect's identifier preparer rather
    than into an f-string directly, so quoting is the dialect's business
    and the statement can't be malformed by an unusual name.
    """
    name = conn.engine.dialect.identifier_preparer.format_table(table)
    conn.execute(text(f"TRUNCATE TABLE {name}"))


class DialectAdapter:
    """Default adapter: assumes standard SQL support. Used for SQLite,
    DuckDB, and anything else without its own adapter below.
    """

    def prepare_metadata(self, metadata: MetaData) -> None:
        """Adjust a freshly-built MetaData for this target before create_all."""

    def insert_rows(self, conn: Connection, table: Table, rows: Sequence[dict[str, Any]]) -> None:
        """Bulk-insert one batch of rows (scd2 staging load)."""
        conn.execute(insert(table), rows)

    def clear_table(self, conn: Connection, table: Table) -> None:
        """Empty the staging table, at the start and end of every run.

        `DELETE` is the portable default and is what SQLite and
        DuckDB want: a `DELETE` with no `WHERE` already takes SQLite's
        truncate shortcut, and neither engine bills by the byte. Only
        engines where `TRUNCATE` is both transactional and materially
        cheaper override this.
        """
        conn.execute(delete(table))

    def staging_chunk_size(self, default: int) -> int:
        """How many rows to buffer per `insert_rows` call. The default
        (5,000, set by the scd2 apply functions) suits per-statement
        engines; targets whose write cost is dominated by fixed per-call
        overhead rather than row count override this upward.
        """
        return default


class PostgresAdapter(DialectAdapter):
    def clear_table(self, conn: Connection, table: Table) -> None:
        """`TRUNCATE` instead of `DELETE`: Postgres' `DELETE` leaves one
        dead tuple per row for VACUUM to reclaim later, which on a
        staging table holding millions of rows is real work deferred onto
        the next autovacuum. `TRUNCATE` is transactional here, so it
        rolls back with the rest of the run if the run fails.
        """
        _truncate(conn, table)


class BigQueryAdapter(DialectAdapter):
    def prepare_metadata(self, metadata: MetaData) -> None:
        for table in metadata.tables.values():
            table.indexes.clear()

    def clear_table(self, conn: Connection, table: Table) -> None:
        """`TRUNCATE` instead of `DELETE`: on BigQuery a `DELETE` is DML
        and scans the table, so emptying staging is billed by the byte.
        Measured on the annual concesiones_busqueda run of 1 September
        2026: 17.2 GB scanned per `DELETE`, twice per run, out of 91 GB
        for the whole diff. `TRUNCATE TABLE` is a metadata operation:
        no bytes scanned, no cost.
        """
        _truncate(conn, table)

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
    "postgresql": PostgresAdapter,
}


def get_adapter(engine: Engine) -> DialectAdapter:
    return _ADAPTERS.get(engine.dialect.name, DialectAdapter)()
