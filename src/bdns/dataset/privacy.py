# SPDX-License-Identifier: MIT

"""Checks that stop the dataset build before personal data can be published.

They run as SQL on each table about to be written, never on the source,
and they fail instead of cleaning up: [`check_table`][] raises
[`PrivacyViolation`][] listing what tripped it. A check that quietly
dropped what it found would hide the real fault upstream (a classification
that let a person through, a column that should never have been selected)
behind a dataset that looks fine. What the checks enforce, and why, is in
[the dataset decision](../../../adr/0002-anonymised-dataset.md).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb

__all__ = [
    "FORBIDDEN_FIELDS",
    "PERSONAL_ID_PATTERN",
    "PrivacyViolation",
    "check_table",
    "find_personal_ids",
]

FORBIDDEN_FIELDS = frozenset({"beneficiario", "nifCif", "idPersona", "urlBR", "codConcesion", "id"})
"""Fields that identify a beneficiary, or lead back to one: never published
in anything about natural persons."""

PERSONAL_ID_PATTERN = (
    r"\*{2,}\d{3,5}\*{0,3}"
    r"|\b\d{8}[A-Za-z]\b"
    r"|\b[XYZxyz]\d{7}[A-Za-z]\b"
    r"|\b[KLMklm]\d{7}[A-Za-z0-9]\b"
)
"""A natural person's tax ID anywhere in a text: masked (`***1234**`), a DNI,
an NIE or a K/L/M one. A legal person's ID (`B12345678`) matches none of
them. Written in the regex syntax Python and DuckDB share."""

_PERSONAL_ID = re.compile(PERSONAL_ID_PATTERN)


class PrivacyViolation(Exception):
    """What is about to be published could reveal a natural person.

    Attributes:
        problems: One line per finding, saying where it is.
    """

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(f"{len(problems)} privacy problem(s):\n" + "\n".join(problems))


def find_personal_ids(text: str) -> list[str]:
    """Return every substring of `text` shaped like a natural person's tax ID."""
    return _PERSONAL_ID.findall(text)


def check_table(
    con: duckdb.DuckDBPyConnection,
    table: str,
    *,
    count_column: str | None = None,
    k: int | None = None,
    forbidden: frozenset[str] = FORBIDDEN_FIELDS,
    limit: int = 20,
) -> None:
    """Fail if a table about to be published could reveal a natural person.

    Three checks, all in SQL: no forbidden column; no text value shaped
    like a natural person's tax ID; and, for an aggregated table, no cell
    counting fewer than `k` beneficiaries. A suppressed cell carries NULL in
    `count_column` and passes; so does a cell counting nobody.

    Args:
        con: An open DuckDB connection holding the table.
        table: The table's name.
        count_column: For an aggregated table, the column holding each
            cell's number of beneficiaries.
        k: The smallest number a published cell may count.
        forbidden: Column names that may not appear.
        limit: How many findings to list per check.

    Raises:
        PrivacyViolation: Naming each forbidden column, each tax-ID-shaped
            value (with its column) and each cell below `k`.
    """
    quoted = '"' + table.replace('"', '""') + '"'
    columns = con.execute(f"DESCRIBE {quoted}").fetchall()
    problems = [f"{table}: forbidden column {name}" for name, *_ in columns if name in forbidden]

    for name, column_type, *_ in columns:
        if column_type != "VARCHAR":
            continue
        column = '"' + name.replace('"', '""') + '"'
        rows = con.execute(
            f"SELECT {column} FROM {quoted} WHERE regexp_matches({column}, ?) LIMIT ?",
            [PERSONAL_ID_PATTERN, limit],
        ).fetchall()
        for (value,) in rows:
            problems.append(f"{table}.{name}: {find_personal_ids(value)[0]!r}")

    if count_column is not None and k is not None:
        column = '"' + count_column.replace('"', '""') + '"'
        rows = con.execute(
            f"SELECT {column} FROM {quoted} WHERE {column} > 0 AND {column} < ? LIMIT ?",
            [k, limit],
        ).fetchall()
        problems += [
            f"{table}: a cell counts {count} beneficiaries, below {k}" for (count,) in rows
        ]

    if problems:
        raise PrivacyViolation(problems)
