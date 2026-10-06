"""What keeps the build honest without anyone having to remember it: the
checks find the published tables by themselves (90_checks.sql), the export
fails if a published table has no file (95_export.sql), and fields the API
stops sending are reported (80_schema_drift.sql)."""

import datetime

import duckdb
import pytest

from tests.dataset.conftest import ROOT, T1, make_sync_db, run_steps, version

SQL = ROOT / "dataset" / "sql"


def step(name):
    return (SQL / name).read_text(encoding="utf-8")


def test_a_table_nobody_listed_is_checked_too(built):
    built.execute("CREATE TABLE publish.nueva AS SELECT 'Ayuda nominativa a 12345678Z' AS texto")
    with pytest.raises(
        duckdb.InvalidInputException, match=r"publish\.nueva: 1 rows with something shaped"
    ):
        built.execute(step("90_checks.sql"))


def test_a_new_summary_is_recognised_by_its_columns(built):
    built.execute(
        "CREATE TABLE publish.otro_resumen AS SELECT 3 AS beneficiarios, 100 AS importeTotal"
    )
    with pytest.raises(
        duckdb.InvalidInputException, match=r"publish\.otro_resumen: 1 rows below 10"
    ):
        built.execute(step("90_checks.sql"))


def test_a_published_table_without_its_copy_line_stops_the_export(built):
    built.execute("CREATE TABLE publish.sin_exportar AS SELECT 1 AS x")
    with pytest.raises(
        duckdb.InvalidInputException, match="Published but not exported.*sin_exportar"
    ):
        built.execute(step("95_export.sql"))


def plan(id_pes, **fields):
    return {
        "idPES": id_pes,
        "descripcion": f"Plan {id_pes}",
        "vigenciaDesde": 2026,
        "vigenciaHasta": 2028,
        **fields,
    }


def test_a_field_the_api_stops_sending_is_reported(tmp_path):
    # The older plan has tipoPlan; the API then renamed it in the newer one.
    old = version(1, T1, None, True, None, plan(1, tipoPlan="Ministerial"))
    new = version(
        2, T1 + datetime.timedelta(days=200), None, True, None, plan(2, tipoDePlan="Ministerial")
    )
    sync_db = make_sync_db(tmp_path / "sync.duckdb", [], [], [], planesestrategicos=[old, new])
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    run_steps(con, {p.name for p in SQL.iterdir()} - {"90_checks.sql", "95_export.sql"})
    empty = con.execute(
        "SELECT campo FROM campos_vacios WHERE tabla = 'planesestrategicos' ORDER BY campo"
    ).fetchall()
    assert ("tipoPlan",) in empty
    # Fields that keep coming are not reported.
    assert ("descripcion",) not in empty
