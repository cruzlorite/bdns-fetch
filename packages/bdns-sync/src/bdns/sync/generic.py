# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared sync shapes reused by several entity modules.

Each entity module still owns its own name, key fields, and any real
one-off logic. Only the mechanical "fetch, then apply" plumbing lives
here.
"""

import inspect
import logging
from collections.abc import Callable, Iterator, Sequence
from datetime import date, timedelta
from typing import Any, Optional

from bdns.fetch import BDNSClient
from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy
from bdns.sync.sinks import Sink

__all__ = [
    "CHUNK_DAYS",
    "WINDOWS",
    "all_pages",
    "iter_date_chunks",
    "resolve_when",
    "sync_full_catalog",
    "sync_search_range",
    "sync_search_range_inclusive",
    "sync_swept_catalog",
    "to_api_upper_bound",
    "window_bounds",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def all_pages(fetch: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a client fetch method so paginated endpoints return EVERY page.

    bdns-fetch's `num_pages` option defaults to 1, which silently
    truncates any response bigger than one page. Only the paginated
    methods accept the parameter, so it is added by signature inspection
    rather than blindly.

    See docs/explanation/bdns-api-behavior.md#api-issues for what this cost when it
    was missing.

    Args:
        fetch: A bound client fetch method.

    Returns:
        `fetch` unchanged if it takes no `num_pages`, otherwise a wrapper
        that defaults it to 0, meaning "all pages".
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
    """Split `[start, end]` into contiguous, non-overlapping chunks.

    Both bounds are inclusive, the project-wide convention. Why the range
    is chunked at all, and why the result does not depend on the chunk
    size, is in docs/explanation/bdns-api-behavior.md#window-chunking.

    Args:
        start: First day of the range, inclusive.
        end: Last day of the range, inclusive.
        chunk_days: Maximum days per chunk.

    Yields:
        `(chunk_start, chunk_end)` pairs, both inclusive. Always at least
        one pair, even when `start == end`.
    """
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def to_api_upper_bound(inclusive_end: date) -> date:
    """Convert an inclusive end date to the exclusive `fechaRegFin` bound.

    This is the only place that crosses from the codebase's inclusive
    convention to the API's half-open one. Keep it here rather than
    inlining a `+ 1` at call sites.

    It is NOT universal: it applies to the four `fechaRegFin` endpoints
    only. The `fechaDesde`/`fechaHasta` family is inclusive and must not
    go through here. Both semantics, and the measurements behind them,
    are in docs/explanation/bdns-api-behavior.md#upper-bound.

    Args:
        inclusive_end: Last day the caller wants included.

    Returns:
        The day after, which is what `fechaRegFin` needs in order to
        cover `inclusive_end` itself.
    """
    return inclusive_end + timedelta(days=1)


def sync_full_catalog(
    sink: Sink, client: BDNSClient, endpoint_name: str, fetch_method_name: str, key_fields: Sequence[str]
) -> dict[str, int]:
    """Fetch everything with one no-arg call, full-reconcile every run.

    Args:
        sink: Where the rows are applied.
        client: The BDNS API client.
        endpoint_name: Table name for this entity.
        fetch_method_name: Client method to call, by name.
        key_fields: Fields forming the natural key.

    Returns:
        The sink's per-run counters.
    """
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
    """Sweep one parameter across several values into a single table.

    All values are merged before reconciling. Reconciling per sweep value
    would wrongly close out the other values' rows as missing.

    Args:
        sink: Where the rows are applied.
        client: The BDNS API client.
        endpoint_name: Table name for this entity.
        fetch_method_name: Client method to call, by name.
        sweep_param: Parameter swept across `sweep_values`. Tagged onto
            each payload under this name, since the API does not echo it
            back.
        sweep_values: The values to sweep over.
        key_fields: Fields forming the natural key.

    Returns:
        The sink's per-run counters.
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
    """Map a cascade window name to its inclusive `[start, end]` range.

    Args:
        window: A key of `WINDOWS`.

    Returns:
        `(start, end)`, both inclusive. `end` is always yesterday: today
        is still accruing registrations, so syncing it would leave a
        partial day behind that nothing revisits.

    Raises:
        KeyError: If `window` is not a known window name.
    """
    days = WINDOWS[window]
    end = date.today() - timedelta(days=1)
    return end - timedelta(days=days - 1), end


