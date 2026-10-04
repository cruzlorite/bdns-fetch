"""Beneficiary classification, run as the build runs it: the SQL macro in
DuckDB. Every name and ID here is made up, in the shapes the BDNS uses."""

import duckdb
import pytest

from bdns.dataset.beneficiaries import BeneficiaryKind, is_protected
from bdns.dataset.build import run_sql

K = BeneficiaryKind


@pytest.fixture(scope="module")
def con():
    connection = duckdb.connect()
    run_sql(connection, "00_beneficiaries.sql")
    yield connection
    connection.close()


def kind_of(con, beneficiary):
    return BeneficiaryKind(
        con.execute("SELECT beneficiary_kind(?::VARCHAR)", [beneficiary]).fetchone()[0]
    )


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
        ("  B12345678   ESPACIOS DE MAS  ", K.LEGAL_PERSON),
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
def test_classification_reads_the_leading_tax_id(con, beneficiary, kind):
    assert kind_of(con, beneficiary) is kind


@pytest.mark.parametrize(
    "identifier", ["B1234567", "B123456789", "Z12345678", "12345678", "ABC", "?"]
)
def test_any_shape_not_recognised_is_protected(con, identifier):
    # The conservative direction: a near-miss of a company's ID must not
    # pass as a company.
    assert is_protected(kind_of(con, f"{identifier} NOMBRE"))


def test_the_name_never_changes_the_verdict(con):
    assert kind_of(con, "B12345678 12345678Z") is K.LEGAL_PERSON
    assert kind_of(con, "***1234** EMPRESA SL") is K.NATURAL_PERSON


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
def test_only_legal_persons_and_public_bodies_are_unprotected(con, kind, protected):
    assert is_protected(kind) is protected
    # The SQL macro agrees with the Python one.
    assert con.execute("SELECT is_protected(?)", [kind.value]).fetchone()[0] is protected
