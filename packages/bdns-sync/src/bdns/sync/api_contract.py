# SPDX-License-Identifier: GPL-3.0-or-later

"""Live verification that the BDNS API still behaves as this engine assumes.

Everything the date handling does rests on behavior measured once against
the real service and then frozen into tests (see
docs/bdns-api-behavior.md#upper-bound). Those tests pin the assumption,
not the API:
`tests/fake_client.py` models the same semantics, so if the source ever
changes them, CI stays green forever while production quietly loses a day
at every chunk boundary.

This module is the only thing in the project that asks the real service
whether those assumptions still hold. It is reached through
`bdns-sync check-api`, run once before a day's cadence rather than inside
every sync: it costs a handful of calls and answers a question about the
source, not about any one endpoint.
"""

import logging
from datetime import date, timedelta
from typing import Optional

from bdns.fetch import BDNSClient
from bdns.sync.generic import all_pages

__all__ = ["check_api_contract"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# 30 days back: recent enough that the API still serves it, old enough that
# the day is closed and its record set is stable.
API_CHECK_LOOKBACK_DAYS = 30
API_CHECK_MAX_ATTEMPTS = 5

# One entity per date-parameter family. Both are dense enough that a single
# day is one page, and small enough that the whole check runs in seconds;
# concesiones_busqueda would pull ~58,000 rows per probe for the same answer.
EXCLUSIVE_PROBE = ("minimis_busqueda", "fetch_minimis_busqueda", "idConcesion", "fechaRegistro")
INCLUSIVE_PROBE = (
    "convocatorias_busqueda",
    "fetch_convocatorias_busqueda",
    "numeroConvocatoria",
    "fechaRecepcion",
)

# A single midnight-exact record leaked past the exclusive bound when this
# was measured live, so the check tolerates a trace rather than demanding
# exactly zero.
_LEAK_TOLERANCE = 0.05


def _keys(records, key_field):
    return {record[key_field] for record in records if isinstance(record, dict) and key_field in record}


def _probe_exclusive(client, day, problems):
    """`fechaRegFin` is exclusive: it must not include its own day."""
    name, method, key_field, reg_field = EXCLUSIVE_PROBE
    fetch = all_pages(getattr(client, method))
    nxt = day + timedelta(days=1)

    full_day = list(fetch(fechaRegInicio=day, fechaRegFin=nxt))
    if not full_day:
        return False  # nothing registered that day; try another

    bare = list(fetch(fechaRegInicio=day, fechaRegFin=day))
    if len(bare) > max(1, _LEAK_TOLERANCE * len(full_day)):
        problems.append(
            f"{name}: fechaRegFin looks INCLUSIVE now: fechaRegFin={day} returned {len(bare)} "
            f"records for that same day (expected ~0 of {len(full_day)}). "
            f"generic.to_api_upper_bound would now over-fetch a day per chunk."
        )

    next_day = list(fetch(fechaRegInicio=nxt, fechaRegFin=nxt + timedelta(days=1)))
    if next_day:
        shared = _keys(full_day, key_field) & _keys(next_day, key_field)
        if shared:
            problems.append(
                f"{name}: adjacent days overlap by {len(shared)} record(s); "
                f"consecutive windows would double-count them."
            )
        span = list(fetch(fechaRegInicio=day, fechaRegFin=nxt + timedelta(days=1)))
        union = _keys(full_day, key_field) | _keys(next_day, key_field)
        if _keys(span, key_field) != union:
            problems.append(
                f"{name}: a two-day range is not the union of its two days "
                f"({len(_keys(span, key_field))} vs {len(union)} records); "
                f"chunking a window would lose or duplicate records."
            )

    _check_shape(name, full_day, key_field, reg_field, day, problems)
    return True


def _probe_inclusive(client, day, problems):
    """`fechaHasta` is inclusive: it must include its own day."""
    name, method, key_field, reg_field = INCLUSIVE_PROBE
    fetch = all_pages(getattr(client, method))

    same_day = list(fetch(fechaDesde=day, fechaHasta=day))
    if not same_day:
        # Either the day is genuinely empty, or the bound stopped being
        # inclusive. Asking for the wider range tells them apart: if the
        # records for this day show up there, the day was not empty and
        # the bound moved.
        wider = [
            r
            for r in fetch(fechaDesde=day, fechaHasta=day + timedelta(days=1))
            if isinstance(r, dict) and r.get(reg_field) == day.isoformat()
        ]
        if wider:
            problems.append(
                f"{name}: fechaHasta looks EXCLUSIVE now: fechaHasta={day} returned nothing for "
                f"that day, while a wider range returned {len(wider)} records for it. "
                f"convocatorias discovery would drop the last day of every window."
            )
            return True
        return False
    _check_shape(name, same_day, key_field, reg_field, day, problems)
    return True


def _check_shape(name, records, key_field, reg_field, day, problems):
    """Check the record-level assumptions, appending any failures to `problems`.

    Namely that the natural key and the registration date are present,
    usable, and mean what the engine thinks they mean.
    """
    missing_key = sum(1 for r in records if not isinstance(r, dict) or r.get(key_field) is None)
    if missing_key:
        problems.append(
            f"{name}: {missing_key} of {len(records)} records have no usable {key_field}, "
            f"which is the natural key; they cannot be versioned."
        )
    off_day = [r.get(reg_field) for r in records if isinstance(r, dict) and r.get(reg_field) != day.isoformat()]
    if off_day:
        problems.append(
            f"{name}: {len(off_day)} of {len(records)} records fetched for {day} carry a different "
            f"{reg_field} (e.g. {off_day[0]!r}); the date filter no longer matches that field."
        )


def check_api_contract(client: BDNSClient, day: Optional[date] = None) -> tuple[str, list[str]]:
    """Ask the live API whether it still behaves the way this engine assumes.

    Args:
        client: The BDNS API client.
        day: Probe day. Defaults to `API_CHECK_LOOKBACK_DAYS` ago, far
            enough back that the day is fully registered.

    Returns:
        `(status, messages)`, where `status` is one of:

        - "ok": every invariant held.
        - "inconclusive": the probe days came back empty or the API
          errored. Deliberately not a failure. Transient trouble is
          normal here, and blocking a whole day's cadence over it would
          cost more than it saves; a genuinely unreachable API makes the
          syncs themselves fail, which is the real signal.
        - "changed": the API returned valid data contradicting an
          invariant. The one case worth stopping for, because syncing
          through a changed boundary loses or duplicates data silently.
    """
    start = day or (date.today() - timedelta(days=API_CHECK_LOOKBACK_DAYS))
    problems: list[str] = []
    checked = False

    for offset in range(API_CHECK_MAX_ATTEMPTS):
        probe_day = start - timedelta(days=offset)
        try:
            exclusive = _probe_exclusive(client, probe_day, problems)
            inclusive = _probe_inclusive(client, probe_day, problems)
        except Exception as exc:
            logger.warning("api check: %s on %s, retrying another day", exc, probe_day)
            continue
        if exclusive and inclusive:
            checked = True
            logger.info("api check: probed %s", probe_day)
            break

    if problems:
        return "changed", problems
    if not checked:
        return "inconclusive", [
            "API contract check inconclusive: no probe day returned data. "
            "Not treated as a failure; the syncs themselves will fail if the API is down."
        ]
    return "ok", ["API contract check passed: date-window semantics and record shape unchanged."]
