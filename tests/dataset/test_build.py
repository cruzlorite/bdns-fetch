"""The SQL pipeline, end to end on a small bdns-sync table."""

import duckdb

from bdns.dataset.build import run_sql, sql_files
from bdns.dataset.extract import extract_table
from tests.dataset.test_extract import source  # noqa: F401  (the fixture)


def test_sql_files_run_in_name_order():
    names = sql_files()
    assert names == sorted(names)
    assert names[:2] == ["00_beneficiaries.sql", "10_concesiones.sql"]


def test_awards_get_typed_columns_and_a_beneficiary_kind(source):  # noqa: F811
    con = duckdb.connect()
    extract_table(source, con, "concesiones_busqueda")
    for name in sql_files():
        run_sql(con, name)
    rows = con.execute(
        "SELECT id, importe, tipo_beneficiario, retirada FROM concesiones ORDER BY id"
    ).fetchall()
    con.close()
    # The fixture's payloads carry no beneficiary, so all are 'unknown':
    # protected by default. Award 3's last version is closed (written before
    # closing reasons existed), so it counts as withdrawn too.
    assert [(i, float(m), k, r) for i, m, k, r in rows] == [
        (1, 1200.0, "unknown", False),
        (2, 500.0, "unknown", True),
        (3, 80.0, "unknown", True),
    ]
