# SPDX-License-Identifier: MIT

"""Date ranges the API can serve.

The API's two families of date filter disagree on the upper bound:
`fechaRegFin` is exclusive and `fechaHasta` inclusive. The measurements
are in [the API behaviour notes](../../explanation/api-behavior.md#upper-bound),
and [`check_api_contract`][bdns.fetch.contract.check_api_contract] re-checks
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

__all__ = ["MAX_RANGE_DAYS", "split_range"]

MAX_RANGE_DAYS = 7
"""Widest range known to be fetched reliably in one go."""


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
