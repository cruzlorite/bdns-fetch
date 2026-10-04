"""Awards, state aid and de minimis aid to legal persons and public bodies
(dataset/sql/20_entidades.sql), and the checks that guard them (90_checks.sql)."""

import duckdb
import pytest

from tests.dataset.conftest import ROOT


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
        "SELECT id, nif, nombre, tipo_persona, importe FROM publish.concesiones_entidades"
    ).fetchall()
    # Award 2 (a natural person) and award 3 (an unrecognised ID) stay out.
    assert [(i, t, n, k, float(a)) for i, t, n, k, a in rows] == [
        (1, "B12345678", "EMPRESA SL", "persona_juridica", 1200.0)
    ]


def test_state_aid_names_lose_their_dash(built):
    rows = built.execute(
        "SELECT id_concesion, nif, nombre, region FROM publish.ayudas_estado_entidades"
    ).fetchall()
    # The natural person (12) stays out; the company's name has no leading dash.
    assert rows == [(11, "B12345678", "EMPRESA SL", "ES615 - Huelva")]


def test_de_minimis_publishes_legal_persons_only(built):
    rows = built.execute(
        "SELECT id_concesion, nif, nombre FROM publish.minimis_entidades"
    ).fetchall()
    # The community of property (22) is protected like a natural person.
    assert rows == [(21, "G12345678", "ASOCIACION")]


@pytest.mark.parametrize(
    "table", ["concesiones_entidades", "ayudas_estado_entidades", "minimis_entidades"]
)
def test_columns_that_lead_to_people_are_left_out(built, table):
    columns = columns_of(built, table)
    assert not columns & {"beneficiario", "id_persona", "url_br"}
    assert {"nif", "nombre", "fecha_concesion", "tipo_persona"} <= columns


def test_a_protected_row_stops_the_build(built):
    built.execute(
        "INSERT INTO publish.concesiones_entidades (id, nif, tipo_persona) "
        "VALUES (9, '***1234**', 'persona_fisica')"
    )
    with pytest.raises(duckdb.InvalidInputException, match="protected beneficiaries"):
        built.execute(checks())


def test_a_personal_tax_id_anywhere_stops_the_build(built):
    built.execute(
        "INSERT INTO publish.concesiones_entidades (id, nif, tipo_persona, convocatoria) "
        "VALUES (9, 'B87654321', 'persona_juridica', 'Ayuda nominativa a 12345678Z')"
    )
    with pytest.raises(duckdb.InvalidInputException, match="personal tax ID"):
        built.execute(checks())
