"""The Parquet export (dataset/sql/95_export.sql)."""

import re

import duckdb
import pytest

from tests.dataset.conftest import ROOT

EXPORT = ROOT / "dataset" / "sql" / "95_export.sql"


def test_each_published_table_becomes_a_parquet_file(built, output):
    published = built.execute("SELECT count(*) FROM publicar.concesiones_entidades").fetchone()
    exported = built.execute(
        "SELECT count(*) FROM read_parquet(?)", [str(output / "concesiones_entidades.parquet")]
    ).fetchone()
    assert exported == published


def test_every_published_table_has_its_export_line(built):
    tables = {
        name
        for (name,) in built.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'publicar'"
        ).fetchall()
    }
    exported = set(re.findall(r"COPY publicar\.(\w+)", EXPORT.read_text(encoding="utf-8")))
    assert tables == exported


def test_nothing_private_is_exported():
    assert set(re.findall(r"COPY (\w+)\.", EXPORT.read_text(encoding="utf-8"))) == {"publicar"}


def test_without_an_output_folder_the_export_says_what_to_do(built):
    built.execute("RESET VARIABLE salida")
    with pytest.raises(duckdb.InvalidInputException, match="SET VARIABLE salida"):
        built.execute(EXPORT.read_text(encoding="utf-8"))
