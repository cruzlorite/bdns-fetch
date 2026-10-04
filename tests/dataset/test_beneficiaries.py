"""Beneficiary classification. Every name and ID here is made up, in the
shapes the BDNS uses; none comes from real data."""

import duckdb
import pytest

from bdns.dataset.beneficiaries import BeneficiaryKind, classify, classify_sql, is_protected, split

K = BeneficiaryKind


@pytest.fixture(scope="module")
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


def sql_classify(con, beneficiary):
    query = f"SELECT {classify_sql('b')} FROM (SELECT ?::VARCHAR AS b)"
    return BeneficiaryKind(con.execute(query, [beneficiary]).fetchone()[0])


@pytest.mark.parametrize(
    ("beneficiary", "kind"),
    [
        ("***1234** NOMBRE APELLIDO APELLIDO", K.NATURAL_PERSON),
        ("****1234* NOMBRE APELLIDO", K.NATURAL_PERSON),
        ("*****1234 NOMBRE", K.NATURAL_PERSON),
        ("12345678Z NOMBRE APELLIDO", K.NATURAL_PERSON),
        ("X1234567L NOMBRE APELLIDO", K.NATURAL_PERSON),
        ("L1234567A NOMBRE APELLIDO", K.NATURAL_PERSON),
        ("B12345678 EMPRESA DE EJEMPLO SL", K.LEGAL_PERSON),
        ("G12345678 FUNDACION DE EJEMPLO", K.LEGAL_PERSON),
        ("A1234567J SOCIEDAD ANONIMA", K.LEGAL_PERSON),
        ("b12345678 empresa en minusculas", K.LEGAL_PERSON),
        ("P1234567D AYUNTAMIENTO DE EJEMPLO", K.PUBLIC_BODY),
        ("Q1234567H ORGANISMO DE EJEMPLO", K.PUBLIC_BODY),
        ("S1234567E CONSEJERIA DE EJEMPLO", K.PUBLIC_BODY),
        ("E12345678 APELLIDO Y APELLIDO CB", K.PERSON_BASED_ENTITY),
        ("J12345678 APELLIDO SC", K.PERSON_BASED_ENTITY),
        ("123456789012 FOREIGN COMPANY LTD", K.UNKNOWN),
        ("BE0123456789 SOCIETE ETRANGERE", K.UNKNOWN),
        ("", K.UNKNOWN),
        (None, K.UNKNOWN),
    ],
)
def test_classify_reads_the_leading_tax_id(con, beneficiary, kind):
    # Python and the SQL the build runs must agree on every case.
    assert classify(beneficiary) is kind
    assert sql_classify(con, beneficiary) is kind


@pytest.mark.parametrize(
    ("kind", "protected"),
    [
        (K.NATURAL_PERSON, True),
        (K.PERSON_BASED_ENTITY, True),
        (K.UNKNOWN, True),
        (K.LEGAL_PERSON, False),
        (K.PUBLIC_BODY, False),
    ],
)
def test_only_legal_persons_and_public_bodies_are_unprotected(kind, protected):
    assert is_protected(kind) is protected


@pytest.mark.parametrize(
    "identifier", ["B1234567", "B123456789", "Z12345678", "12345678", "ABC", "?"]
)
def test_any_shape_not_recognised_is_protected(con, identifier):
    # The conservative direction: a near-miss of a company's ID must not
    # pass as a company.
    assert is_protected(classify(f"{identifier} NOMBRE"))
    assert is_protected(sql_classify(con, f"{identifier} NOMBRE"))


def test_the_name_never_changes_the_verdict(con):
    for beneficiary, kind in [
        ("B12345678 12345678Z", K.LEGAL_PERSON),
        ("***1234** EMPRESA SL", K.NATURAL_PERSON),
    ]:
        assert classify(beneficiary) is kind
        assert sql_classify(con, beneficiary) is kind


def test_sql_classifies_a_whole_column(con):
    con.execute("CREATE OR REPLACE TABLE concesiones (beneficiario VARCHAR)")
    con.execute(
        "INSERT INTO concesiones VALUES ('***1234** NOMBRE'), ('B12345678 EMPRESA SL'), (NULL)"
    )
    rows = con.execute(f"SELECT {classify_sql('beneficiario')} AS kind FROM concesiones").fetchall()
    assert [kind for (kind,) in rows] == ["natural_person", "legal_person", "unknown"]


def test_split_separates_identifier_and_name():
    assert split("  B12345678   EMPRESA SL ") == ("B12345678", "EMPRESA SL")
    assert split("B12345678") == ("B12345678", "")
    assert split(None) == ("", "")
