# SPDX-License-Identifier: MIT

"""Run the dataset's SQL, one file after another, in a DuckDB connection.

The transforms are plain SQL files in `bdns/dataset/sql/`, run in the order
of their names (`00_beneficiaries.sql`, `10_concesiones.sql`...), so the
method can be read, reviewed and rerun as it is. Python only moves data in
([`bdns.dataset.extract`][]) and checks what goes out
([`bdns.dataset.privacy`][]).
"""

from __future__ import annotations

from importlib.resources import files
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb

__all__ = ["run_sql", "sql_files"]


def sql_files() -> list[str]:
    """Return the names of the SQL files, in the order they run."""
    folder = files("bdns.dataset") / "sql"
    return sorted(entry.name for entry in folder.iterdir() if entry.name.endswith(".sql"))


def run_sql(con: duckdb.DuckDBPyConnection, name: str) -> None:
    """Run one of the dataset's SQL files.

    Args:
        con: The private DuckDB connection.
        name: The file's name, such as `10_concesiones.sql`.
    """
    con.execute((files("bdns.dataset") / "sql" / name).read_text(encoding="utf-8"))
