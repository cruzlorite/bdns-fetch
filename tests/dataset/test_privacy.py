"""Privacy checks, run as SQL on DuckDB tables. Every ID here is made up."""

import duckdb
import pytest

from bdns.dataset.privacy import (
    FORBIDDEN_FIELDS,
    PERSONAL_ID_PATTERN,
    PrivacyViolation,
    check_table,
    find_personal_ids,
)


@pytest.fixture
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("Ayuda a ***1234** para obras", ["***1234**"]),
        ("Subvención nominativa a 12345678Z", ["12345678Z"]),
        ("beneficiario X1234567L y Y7654321M", ["X1234567L", "Y7654321M"]),
        ("residente L1234567A", ["L1234567A"]),
        ("Empresa B12345678 y ayuntamiento P1234567D", []),
        ("Convocatoria 2026 de ayudas por 12.345.678 euros", []),
    ],
)
def test_find_personal_ids(con, text, found):
    assert find_personal_ids(text) == found
    # DuckDB, which runs the check on whole tables, must see the same thing.
    matches = con.execute("SELECT regexp_matches(?, ?)", [text, PERSONAL_ID_PATTERN]).fetchone()[0]
    assert matches is bool(found)


def test_a_clean_table_passes(con):
    con.execute(
        "CREATE TABLE agregados (anio INTEGER, organo VARCHAR, beneficiarios INTEGER, importe DOUBLE)"
    )
    con.execute("INSERT INTO agregados VALUES (2026, 'Ayuntamiento de Ejemplo', 25, 1000.0)")
    check_table(con, "agregados", count_column="beneficiarios", k=10)


def test_a_personal_id_stops_the_build_naming_where_it_is(con):
    con.execute("CREATE TABLE convocatorias (titulo VARCHAR, importe DOUBLE)")
    con.execute("INSERT INTO convocatorias VALUES ('Ayudas 2026', 10), ('Ayuda a 12345678Z', 50)")
    with pytest.raises(PrivacyViolation) as caught:
        check_table(con, "convocatorias")
    assert caught.value.problems == ["convocatorias.titulo: '12345678Z'"]


def test_forbidden_columns_are_named(con):
    con.execute('CREATE TABLE t (anio INTEGER, "idPersona" BIGINT, "urlBR" VARCHAR)')
    with pytest.raises(PrivacyViolation) as caught:
        check_table(con, "t")
    assert caught.value.problems == ["t: forbidden column idPersona", "t: forbidden column urlBR"]
    assert "beneficiario" in FORBIDDEN_FIELDS


def test_cells_below_k_are_named_and_suppressed_cells_pass(con):
    con.execute("CREATE TABLE agregados (convocatoria VARCHAR, beneficiarios INTEGER)")
    con.execute(
        "INSERT INTO agregados VALUES ('A', 25), ('B', 3), ('C', NULL), ('D', 0), ('E', 10)"
    )
    with pytest.raises(PrivacyViolation) as caught:
        check_table(con, "agregados", count_column="beneficiarios", k=10)
    assert caught.value.problems == ["agregados: a cell counts 3 beneficiaries, below 10"]


def test_findings_are_capped_per_check(con):
    con.execute("CREATE TABLE t (titulo VARCHAR)")
    con.execute("INSERT INTO t SELECT printf('***%04d**', i) FROM range(50) r(i)")
    with pytest.raises(PrivacyViolation) as caught:
        check_table(con, "t", limit=5)
    assert len(caught.value.problems) == 5
