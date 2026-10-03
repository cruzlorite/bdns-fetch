# SPDX-License-Identifier: MIT

"""Live check that the API still behaves the way this package documents.

[`dates`][bdns.fetch.dates] encodes two measured facts: `fechaRegFin` is
exclusive and `fechaHasta` inclusive
([evidence](../../explanation/api-behavior.md#upper-bound)). Unit tests can only pin our model of
the API, not the API, so a change upstream would leave every test green
while callers lose or duplicate a day at every range boundary. This module
asks the real service, at a cost of a dozen requests.

Reached as `bdns-fetch check-api`, and meant to run before a scheduled
sync rather than inside each request.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from bdns.fetch.client import BDNSClient
from bdns.fetch.dates import period_range, registration_range

__all__ = ["ContractReport", "check_api_contract"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

LOOKBACK_DAYS = 30
"""Default probe day, this many days back: recent enough that the API still serves it, old enough that the day is closed and its records stable."""

MAX_ATTEMPTS = 5
"""Earlier days tried when a probe day is empty or the API errors."""

# One endpoint per date family, chosen because a single day is one page and
# the whole check runs in seconds; concesiones would pull ~58,000 rows per
# probe for the same answer. (method, key field, registration-date field)
_EXCLUSIVE_PROBE = ("fetch_minimis_busqueda", "idConcesion", "fechaRegistro")
_INCLUSIVE_PROBE = ("fetch_convocatorias_busqueda", "numeroConvocatoria", "fechaRecepcion")

# A single midnight-exact record leaked past the exclusive bound when this
# was measured, so a trace is tolerated rather than demanding exactly zero.
_LEAK_TOLERANCE = 0.05


@dataclass
class ContractReport:
    """Outcome of a contract check.

    Attributes:
        status: `"ok"` when every invariant held. `"inconclusive"` when the
            probe days were empty or the API errored: transient trouble,
            not a reason to stop anything. `"changed"` when the API
            returned valid data contradicting an invariant, the one case
            worth stopping a sync for.
        messages: What was found, one sentence each.
    """

    status: Literal["ok", "inconclusive", "changed"]
    messages: list[str] = field(default_factory=list)


def _keys(records: list, key_field: str) -> set:
    """Collect the key values of the records that have one."""
    return {r[key_field] for r in records if isinstance(r, dict) and key_field in r}


def _probe_exclusive(client: BDNSClient, day: date, problems: list[str]) -> bool:
    """`fechaRegFin` is exclusive: it must not include its own day."""
    method, key_field, reg_field = _EXCLUSIVE_PROBE
    fetch = getattr(client, method)
    nxt = day + timedelta(days=1)

    full_day = list(fetch(**registration_range(day, day)))
    if not full_day:
        return False  # nothing registered that day; try another

    bare = list(fetch(fechaRegInicio=day, fechaRegFin=day))
    if len(bare) > max(1, _LEAK_TOLERANCE * len(full_day)):
        problems.append(
            f"{method}: fechaRegFin looks INCLUSIVE now: fechaRegFin={day} returned {len(bare)} "
            f"records for that same day (expected ~0 of {len(full_day)}). "
            f"registration_range would now fetch one day too many."
        )

    next_day = list(fetch(**registration_range(nxt, nxt)))
    if next_day:
        shared = _keys(full_day, key_field) & _keys(next_day, key_field)
        if shared:
            problems.append(
                f"{method}: adjacent days overlap by {len(shared)} record(s); "
                f"consecutive ranges would double-count them."
            )
        span = list(fetch(**registration_range(day, nxt)))
        union = _keys(full_day, key_field) | _keys(next_day, key_field)
        if _keys(span, key_field) != union:
            problems.append(
                f"{method}: a two-day range is not the union of its two days "
                f"({len(_keys(span, key_field))} vs {len(union)} records); "
                f"splitting a range would lose or duplicate records."
            )

    _check_shape(method, full_day, key_field, reg_field, day, problems)
    return True


def _probe_inclusive(client: BDNSClient, day: date, problems: list[str]) -> bool:
    """`fechaHasta` is inclusive: it must include its own day."""
    method, key_field, reg_field = _INCLUSIVE_PROBE
    fetch = getattr(client, method)

    same_day = list(fetch(**period_range(day, day)))
    if not same_day:
        # Either the day is empty, or the bound stopped being inclusive. A
        # wider range tells them apart: if this day's records show up
        # there, the day was not empty and the bound moved.
        wider = [
            r
            for r in fetch(**period_range(day, day + timedelta(days=1)))
            if isinstance(r, dict) and r.get(reg_field) == day.isoformat()
        ]
        if wider:
            problems.append(
                f"{method}: fechaHasta looks EXCLUSIVE now: fechaHasta={day} returned nothing for "
                f"that day, while a wider range returned {len(wider)} records for it. "
                f"period_range would now drop the last day of every range."
            )
            return True
        return False
    _check_shape(method, same_day, key_field, reg_field, day, problems)
    return True


def _check_shape(
    method: str, records: list, key_field: str, reg_field: str, day: date, problems: list[str]
) -> None:
    """Check that records carry their key and the date they were filtered by."""
    missing_key = sum(1 for r in records if not isinstance(r, dict) or r.get(key_field) is None)
    if missing_key:
        problems.append(
            f"{method}: {missing_key} of {len(records)} records have no {key_field}, "
            f"the field that identifies them."
        )
    off_day = [
        r.get(reg_field)
        for r in records
        if isinstance(r, dict) and r.get(reg_field) != day.isoformat()
    ]
    if off_day:
        problems.append(
            f"{method}: {len(off_day)} of {len(records)} records fetched for {day} carry a different "
            f"{reg_field} (e.g. {off_day[0]!r}); the date filter no longer matches that field."
        )


def check_api_contract(client: BDNSClient, day: date | None = None) -> ContractReport:
    """Ask the live API whether the documented date semantics still hold.

    Args:
        client: The client to probe with.
        day: Probe day. Defaults to `LOOKBACK_DAYS` ago. If it is empty or
            the API errors, up to `MAX_ATTEMPTS` earlier days are tried.

    Returns:
        The report. Only `"changed"` means the API moved.
    """
    start = day or (date.today() - timedelta(days=LOOKBACK_DAYS))
    problems: list[str] = []

    for offset in range(MAX_ATTEMPTS):
        probe_day = start - timedelta(days=offset)
        try:
            exclusive = _probe_exclusive(client, probe_day, problems)
            inclusive = _probe_inclusive(client, probe_day, problems)
        except Exception as exc:  # any failure makes this day inconclusive
            logger.warning("api check: %s on %s, trying an earlier day", exc, probe_day)
            continue
        if exclusive and inclusive:
            logger.info("api check: probed %s", probe_day)
            if problems:
                return ContractReport("changed", problems)
            return ContractReport(
                "ok", [f"Probed {probe_day}: date semantics and record shape unchanged."]
            )

    if problems:
        return ContractReport("changed", problems)
    return ContractReport(
        "inconclusive",
        [
            f"No usable probe day in the {MAX_ATTEMPTS} days before {start} "
            f"(empty days or API errors); nothing could be verified."
        ],
    )
