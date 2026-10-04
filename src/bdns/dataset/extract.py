# SPDX-License-Identifier: MIT

"""Copy the last known version of every record from bdns-sync's tables into DuckDB.

The last known version of a key is its current one or, for a key the API
stopped serving, the one closed as `removed`: its newest version either
way. That is what makes the history worth publishing, since keys the
portal withdrew keep their last content.

The source is any database bdns-sync writes to, read through SQLAlchemy
with portable SQL (a window function, which SQLite, PostgreSQL, DuckDB and
BigQuery all support); everything after this step runs in DuckDB. The
copy holds personal data, so the DuckDB file it lands in must stay private
([why](../../../adr/0002-anonymised-dataset.md)).

Rows travel in batches through a newline-delimited JSON file that DuckDB
reads in one go. `payload` is read as the text bdns-sync stored and
written into the file untouched, so it is never parsed in Python.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import MetaData, Select, Text, func, select, type_coerce

from bdns.sync.sinks.sql.schema import build_sync_table

if TYPE_CHECKING:
    import duckdb
    from sqlalchemy import Engine, Table

__all__ = ["RAW_PREFIX", "extract_table", "latest_versions"]

RAW_PREFIX = "raw_"
"""Prefix of the DuckDB table each source table is copied to (`raw_concesiones_busqueda`...)."""

_COLUMNS = {
    "natural_key": "VARCHAR",
    "valid_from": "TIMESTAMPTZ",
    "valid_to": "TIMESTAMPTZ",
    "is_current": "BOOLEAN",
    "closed_reason": "VARCHAR",
    "reg_date": "DATE",
    "payload": "JSON",
}


def latest_versions(table: Table) -> Select:
    """Build the query for each key's newest version in a bdns-sync table.

    Args:
        table: The entity table, as bdns-sync defines it.

    Returns:
        A `SELECT` with one row per natural key, `payload` as raw text.
    """
    ranked = select(
        table.c._natural_key.label("natural_key"),
        table.c._valid_from.label("valid_from"),
        table.c._valid_to.label("valid_to"),
        table.c._is_current.label("is_current"),
        table.c._closed_reason.label("closed_reason"),
        table.c._reg_date.label("reg_date"),
        type_coerce(table.c.payload, Text).label("payload"),
        func.row_number()
        .over(partition_by=table.c._natural_key, order_by=table.c._valid_from.desc())
        .label("rank"),
    ).subquery()
    return select(*(ranked.c[name] for name in _COLUMNS)).where(ranked.c.rank == 1)


def _json_line(row) -> str:
    """Write one row as a JSON line, splicing in the payload text as it is."""
    fields = {
        "natural_key": row.natural_key,
        "valid_from": row.valid_from.isoformat() if row.valid_from else None,
        "valid_to": row.valid_to.isoformat() if row.valid_to else None,
        "is_current": row.is_current,
        "closed_reason": row.closed_reason,
        "reg_date": row.reg_date.isoformat() if row.reg_date else None,
    }
    head = json.dumps(fields, ensure_ascii=False)[:-1]
    return f'{head}, "payload": {row.payload if row.payload is not None else "null"}}}\n'


def extract_table(
    engine: Engine, con: duckdb.DuckDBPyConnection, name: str, *, batch_size: int = 50_000
) -> int:
    """Copy one bdns-sync table's last known versions into DuckDB.

    The DuckDB table, `raw_<name>`, is replaced if it already exists, so a
    build always starts from the source's current state.

    Args:
        engine: The bdns-sync database.
        con: The private DuckDB connection to copy into.
        name: The entity table, such as `concesiones_busqueda`.
        batch_size: Rows per batch.

    Returns:
        How many keys were copied.
    """
    target = f'"{RAW_PREFIX}{name}"'
    columns = ", ".join(f'"{column}" {kind}' for column, kind in _COLUMNS.items())
    con.execute(f"CREATE OR REPLACE TABLE {target} ({columns})")
    spec = "{" + ", ".join(f"'{column}': '{kind}'" for column, kind in _COLUMNS.items()) + "}"
    table = build_sync_table(name, MetaData())
    copied = 0
    with tempfile.TemporaryDirectory() as scratch, engine.connect() as source:
        batch_file = Path(scratch) / "batch.jsonl"
        result = source.execution_options(stream_results=True).execute(latest_versions(table))
        for rows in result.partitions(batch_size):
            batch_file.write_text("".join(_json_line(row) for row in rows), encoding="utf-8")
            con.execute(
                f"INSERT INTO {target} SELECT * FROM read_json(?, format = 'newline_delimited', columns = {spec})",
                [str(batch_file)],
            )
            copied += len(rows)
    return copied
