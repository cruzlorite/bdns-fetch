# SPDX-License-Identifier: GPL-3.0-or-later

"""Date ranges in the shape the API's two date filters expect.

The API has two families of date filter, and they disagree on the upper
bound:

- `fechaRegInicio` / `fechaRegFin`, the registration date, on the award
  searches (`concesiones`, `ayudasestado`, `minimis`, `partidospoliticos`):
  **`fechaRegFin` is exclusive**. Asking for one day means
  `fechaRegFin = day + 1`.
- `fechaDesde` / `fechaHasta` on the other searches: **`fechaHasta` is
  inclusive**.

Getting this wrong loses or duplicates one day at every range boundary,
silently. The helpers here take an inclusive `[first, last]`, the natural
way to say it, and return the keyword arguments each family needs. The
measurements behind both rules are in
[the API behaviour notes](../../explanation/api-behavior.md#upper-bound), and
[`check_api_contract`][bdns.fetch.contract.check_api_contract] re-checks
them against the live service.

Long ranges also fail: a multi-year registration-date range returns
`ERR_MANTENIMIENTO_BBDD` intermittently, at any page depth, while the same
dates fetched a week at a time do not
([measurements](../../explanation/api-behavior.md#range-reliability)).
[`split_range`][bdns.fetch.dates.split_range] cuts a range into
`MAX_RANGE_DAYS` pieces.
"""

from collections.abc import Iterator
from datetime import date, timedelta

__all__ = ["MAX_RANGE_DAYS", "period_range", "registration_range", "split_range"]

MAX_RANGE_DAYS = 7
"""Widest range known to be fetched reliably in one go."""


def registration_range(first: date, last: date) -> dict[str, date]:
    """Return the `fechaRegInicio`/`fechaRegFin` arguments covering `[first, last]`.

    Args:
        first: First registration day wanted, inclusive.
        last: Last registration day wanted, inclusive.

    Returns:
        `{"fechaRegInicio": first, "fechaRegFin": last + 1 day}`, since
        the API excludes `fechaRegFin` itself.
    """
    return {"fechaRegInicio": first, "fechaRegFin": last + timedelta(days=1)}


def period_range(first: date, last: date) -> dict[str, date]:
    """Return the `fechaDesde`/`fechaHasta` arguments covering `[first, last]`.

    Args:
        first: First day wanted, inclusive.
        last: Last day wanted, inclusive.

    Returns:
        `{"fechaDesde": first, "fechaHasta": last}`; both are inclusive.
    """
    return {"fechaDesde": first, "fechaHasta": last}


def split_range(first: date, last: date, days: int = MAX_RANGE_DAYS) -> Iterator[tuple[date, date]]:
    """Split `[first, last]` into contiguous, non-overlapping inclusive pieces.

    Args:
        first: First day of the range, inclusive.
        last: Last day of the range, inclusive.
        days: Maximum days per piece.

    Yields:
        `(piece_first, piece_last)` pairs, both inclusive, in order. At
        least one, even when `first == last`.

    Raises:
        ValueError: If `last` is before `first`, or `days` is below 1.
    """
    if last < first:
        raise ValueError(f"last ({last}) is before first ({first})")
    if days < 1:
        raise ValueError("days must be 1 or greater")
    current = first
    while current <= last:
        piece_last = min(current + timedelta(days=days - 1), last)
        yield current, piece_last
        current = piece_last + timedelta(days=1)
