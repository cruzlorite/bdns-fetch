# SPDX-License-Identifier: GPL-3.0-or-later

"""Per-engine adapters, the only code allowed to branch on dialect name.

The rest of the codebase writes portable SQL (see scd2.py) that runs
unchanged on SQLite, PostgreSQL, and BigQuery. This module is the only
place allowed to know a specific engine's name and quirks.

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

__all__ = [
    "BigQueryAdapter",
    "DialectAdapter",
    "PostgresAdapter",
    "get_adapter",
    "staging_json_rows",
]


def staging_json_rows(table: Table, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn staged rows into the JSON records a BigQuery load job takes.

    Separate from `BigQueryAdapter.insert_rows` so it can be tested
    without the google-cloud stack: this is the part that can quietly go
    wrong, since it bypasses SQLAlchemy's bind processors and hand-builds
    what lands in the table.

    Args:
        table: The staging table, whose `payload` column type does the
            serializing, so this path and the ordinary INSERT path can
            never drift apart.
        rows: Staged rows, as built by scd2.

    Returns:
        One JSON-compatible dict per row. `_reg_date` is omitted rather
        than sent as null when the entity has none, and dates go as ISO
        strings, which is what a load job expects.
    """
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
    return json_rows


def _truncate(conn: Connection, table: Table) -> None:
    """Empty `table` with `TRUNCATE TABLE`.

    For engines where truncation is a metadata operation rather than
    row-by-row DML. The table name goes through the dialect's identifier preparer rather
    than into an f-string directly, so quoting is the dialect's business
    and the statement can't be malformed by an unusual name.
    """
    name = conn.engine.dialect.identifier_preparer.format_table(table)
    conn.execute(text(f"TRUNCATE TABLE {name}"))


class DialectAdapter:
    """Default adapter, assuming standard SQL support.

    Used for SQLite, DuckDB, and anything else without its own adapter
    below. Each method has a portable default, so a subclass overrides
    only the ones its engine actually differs on.
    """

    def prepare_metadata(self, metadata: MetaData) -> None:
        """Adjust a freshly-built MetaData for this target before create_all."""

    def insert_rows(self, conn: Connection, table: Table, rows: Sequence[dict[str, Any]]) -> None:
        """Bulk-insert one batch of rows, the scd2 staging load.

        Args:
            conn: Open connection, inside the run's transaction.
            table: The staging table.
            rows: The batch to insert.
        """
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
        """Return how many rows to buffer per `insert_rows` call.

        Args:
            default: The caller's value, set by the scd2 apply functions.
                Suits per-statement engines.

        Returns:
            `default` unchanged. Targets whose write cost is dominated by
            fixed per-call overhead rather than row count override this
            upward.
        """
        return default


class PostgresAdapter(DialectAdapter):
    """PostgreSQL. Differs from the default only in how staging is emptied."""

    def clear_table(self, conn: Connection, table: Table) -> None:
        """Empty the staging table with `TRUNCATE` rather than `DELETE`.

        Postgres' `DELETE` leaves one dead tuple per row for VACUUM to
        reclaim later, which on a staging table holding millions of rows
        is real work deferred onto the next autovacuum. `TRUNCATE` is
        transactional here, so it rolls back with the rest of the run.
        """
        _truncate(conn, table)


class BigQueryAdapter(DialectAdapter):
    """BigQuery. Overrides every method: it differs on all of them."""

    def prepare_metadata(self, metadata: MetaData) -> None:
        """Strip indexes, which BigQuery has no equivalent for and rejects.

        Pruning is handled by the clustering fields declared in schema.py
        instead.
        """
        for table in metadata.tables.values():
            table.indexes.clear()

    def clear_table(self, conn: Connection, table: Table) -> None:
        """Empty the staging table with `TRUNCATE` rather than `DELETE`.

        On BigQuery a `DELETE` is DML and scans the table, so emptying
        staging is billed by the byte. Measured on the annual
        concesiones_busqueda run of 1 September 2026: 17.2 GB scanned per
        `DELETE`, twice per run, out of 91 GB for the whole diff.
        `TRUNCATE TABLE` is a metadata operation: no bytes scanned, no
        cost.
        """
        _truncate(conn, table)

    def staging_chunk_size(self, default: int) -> int:
        """Return 50,000, ignoring the caller's default.

        A load job costs seconds regardless of row count, so bigger
        batches amortize the fixed cost and mean fewer table-update
        operations, which is more margin under BigQuery's hard 429 rate
        limit. 50,000 keeps the bounded queue's worst-case in-memory
        footprint (three chunks: two queued, one in flight) in the low
        hundreds of MB. Measured figures in
        docs/explanation/bdns-api-behavior.md#performance.

        Args:
            default: The caller's value, ignored here.

        Returns:
            50,000.
        """
        return 50_000

    def insert_rows(self, conn: Connection, table: Table, rows: Sequence[dict[str, Any]]) -> None:
        """Bulk-insert one batch with a load job instead of a DML INSERT.

        Load jobs are roughly 3-4x faster than batched DML and free: they
        do not count against the query/DML byte quota. Measured figures
        in docs/explanation/bdns-api-behavior.md#performance.

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

        Args:
            conn: Open connection, used to reach the BigQuery client.
            table: The staging table.
            rows: The batch to load.
        """
        from google.cloud import bigquery

        client = conn.connection.driver_connection._client
        table_ref = bigquery.DatasetReference(client.project, conn.engine.url.database).table(table.name)
        client.load_table_from_json(staging_json_rows(table, rows), table_ref).result()


_ADAPTERS: dict[str, type[DialectAdapter]] = {
    "bigquery": BigQueryAdapter,
    "postgresql": PostgresAdapter,
}


def get_adapter(engine: Engine) -> DialectAdapter:
    """Return the adapter for `engine`'s dialect.

    Args:
        engine: The target engine.

    Returns:
        A new adapter instance. `DialectAdapter` for any dialect without
        a registered one, which is the portable default rather than an
        error: an unknown engine works if its SQL is standard.
    """
    return _ADAPTERS.get(engine.dialect.name, DialectAdapter)()
