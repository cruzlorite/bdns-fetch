"""Beneficiary classification (dataset/sql/01_beneficiaries.sql). Every name
and ID here is made up, in the shapes the BDNS uses."""

import pytest

PROTECTED = {"natural_person", "person_based_entity", "unknown"}


def kind_of(con, beneficiary):
    return con.execute("SELECT beneficiary_kind(?::VARCHAR)", [beneficiary]).fetchone()[0]


@pytest.mark.parametrize(
    ("beneficiary", "kind"),
    [
        ("***1234** NOMBRE APELLIDO APELLIDO", "natural_person"),
        ("****1234* NOMBRE APELLIDO", "natural_person"),
        ("*****1234 NOMBRE", "natural_person"),
        ("12345678Z NOMBRE APELLIDO", "natural_person"),
        ("X1234567L NOMBRE APELLIDO", "natural_person"),
        ("L1234567A NOMBRE APELLIDO", "natural_person"),
        ("B12345678 EMPRESA DE EJEMPLO SL", "legal_person"),
        ("G12345678 FUNDACION DE EJEMPLO", "legal_person"),
        ("A1234567J SOCIEDAD ANONIMA", "legal_person"),
        ("b12345678 empresa en minusculas", "legal_person"),
        ("  B12345678   ESPACIOS DE MAS  ", "legal_person"),
        ("P1234567D AYUNTAMIENTO DE EJEMPLO", "public_body"),
        ("Q1234567H ORGANISMO DE EJEMPLO", "public_body"),
        ("S1234567E CONSEJERIA DE EJEMPLO", "public_body"),
        ("E12345678 APELLIDO Y APELLIDO CB", "person_based_entity"),
        ("J12345678 APELLIDO SC", "person_based_entity"),
        ("123456789012 FOREIGN COMPANY LTD", "unknown"),
        ("BE0123456789 SOCIETE ETRANGERE", "unknown"),
        ("", "unknown"),
        (None, "unknown"),
    ],
)
def test_classification_reads_the_leading_tax_id(macros, beneficiary, kind):
    assert kind_of(macros, beneficiary) == kind


@pytest.mark.parametrize(
    "identifier", ["B1234567", "B123456789", "Z12345678", "12345678", "ABC", "?"]
)
def test_any_shape_not_recognised_is_protected(macros, identifier):
    # The conservative direction: a near-miss of a company's ID must not
    # pass as a company.
    assert kind_of(macros, f"{identifier} NOMBRE") in PROTECTED


def test_the_name_never_changes_the_verdict(macros):
    assert kind_of(macros, "B12345678 12345678Z") == "legal_person"
    assert kind_of(macros, "***1234** EMPRESA SL") == "natural_person"


@pytest.mark.parametrize(
    ("kind", "protected"),
    [
        ("natural_person", True),
        ("person_based_entity", True),
        ("unknown", True),
        ("legal_person", False),
        ("public_body", False),
    ],
)
def test_only_legal_persons_and_public_bodies_are_unprotected(macros, kind, protected):
    assert macros.execute("SELECT is_protected(?)", [kind]).fetchone()[0] is protected


@pytest.mark.parametrize(
    ("beneficiary", "name"),
    [
        ("B12345678 EMPRESA SL", "EMPRESA SL"),
        ("B12345678 - EMPRESA SL", "EMPRESA SL"),
        ("  B12345678   EMPRESA  SL ", "EMPRESA  SL"),
        ("B12345678 GUION-EN EL NOMBRE", "GUION-EN EL NOMBRE"),
        ("B12345678", ""),
        (None, ""),
    ],
)
def test_beneficiary_name_handles_both_separators(macros, beneficiary, name):
    assert (
        macros.execute("SELECT beneficiary_name(?::VARCHAR)", [beneficiary]).fetchone()[0] == name
    )
