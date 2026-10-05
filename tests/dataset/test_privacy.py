"""Privacy building blocks (dataset/sql/02_privacy.sql). Every ID here is made up."""

import duckdb
import pytest


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("Ayuda a ***1234** para obras", True),
        ("Subvención nominativa a 12345678Z", True),
        ("beneficiario X1234567L", True),
        ("residente L1234567A", True),
        ("Empresa B12345678 y ayuntamiento P1234567D", False),
        ("Convocatoria 2026 de ayudas por 12.345.678 euros", False),
        (None, False),
    ],
)
def test_has_personal_id(macros, text, found):
    assert macros.execute("SELECT has_personal_id(?::VARCHAR)", [text]).fetchone()[0] is found


def test_rows_with_personal_ids_scans_every_column(macros):
    macros.execute("CREATE TABLE t (titulo VARCHAR, importe DECIMAL(18, 2), nota VARCHAR)")
    macros.execute(
        "INSERT INTO t VALUES ('Ayudas 2026', 10, NULL), ('Ayudas', 20, 'a 12345678Z'), (NULL, 30, NULL)"
    )
    rows = macros.execute("SELECT importe FROM rows_with_personal_ids('t')").fetchall()
    assert [float(r) for (r,) in rows] == [20.0]


def test_two_columns_never_form_one_match(macros):
    macros.execute("CREATE TABLE t (a VARCHAR, b VARCHAR)")
    macros.execute("INSERT INTO t VALUES ('1234567', '8Z')")
    assert macros.execute("SELECT count(*) FROM rows_with_personal_ids('t')").fetchone() == (0,)


@pytest.mark.parametrize(
    ("name", "identifying"),
    [
        ("beneficiario", True),
        ("idPersona", True),
        ("urlBR", True),
        ("id_persona", True),
        ("url_br", True),
        ("cod_concesion", True),
        ("nif", True),
        ("NOMBRE", True),
        # Counts and summaries of people are what may be published.
        ("beneficiarios", False),
        ("importe_total", False),
        ("convocatoria", False),
    ],
)
def test_identifying_column(macros, name, identifying):
    assert macros.execute("SELECT identifying_column(?)", [name]).fetchone()[0] is identifying


def test_a_check_stops_the_build_only_when_it_finds_something(macros):
    # The shape every check in 90_checks.sql takes.
    macros.execute("CREATE TABLE t (titulo VARCHAR)")
    check = "SELECT CASE WHEN count(*) > 0 THEN error('personal data in t') END FROM rows_with_personal_ids('t')"
    macros.execute(check)
    macros.execute("INSERT INTO t VALUES ('Ayuda a ***1234**')")
    with pytest.raises(duckdb.InvalidInputException, match="personal data in t"):
        macros.execute(check)


@pytest.mark.parametrize(
    ("kind", "beneficiary", "protected"),
    [
        ("persona_juridica", "B12345678 EMPRESA DE EJEMPLO SL", False),
        ("entidad_publica", "P1234567D AYUNTAMIENTO DE EJEMPLO", False),
        # A company named after its partner, or carrying its representative.
        ("persona_juridica", "B12345678 NOMBRE APELLIDO APELLIDO 12345678Z SL", True),
        ("persona_juridica", "G12345678 ASOCIACION DE EJEMPLO REPRESENTANTE: 12345678Z", True),
        ("persona_fisica", "***1234** NOMBRE APELLIDO", True),
    ],
)
def test_a_personal_id_in_the_name_protects_a_company(macros, kind, beneficiary, protected):
    assert (
        macros.execute("SELECT is_protected_beneficiary(?, ?)", [kind, beneficiary]).fetchone()[0]
        is protected
    )
