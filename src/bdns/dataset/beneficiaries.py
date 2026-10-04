# SPDX-License-Identifier: MIT

"""Tell natural persons apart from legal persons in a BDNS beneficiary field.

The BDNS writes a beneficiary as its tax ID followed by its name
(`B12345678 EMPRESA SL`). For natural persons it hides part of the ID but
keeps the full name (`***1234** NOMBRE APELLIDOS`), so the field identifies
them, and the dataset may only publish them aggregated
([why](../../../adr/0002-anonymised-dataset.md)).

The classification reads only the leading identifier, never the name, and
it is conservative by construction: a shape it does not recognise is
`UNKNOWN`, and `UNKNOWN` is protected exactly like a natural person. Being
wrong in that direction only costs detail; the other direction would
publish a person.

The rule is written once, as the patterns below, and runs two ways: in
Python ([`classify`][]) and as a DuckDB SQL expression
([`classify_sql`][]), which is what the build uses on millions of rows. The
tests check that both give the same answer.
"""

import re
from enum import Enum

__all__ = ["BeneficiaryKind", "classify", "classify_sql", "is_protected", "split"]


class BeneficiaryKind(Enum):
    """Who a beneficiary is, as far as its tax ID tells.

    Attributes:
        NATURAL_PERSON: A person: a DNI, NIE or K/L/M tax ID, whole or masked.
        PERSON_BASED_ENTITY: A community of property (E) or civil
            partnership (J). They have a tax ID of their own, but are
            usually named after their members.
        LEGAL_PERSON: A company, association, foundation or other entity.
        PUBLIC_BODY: A public administration or body (P, Q and S tax IDs).
        UNKNOWN: Empty or an unrecognised shape, such as a foreign ID.
    """

    NATURAL_PERSON = "natural_person"
    PERSON_BASED_ENTITY = "person_based_entity"
    LEGAL_PERSON = "legal_person"
    PUBLIC_BODY = "public_body"
    UNKNOWN = "unknown"


# Each kind's identifier shapes, matched against the whole (upper-cased)
# identifier, in this order. Written in the regex syntax Python and DuckDB
# (RE2) share. A natural person's ID is a masked one (***1234**), a DNI, an
# NIE or a K/L/M one (minors without a DNI, Spaniards abroad, foreigners
# without an NIE). Entity IDs are a letter, seven digits and a control
# character; the letter says what kind of entity it is.
_CIF_BODY = r"\d{7}[0-9A-J]"
_RULES: tuple[tuple[BeneficiaryKind, str], ...] = (
    (
        BeneficiaryKind.NATURAL_PERSON,
        r"\*{2,}\d{3,5}\*{0,3}|\d{8}[A-Z]|[XYZ]\d{7}[A-Z]|[KLM]\d{7}[A-Z0-9]",
    ),
    (BeneficiaryKind.PUBLIC_BODY, rf"[PQS]{_CIF_BODY}"),
    (BeneficiaryKind.PERSON_BASED_ENTITY, rf"[EJ]{_CIF_BODY}"),
    (BeneficiaryKind.LEGAL_PERSON, rf"[ABCDFGHNRUVW]{_CIF_BODY}"),
)
_COMPILED = tuple((kind, re.compile(pattern)) for kind, pattern in _RULES)

_PROTECTED = frozenset(
    {BeneficiaryKind.NATURAL_PERSON, BeneficiaryKind.PERSON_BASED_ENTITY, BeneficiaryKind.UNKNOWN}
)


def split(beneficiary: str | None) -> tuple[str, str]:
    """Split a beneficiary field into its leading identifier and its name.

    Args:
        beneficiary: The field as the API returns it, possibly None.

    Returns:
        `(identifier, name)`, either of them empty when absent.
    """
    text = (beneficiary or "").strip()
    identifier, _, name = text.partition(" ")
    return identifier, name.strip()


def classify(beneficiary: str | None) -> BeneficiaryKind:
    """Classify a beneficiary by the shape of its leading tax ID.

    Args:
        beneficiary: The field as the API returns it (`ID NAME`).

    Returns:
        The kind; `UNKNOWN` for anything not recognised.
    """
    identifier = split(beneficiary)[0].upper()
    for kind, pattern in _COMPILED:
        if identifier and pattern.fullmatch(identifier):
            return kind
    return BeneficiaryKind.UNKNOWN


def classify_sql(column: str) -> str:
    """Return a DuckDB SQL expression that classifies `column` like [`classify`][].

    The expression yields each kind's value (`'natural_person'`,
    `'legal_person'`...), for use in a `SELECT` over millions of rows.

    Args:
        column: The SQL expression holding the beneficiary field, such as
            `payload->>'beneficiario'`.

    Returns:
        A `CASE` expression.
    """
    identifier = f"upper(split_part(trim(coalesce({column}, '')), ' ', 1))"
    branches = "\n".join(
        f"    WHEN regexp_full_match({identifier}, '{pattern}') THEN '{kind.value}'"
        for kind, pattern in _RULES
    )
    return f"CASE\n{branches}\n    ELSE '{BeneficiaryKind.UNKNOWN.value}'\nEND"


def is_protected(kind: BeneficiaryKind) -> bool:
    """Return whether a beneficiary of this kind may only be published aggregated."""
    return kind in _PROTECTED
