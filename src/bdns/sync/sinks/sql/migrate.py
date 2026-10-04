# SPDX-License-Identifier: MIT

"""Additive schema migration: add the columns an existing table lacks.

The schema only ever grows by nullable columns (see
[ADR 0015](../../../adr/0015-run-linked-versions-additive-migrations.md)), so
bringing an existing target up to date is one `ALTER TABLE ... ADD COLUMN`
per missing column, which SQLite, PostgreSQL, DuckDB and BigQuery all
accept. Nothing is ever renamed, retyped or dropped, which is what keeps
this safe to run unattended at the start of every run: a target written by
an older version is upgraded in place, and existing rows read NULL in the
new columns.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Table

__all__ = ["add_missing_columns"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def add_missing_columns(engine: Engine, tables: list[Table]) -> list[str]:
    """Add to each existing table the nullable columns its definition has and it lacks.

    Tables that do not exist yet are left alone: `create_all` creates them
    whole.

    Args:
        engine: Engine for the target database.
        tables: Current table definitions.

    Returns:
        `table.column` for every column added, for the log.

    Raises:
        ValueError: If a missing column is NOT NULL, which an additive
            migration cannot fill for existing rows.
    """
    inspector = inspect(engine)
    preparer = engine.dialect.identifier_preparer
    added = []
    for table in tables:
        if not inspector.has_table(table.name):
            continue
        present = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue
            if not column.nullable:
                raise ValueError(
                    f"{table.name}.{column.name} is NOT NULL and missing from the target; "
                    f"an additive migration cannot add it"
                )
            column_type = column.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"ALTER TABLE {preparer.format_table(table)} "
                        f"ADD COLUMN {preparer.format_column(column)} {column_type}"
                    )
                )
            added.append(f"{table.name}.{column.name}")
            logger.info("schema: added column %s.%s", table.name, column.name)
    return added
