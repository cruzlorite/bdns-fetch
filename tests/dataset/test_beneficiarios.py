"""Beneficiary classification (dataset/sql/01_beneficiarios.sql). Every name
and ID here is made up, in the shapes the BDNS uses."""

import pytest

PROTECTED = {"persona_fisica", "comunidad_o_sociedad_civil", "desconocido"}


def kind_of(con, beneficiary):
    return con.execute("SELECT beneficiary_kind(?::VARCHAR)", [beneficiary]).fetchone()[0]


@pytest.mark.parametrize(
    ("beneficiary", "kind"),
    [
        ("***1234** NOMBRE APELLIDO APELLIDO", "persona_fisica"),
        ("****1234* NOMBRE APELLIDO", "persona_fisica"),
        ("*****1234 NOMBRE", "persona_fisica"),
        ("12345678Z NOMBRE APELLIDO", "persona_fisica"),
        ("X1234567L NOMBRE APELLIDO", "persona_fisica"),
        ("L1234567A NOMBRE APELLIDO", "persona_fisica"),
        ("B12345678 EMPRESA DE EJEMPLO SL", "persona_juridica"),
        ("G12345678 FUNDACION DE EJEMPLO", "persona_juridica"),
        ("A1234567J SOCIEDAD ANONIMA", "persona_juridica"),
        ("b12345678 empresa en minusculas", "persona_juridica"),
        ("  B12345678   ESPACIOS DE MAS  ", "persona_juridica"),
        ("P1234567D AYUNTAMIENTO DE EJEMPLO", "entidad_publica"),
        ("Q1234567H ORGANISMO DE EJEMPLO", "entidad_publica"),
        ("S1234567E CONSEJERIA DE EJEMPLO", "entidad_publica"),
        ("E12345678 APELLIDO Y APELLIDO CB", "comunidad_o_sociedad_civil"),
        ("J12345678 APELLIDO SC", "comunidad_o_sociedad_civil"),
        ("123456789012 FOREIGN COMPANY LTD", "desconocido"),
        ("BE0123456789 SOCIETE ETRANGERE", "desconocido"),
        ("", "desconocido"),
        (None, "desconocido"),
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
    assert kind_of(macros, "B12345678 12345678Z") == "persona_juridica"
    assert kind_of(macros, "***1234** EMPRESA SL") == "persona_fisica"


@pytest.mark.parametrize(
    ("kind", "protected"),
    [
        ("persona_fisica", True),
        ("comunidad_o_sociedad_civil", True),
        ("desconocido", True),
        ("persona_juridica", False),
        ("entidad_publica", False),
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
