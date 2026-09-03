# SPDX-License-Identifier: GPL-3.0-or-later

"""Canonical JSON, row hashing, and natural key derivation for SCD2 versioning."""

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional


def _order_independent(value: Any) -> Any:
    """Recursively sort list elements so hashing doesn't care about array
    order. Confirmed live on `regiones`: the API returns the same tree
    `children` in a different element order across calls, with no field
    actually changed. Without this normalization, every re-sync produced a
    spurious SCD2 version for any key with a reordered nested array.

    Dict key order is already handled by `json.dumps(sort_keys=True)`
    (recursively); only list element order needs normalizing here, by
    sorting on each element's own canonical JSON string.
    """
    if isinstance(value, dict):
        return {k: _order_independent(v) for k, v in value.items()}
    if isinstance(value, list):
        items = [_order_independent(v) for v in value]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False, default=str))
    return value


def sorted_delimited_list(value: str, separator: str) -> str:
    """Sort the elements of a list that travels inside a single string.

    Some fields carry several values joined by a separator, and the API
    returns them in a different order between calls with the same elements
    (`sectorActividad` in minimis uses ";", `sectores` in ayudasestado uses
    "#"; see section 9 of docs/bdns-api-behavior.md). `_order_independent`
    cannot help: it sorts JSON arrays, and this list is just text as far as
    JSON is concerned.

    Elements are stripped and re-joined on the bare separator, so spacing
    around it stops mattering too. Only the hash sees this; the payload is
    stored exactly as the API sent it.
    """
    return separator.join(sorted(part.strip() for part in value.split(separator)))


def canonical_json(
    payload: dict[str, Any],
    exclude_fields: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
) -> str:
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
    return json.dumps(
        _order_independent(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def row_hash(
    payload: dict[str, Any],
    exclude_fields: Optional[Iterable[str]] = None,
    delimited_lists: Optional[Mapping[str, str]] = None,
) -> str:
    digest = canonical_json(payload, exclude_fields, delimited_lists).encode("utf-8")
    return hashlib.sha256(digest).hexdigest()


def natural_key(payload: dict[str, Any], key_fields: Sequence[str]) -> str:
    """Build a stable string key from one or more fields (composite keys supported)."""
    values = [payload[field] for field in key_fields]
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False, default=str)
