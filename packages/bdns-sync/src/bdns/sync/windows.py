# SPDX-License-Identifier: MIT

"""Registration-date windows: which days a windowed sync covers.

Every range in this package is inclusive at both ends, and ends at
yesterday at the latest: today is still receiving registrations, so a run
that covered it would leave a partial day behind that nothing revisits.
Translating an inclusive range into each API date family's arguments is
bdns-fetch's job
([`bdns.fetch.dates`](https://cruzlorite.github.io/bdns-fetch/en/reference/api/dates/)),
not this module's.

The windows are nested: each ends yesterday, so on any given day annual
contains monthly, which contains weekly, which contains daily. Running
the widest window that applies covers every narrower one, which is what
[`cadence_window`][bdns.sync.windows.cadence_window] picks.
"""

from datetime import date, timedelta

__all__ = ["WINDOWS", "cadence_window", "resolve_when", "window_bounds"]

WINDOWS: dict[str, int] = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "annual": 365,
}
"""Window name to its width in days."""

ANNUAL_DAYS = ("01-01", "05-01", "09-01")
"""Days of the year (`MM-DD`) on which the delta widens to the annual window."""


def window_bounds(window: str, today: date | None = None) -> tuple[date, date]:
    """Map a window name to its inclusive `[start, end]` range.

    Args:
        window: A key of `WINDOWS`.
        today: The day the run happens. Defaults to the current date.

    Returns:
        `(start, end)`, both inclusive, with `end` yesterday.

    Raises:
        KeyError: If `window` is not a known window name.
    """
    days = WINDOWS[window]
    end = (today or date.today()) - timedelta(days=1)
    return end - timedelta(days=days - 1), end


def resolve_when(
    window: str | None,
    since: date | None,
    until: date | None,
    today: date | None = None,
) -> tuple[date, date, str]:
    """Resolve the two ways of asking for a range into one triple.

    Args:
        window: A named window, or None.
        since: First day of an explicit range, or None. Wins over
            `window` when both are given.
        until: Last day of that range. Defaults to yesterday.
        today: The day the run happens. Defaults to the current date.

    Returns:
        `(start, end, run_type)`. `run_type` is the label recorded in
        `_sync_runs`: the window name, or `"backfill"`.

    Raises:
        ValueError: If neither `window` nor `since` was given.
    """
    today = today or date.today()
    if since is not None:
        end = until if until is not None else today - timedelta(days=1)
        return since, end, "backfill"
    if window is not None:
        start, end = window_bounds(window, today)
        return start, end, window
    raise ValueError("a windowed sync needs either a window or a since date")


def cadence_window(day: date) -> str:
    """Pick the window a daily delta run uses on `day`.

    Weekly is the baseline, not daily: records can arrive with a
    registration date some days in the past, and deletions are only
    detected inside the window a run covers, so a 7-day lookback every day
    catches late arrivals and late removals that a 1-day window would
    miss. Mondays widen to monthly, and three days a year to annual, for
    progressively deeper reconciliation.

    Args:
        day: The day the run happens.

    Returns:
        `"annual"`, `"monthly"` or `"weekly"`.
    """
    if day.strftime("%m-%d") in ANNUAL_DAYS:
        return "annual"
    if day.isoweekday() == 1:
        return "monthly"
    return "weekly"
