# SPDX-License-Identifier: GPL-3.0-or-later

"""Canonical JSON, row hashing, and natural key derivation for SCD2 versioning."""

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional

__all__ = ["canonical_json", "natural_key", "row_hash", "sorted_delimited_list"]


def _order_independent(value: Any) -> Any:
    """Sort list elements recursively, so hashing ignores array order.

    Dict key order is already handled by `json.dumps(sort_keys=True)`,
    recursively; only list element order needs normalizing here, by
    sorting on each element's own canonical JSON string.

    Evidence that the order varies between calls, and what it cost before
    this existed, is in docs/explanation/bdns-api-behavior.md#spurious-changes.

    Args:
        value: Any JSON-compatible value.

    Returns:
        The same value with every list sorted, recursively.
    """
    if isinstance(value, dict):
        return {k: _order_independent(v) for k, v in value.items()}
    if isinstance(value, list):
        items = [_order_independent(v) for v in value]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, default=str))
    return value


def sorted_delimited_list(value: str, split_pattern: str) -> str:
    """Sort the elements of a list that travels inside a single string.

    `_order_independent` cannot help with these: it sorts JSON arrays,
    and this list is just text as far as JSON is concerned.

    `split_pattern` is a regular expression rather than a plain
    separator because a plain one is not always safe. In minimis the
    separator is ";" but several official CNAE names contain a semicolon
    of their own ("Administración Pública y defensa; Seguridad Social
    obligatoria"), so splitting on every ";" cuts those descriptions in
    half. The pattern splits before the start of an element instead,
    leaving them whole. Where the separator is unambiguous the pattern
    is just that character, as with "#" in ayudasestado.

    A pattern that stops matching degrades safely: the value is not
    split, so it is not sorted either, and reordering starts producing
    versions again. It can never merge two genuinely different lists,
    because sorting preserves the elements.

    Which fields carry these lists, and the evidence that their order
    varies between calls, is in docs/explanation/bdns-api-behavior.md#shuffled-lists.

    Args:
        value: The raw field value, elements joined by a separator.
        split_pattern: Regular expression matching the separator.

    Returns:
        The elements, stripped and sorted, joined on NUL — a character
        the payloads do not contain, so the result is unambiguous. Only
        the hash sees this; the payload is stored as the API sent it.
    """
    parts = sorted(part.strip() for part in re.split(split_pattern, value))
    return "\x00".join(parts)


def canonical_json(
    payload: dict[str, Any],
    exclude_fields: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
    canonical_arrays: bool = True,
) -> str:
    """Render `payload` as the canonical JSON string the hash is taken over.

    Canonical means two payloads that this project considers the same
    record produce byte-identical output: keys sorted, no incidental
    whitespace, and the normalizations below applied.

    Args:
        payload: The record to render.
        exclude_fields: Fields the hash ignores. Removed before
            rendering, so a change confined to them is not a change.
        delimited_lists: Fields carrying a list inside a single string,
            mapped to the pattern that splits them. Sorted with
            `sorted_delimited_list`.
        canonical_arrays: Sort JSON array elements recursively. On by
            default; turning it off is offered because it is a
            judgement about the source rather than a law, but it
            re-versions every record with a reordered nested array on
            every run.

    Returns:
        The canonical JSON string. Not stored anywhere: the payload is
        stored as the API sent it.
    """
    if exclude_fields:
        excluded = set(exclude_fields)
        payload = {k: v for k, v in payload.items() if k not in excluded}
    if delimited_lists:
        payload = {
            k: sorted_delimited_list(v, delimited_lists[k])
            if k in delimited_lists and isinstance(v, str)
            else v
            for k, v in payload.items()
        }
    normalized = _order_independent(payload) if canonical_arrays else payload
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def row_hash(
    payload: dict[str, Any],
    exclude_fields: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
    canonical_arrays: bool = True,
) -> str:
    """Return the SHA-256 hex digest of `payload`'s canonical JSON.

    This is the content hash SCD2 versioning compares: a different hash
    means a different stored payload. Arguments are those of
    `canonical_json`, which does the normalizing.

    Args:
        payload: The record to hash.
        exclude_fields: Fields the hash ignores.
        delimited_lists: Fields carrying a list inside a string, mapped
            to the pattern that splits them.
        canonical_arrays: Sort JSON array elements recursively.

    Returns:
        A 64-character lowercase hex digest.
    """
    digest = canonical_json(payload, exclude_fields, delimited_lists, canonical_arrays).encode("utf-8")
    return hashlib.sha256(digest).hexdigest()


def natural_key(payload: dict[str, Any], key_fields: Sequence[str]) -> str:
    """Build a stable string key from one or more fields.

    Args:
        payload: The record to read the key from.
        key_fields: Field names, in order. Composite keys are supported,
            and the order is part of the key: it must stay fixed for an
            entity or its versions stop linking to their own past.

    Returns:
        The field values as a JSON array string.

    Raises:
        KeyError: If `payload` is missing one of `key_fields`.
    """
    values = [payload[field] for field in key_fields]
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False, default=str)
