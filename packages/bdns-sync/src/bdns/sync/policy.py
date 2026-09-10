# SPDX-License-Identifier: GPL-3.0-or-later

"""What a sync does to a record before storing and versioning it.

Two categories of rule live here, and the difference between them is the
whole point of the module:

- Rules that change what is **stored**: `drop`.
- Rules that change only what the **hash sees**, leaving the payload
  stored exactly as the source sent it: `hash_exclude`,
  `delimited_lists`, `canonical_arrays`.

They apply in that order, and `prepare` is the only way to use them, so
the two halves can never be paired wrongly. The invariant that protects:

    a different hash always means a different stored payload,
    never the other way round.

Identity is not policy either: the natural key and the registration-date
field are out of reach of any policy, and `check_identity` refuses one
that tries to drop them.

Why the invariant only holds in that direction, why the hash-only rules
are the safe half, and what the asymmetry costs when it is broken:
docs/explanation/payload-policy.md.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from bdns.sync.hashing import row_hash

__all__ = ["DEFAULT_POLICY", "PayloadPolicy"]


@dataclass(frozen=True)
class PayloadPolicy:
    """The rules one entity's records go through.

    Defaults are the measured findings for each entity (see
    docs/explanation/bdns-api-behavior.md#spurious-changes), declared in
    `bdns.sync.syncers` next to the entity they belong to. The empty policy is the identity function:
    store what arrived, hash all of it.

    Attributes:
        drop: Fields removed from the record before anything else. They
            are not stored and, because everything downstream works on
            the reduced record, they are not hashed either. Listing a
            dropped field in `hash_exclude` as well is therefore
            redundant: it is harmless, but it does nothing.
        hash_exclude: Fields the hash ignores. Still stored whole; they
            just stop counting as a change. For fields the source
            rewrites for the same record, where hashing them versions the
            row forever.
        delimited_lists: Fields carrying a list inside a single string,
            mapped to the pattern that splits them. Elements are sorted
            before hashing, so the order the source happened to use stops
            counting as a change. The payload keeps the original order.
        canonical_arrays: Sort JSON array elements recursively before
            hashing. On by default because the source returns nested
            arrays in an order that varies between calls; turning it off
            re-versions those records on every run.
    """

    drop: tuple[str, ...] = ()
    hash_exclude: tuple[str, ...] = ()
    delimited_lists: Mapping[str, str] = field(default_factory=dict)
    canonical_arrays: bool = True

    def prepare(self, raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
        """Return the record to store and its hash, in that order.

        Deliberately the only entry point. Exposing the two steps
        separately would let a caller hash something other than what it
        stores, which is the one combination that produces history that
        cannot be read back.
        """
        stored = {k: v for k, v in raw.items() if k not in self.drop} if self.drop else raw
        digest = row_hash(stored, self.hash_exclude, self.delimited_lists, self.canonical_arrays)
        return stored, digest

    def check_identity(self, key_fields: Sequence[str], reg_date_field: str | None) -> None:
        """Raise if this policy would drop a field the engine needs.

        Without the natural key a record cannot be versioned at all, and
        without its registration date a windowed run cannot tell a
        withdrawal from a row that simply aged out of the window.
        """
        protected = set(key_fields) | ({reg_date_field} if reg_date_field else set())
        clash = sorted(protected.intersection(self.drop))
        if clash:
            raise ValueError(
                f"policy would drop {', '.join(clash)}, which the engine needs to identify "
                f"records (natural key {list(key_fields)}, registration date {reg_date_field}). "
                f"Identity is not policy."
            )

    def describe(self) -> str:
        """One canonical line naming every rule in force.

        Sorted so two equivalent policies always describe identically,
        which is what makes the string usable for spotting that the rules
        changed between one run and the next.
        """
        return " ".join(
            [
                f"drop={sorted(self.drop)}",
                f"hash_exclude={sorted(self.hash_exclude)}",
                f"delimited_lists={sorted(self.delimited_lists)}",
                f"canonical_arrays={self.canonical_arrays}",
            ]
        )


# Store what arrived, hash all of it, sort arrays. What an entity gets
# when it declares nothing.
DEFAULT_POLICY = PayloadPolicy()
