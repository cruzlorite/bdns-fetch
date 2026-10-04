# SPDX-License-Identifier: MIT

"""The kinds of beneficiary the dataset tells apart, as the SQL names them.

The rule itself lives in SQL, in `sql/00_beneficiaries.sql`, because the
build applies it to millions of rows in DuckDB; it is shown on
[the dataset's page](../../index.md#sql). This module gives its values a
name in Python, for code and tests that read the results.
"""

from enum import Enum

__all__ = ["BeneficiaryKind", "is_protected"]


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


def is_protected(kind: BeneficiaryKind) -> bool:
    """Return whether a beneficiary of this kind may only be published aggregated."""
    return kind in {
        BeneficiaryKind.NATURAL_PERSON,
        BeneficiaryKind.PERSON_BASED_ENTITY,
        BeneficiaryKind.UNKNOWN,
    }
