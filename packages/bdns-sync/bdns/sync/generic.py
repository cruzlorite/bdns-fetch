# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared sync shapes reused by several entity modules. Each entity module
still owns its own name, key fields, and any real one-off logic. Only the
mechanical "fetch, then apply" plumbing lives here.
"""

import inspect
import logging
from collections.abc import Iterator, Sequence
from datetime import date, timedelta
from typing import Optional

from bdns.fetch import BDNSClient
from bdns.sync.sinks import Sink

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def all_pages(fetch):
    """Wrap a client fetch method so paginated endpoints return EVERY page.

    bdns-fetch's `num_pages` option defaults to 1, which silently truncates
    any response bigger than one page (pageSize max 10,000). Caught live:
    grandesbeneficiarios_busqueda returned 10,000 of 142,260 rows. Passing
    `num_pages=0` ("all pages") on every call is the fix, but only the
    paginated methods accept the parameter, so it's added by signature
    inspection instead of blindly.
    """
    params = inspect.signature(fetch).parameters
    if "num_pages" not in params:
        return fetch

    def fetch_all(*args, **kwargs):
        kwargs.setdefault("num_pages", 0)
        return fetch(*args, **kwargs)

    return fetch_all

# window name -> reg-date window size in days. Shared by every entity that
# does cascading re-verification (concesiones, ayudasestado, minimis,
# partidospoliticos, convocatorias).
WINDOWS: dict[str, int] = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "annual": 365,
}

# Every reg-date fetch is chunked into pieces this wide, regardless of the
# requested window. Live-tested against concesiones_busqueda: a 7-day range
# pulled cleanly (147,856 rows, 0 errors), while a 4-year range failed
# intermittently with ERR_MANTENIMIENTO_BBDD at every page depth. `daily`
# and `weekly` are already this size or smaller, so chunking is a no-op for
# them; `monthly` and `annual` are the ones this actually protects.
CHUNK_DAYS = 7


def iter_date_chunks(start: date, end: date, chunk_days: int = CHUNK_DAYS) -> Iterator[tuple[date, date]]:
    """Split [start, end] (inclusive) into chunks of at most `chunk_days`,
    contiguous and non-overlapping. Yields (start, end) is always at least
    one item even if `start == end`.
    """
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def to_api_upper_bound(inclusive_end: date) -> date:
    """Translate an inclusive end date (how windows and chunks are expressed
    everywhere else in this codebase) into the value the four `fechaRegFin`
    search endpoints expect.

    Those endpoints (concesiones/ayudasestado/minimis/partidospoliticos)
    treat `fechaRegFin` as EXCLUSIVE: it matches registrations strictly
    before 00:00 of the given date, so it does NOT include the date's own
    day. Confirmed live: querying `fechaRegFin=D` returned 0 rows for day D
    (concesiones leaked a single midnight-exact row), while `fechaRegFin=D+1`
    returned the whole day (~58,000 for concesiones). Left as a bare
    `fechaRegFin=end`, `daily` (start == end) fetches almost nothing, and
    every wider window silently drops its most recent day per chunk.

    To include every registration made on `inclusive_end`, ask the API for
    the day after. This function is the only place that crosses from the
    codebase's inclusive convention to the API's half-open one. Keep it
    here, not inlined as a `+ 1` at call sites.

    IMPORTANT: this is NOT universal. convocatorias' discovery uses a
    different parameter, `fechaHasta`, which is INCLUSIVE (also confirmed
    live: `fechaHasta=D` returns the full day D). That path must NOT call
    this function; see `syncers.discover_convocatoria_codes`.
    """
    return inclusive_end + timedelta(days=1)


def sync_full_catalog(
    sink: Sink, client: BDNSClient, endpoint_name: str, fetch_method_name: str, key_fields: Sequence[str]
) -> dict[str, int]:
    """Fetch everything with one no-arg call, full-reconcile every run."""
    fetch = all_pages(getattr(client, fetch_method_name))
    return sink.sync_full(endpoint_name, fetch(), key_fields)


def sync_swept_catalog(
    sink: Sink,
    client: BDNSClient,
    endpoint_name: str,
    fetch_method_name: str,
    sweep_param: str,
    sweep_values: Sequence[str],
    key_fields: Sequence[str],
) -> dict[str, int]:
    """Sweep `sweep_param` across `sweep_values`, merging into one table
    before reconciling. Reconciling per sweep value would wrongly close out
    the other values' rows as "missing". The sweep value is tagged onto the
    payload under `sweep_param` since the API doesn't echo it back.
    """
    fetch = all_pages(getattr(client, fetch_method_name))

    def rows():
        for value in sweep_values:
            for item in fetch(**{sweep_param: value}):
                item = dict(item)
                item[sweep_param] = value
                yield item

    return sink.sync_full(endpoint_name, rows(), key_fields)


def window_bounds(window: str) -> tuple[date, date]:
    """Map a cascade window name to its inclusive `[start, end]` range. `end`
    is always yesterday (see `to_api_upper_bound` for why today is excluded).
    """
    days = WINDOWS[window]
    end = date.today() - timedelta(days=1)
    return end - timedelta(days=days - 1), end


def resolve_when(
    window: Optional[str], since: Optional[date], until: Optional[date]
) -> tuple[date, date, str]:
    """Turn the two ways of asking for a reg-date range (a named cascade
    `window`, or an explicit `since`/`until` backfill range) into a single
    `(start, end, run_type)` triple.

    An explicit `since` wins over `window` and marks the run as "backfill"
    in `_sync_runs` (`until` defaults to yesterday). This is what lets the
    tool stay a pure primitive: cadence and history bounds are the caller's
    business (`scripts/`), the engine just syncs whatever range it's told.
    """
    if since is not None:
        end = until if until is not None else date.today() - timedelta(days=1)
        return since, end, "backfill"
    if window is not None:
        start, end = window_bounds(window)
        return start, end, window
    raise ValueError("a reg-date sync needs either a window or a since date")


def sync_search_range(
    sink: Sink,
    client: BDNSClient,
    endpoint_name: str,
    fetch_method_name: str,
    key_fields: Sequence[str],
    start: date,
    end: date,
    run_type: str,
    reg_date_field: Optional[str] = None,
) -> dict[str, int]:
    """Fetch the reg-date range `[start, end]` and apply incrementally. Used
    for both cascade windows (a few days back) and backfills (years back);
    same machinery, only the range and `run_type` label differ.

    By default this never closes out keys, since a range is a subset of the
    table, not its full current state. `reg_date_field` opts into
    window-scoped deletion detection (see `scd2.apply_incremental`); only
    entities that expose their own registration date can use it, confirmed
    live per entity.

    The fetch is chunked into `CHUNK_DAYS`-wide pieces (see `iter_date_chunks`
    and `to_api_upper_bound`). `window_start`/`window_end` given to
    `apply_incremental` still span the whole `[start, end]`, since deletion
    scoping cares about the full range, not how it was split to fetch it.
    """
    fetch = all_pages(getattr(client, fetch_method_name))

    def rows():
        for chunk_start, chunk_end in iter_date_chunks(start, end):
            logger.info("%s: chunk [%s .. %s]", endpoint_name, chunk_start, chunk_end)
            yield from fetch(
                fechaRegInicio=chunk_start, fechaRegFin=to_api_upper_bound(chunk_end)
            )

    return sink.sync_window(
        endpoint_name, rows(), key_fields,
        window_start=start, window_end=end, run_type=run_type, reg_date_field=reg_date_field,
    )


def sync_search_range_inclusive(
    sink: Sink,
    client: BDNSClient,
    endpoint_name: str,
    fetch_method_name: str,
    key_fields: Sequence[str],
    start: date,
    end: date,
    run_type: str,
    reg_date_field: Optional[str] = None,
) -> dict[str, int]:
    """Same shape as `sync_search_range`, for the OTHER date-parameter family:
    `fechaDesde`/`fechaHasta`, which is INCLUSIVE on the upper bound (unlike
    `fechaRegFin`; see `to_api_upper_bound` and section 2 of
    docs/bdns-api-behavior.md).
    `chunk_end` is passed as-is, with NO `to_api_upper_bound` bridge.
    Calling it here would over-fetch one extra day past the window.
    """
    fetch = all_pages(getattr(client, fetch_method_name))

    def rows():
        for chunk_start, chunk_end in iter_date_chunks(start, end):
            logger.info("%s: chunk [%s .. %s]", endpoint_name, chunk_start, chunk_end)
            yield from fetch(fechaDesde=chunk_start, fechaHasta=chunk_end)

    return sink.sync_window(
        endpoint_name, rows(), key_fields,
        window_start=start, window_end=end, run_type=run_type, reg_date_field=reg_date_field,
    )

