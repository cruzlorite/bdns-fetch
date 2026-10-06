"""Awards, state aid and de minimis aid to legal persons and public bodies
(dataset/sql/20, 22 and 24_*_personas_juridicas.sql), and the checks that guard them (90_checks.sql)."""

import duckdb
import pytest

from tests.dataset.conftest import ROOT, T1, award, make_sync_db, run_steps, version


def columns_of(con, table):
    return {
        name
        for (name,) in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'publish' AND table_name = ?",
            [table],
        ).fetchall()
    }


def checks():
    return (ROOT / "dataset" / "sql" / "90_checks.sql").read_text(encoding="utf-8")


def test_only_legal_persons_and_public_bodies_are_published(built):
    rows = built.execute(
        "SELECT id, nif, nombre, tipoPersona, importe FROM publish.concesiones_personas_juridicas"
    ).fetchall()
    # Award 2 (a natural person) and award 3 (an unrecognised ID) stay out.
    assert [(i, t, n, k, float(a)) for i, t, n, k, a in rows] == [
        (1, "B12345678", "EMPRESA SL", "persona_juridica", 1200.0)
    ]


def test_state_aid_names_lose_their_dash(built):
    rows = built.execute(
        "SELECT idConcesion, nif, nombre, region FROM publish.ayudasestado_personas_juridicas"
    ).fetchall()
    # The natural person (12) stays out; the company's name has no leading dash.
    assert rows == [(11, "B12345678", "EMPRESA SL", "ES615 - Huelva")]


def test_de_minimis_publishes_legal_persons_only(built):
    rows = built.execute(
        "SELECT idConcesion, nif, nombre FROM publish.minimis_personas_juridicas"
    ).fetchall()
    # The community of property (22) is protected like a natural person.
    assert rows == [(21, "G12345678", "ASOCIACION")]


@pytest.mark.parametrize(
    "table",
    [
        "concesiones_personas_juridicas",
        "ayudasestado_personas_juridicas",
        "minimis_personas_juridicas",
    ],
)
def test_columns_that_lead_to_people_are_left_out(built, table):
    columns = columns_of(built, table)
    assert not columns & {"beneficiario", "idPersona", "urlBR"}
    assert {"nif", "nombre", "fechaConcesion", "tipoPersona"} <= columns


def test_a_protected_row_stops_the_build(built):
    built.execute(
        "INSERT INTO publish.concesiones_personas_juridicas (id, nif, tipoPersona) "
        "VALUES (9, '***1234**', 'persona_fisica')"
    )
    with pytest.raises(duckdb.InvalidInputException, match="protected beneficiaries"):
        built.execute(checks())


def test_a_personal_tax_id_anywhere_stops_the_build(built):
    built.execute(
        "INSERT INTO publish.concesiones_personas_juridicas (id, nif, tipoPersona, convocatoria) "
        "VALUES (9, 'B87654321', 'persona_juridica', 'Ayuda nominativa a 12345678Z')"
    )
    with pytest.raises(duckdb.InvalidInputException, match="personal tax ID"):
        built.execute(checks())


def test_a_company_named_with_a_personal_id_goes_to_the_summary(tmp_path):
    named = award(1, "B12345678 NOMBRE APELLIDO APELLIDO 12345678Z SL", 300)
    people = [award(10 + n, f"***{n:04d}** NOMBRE", 100, idPersona=10 + n) for n in range(10)]
    sync_db = make_sync_db(
        tmp_path / "sync.duckdb",
        [version(a["id"], T1, None, True, None, a) for a in [named, *people]],
        [],
        [],
    )
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    con.execute(f"SET VARIABLE output_dir = '{tmp_path}'")
    run_steps(con)  # the checks pass: nothing ID-shaped is published
    assert con.execute(
        "SELECT count(*) FROM publish.concesiones_personas_juridicas"
    ).fetchone() == (0,)
    assert con.execute(
        "SELECT concesiones, beneficiarios FROM publish.concesiones_personas_fisicas"
    ).fetchone() == (11, 11)