def resolve_when(
    window: Optional[str], since: Optional[date], until: Optional[date]
) -> tuple[date, date, str]:
    """Resolve the two ways of asking for a reg-date range into one triple.

    Keeping both forms behind one resolver is what lets the tool stay a
    pure primitive: cadence and history bounds are the caller's business
    (see `scripts/`), and the engine syncs whatever range it is told.

    Args:
        window: A named cascade window, or None.
        since: First day of an explicit backfill range, or None. Wins
            over `window` when both are given.
        until: Last day of the backfill range. Defaults to yesterday.

    Returns:
        `(start, end, run_type)`. `run_type` is the label recorded in
        `_sync_runs`: the window name, or "backfill".

    Raises:
        ValueError: If neither `window` nor `since` was given.
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
    policy: PayloadPolicy = DEFAULT_POLICY,
) -> dict[str, int]:
    """Fetch a `fechaRegInicio`/`fechaRegFin` range and apply incrementally.

    Cascade windows and backfills use the same machinery; only the range
    and the `run_type` label differ. The fetch is chunked into
    `CHUNK_DAYS`-wide pieces, but the window handed to the sink still
    spans the whole `[start, end]`: deletion scoping cares about the
    range asked for, not how it was split to fetch it.

    Args:
        sink: Where the rows are applied.
        client: The BDNS API client.
        endpoint_name: Table name for this entity.
        fetch_method_name: Client method to call, by name.
        key_fields: Fields forming the natural key.
        start: First day of the range, inclusive.
        end: Last day of the range, inclusive.
        run_type: Label recorded in `_sync_runs`.
        reg_date_field: Opts into window-scoped deletion detection. Left
            None, the run never closes out a key, because a range is a
            subset of the table rather than its full current state. Only
            entities that expose their own registration date can set it;
            see docs/explanation/bdns-api-behavior.md#windowed-deletions.
        policy: Rules applied to each record before storing and hashing.

    Returns:
        The sink's per-run counters.
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
        policy=policy,
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
    policy: PayloadPolicy = DEFAULT_POLICY,
) -> dict[str, int]:
    """Fetch a `fechaDesde`/`fechaHasta` range and apply incrementally.

    Same shape as `sync_search_range`, for the other date-parameter
    family. This one is inclusive on the upper bound, so `chunk_end` is
    passed as-is with no `to_api_upper_bound` bridge; calling it here
    would over-fetch one day past the window. Both semantics are in
    docs/explanation/bdns-api-behavior.md#upper-bound.

    Args:
        sink: Where the rows are applied.
        client: The BDNS API client.
        endpoint_name: Table name for this entity.
        fetch_method_name: Client method to call, by name.
        key_fields: Fields forming the natural key.
        start: First day of the range, inclusive.
        end: Last day of the range, inclusive.
        run_type: Label recorded in `_sync_runs`.
        reg_date_field: Opts into window-scoped deletion detection.
        policy: Rules applied to each record before storing and hashing.

    Returns:
        The sink's per-run counters.
    """
    fetch = all_pages(getattr(client, fetch_method_name))

    def rows():
        for chunk_start, chunk_end in iter_date_chunks(start, end):
            logger.info("%s: chunk [%s .. %s]", endpoint_name, chunk_start, chunk_end)
            yield from fetch(fechaDesde=chunk_start, fechaHasta=chunk_end)

    return sink.sync_window(
        endpoint_name, rows(), key_fields,
        window_start=start, window_end=end, run_type=run_type, reg_date_field=reg_date_field,
        policy=policy,
    )

