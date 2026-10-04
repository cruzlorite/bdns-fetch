from datetime import date, timedelta

import pytest

from bdns.sync.windows import cadence_window, resolve_when, window_bounds

TODAY = date(2026, 3, 11)  # a Wednesday
YESTERDAY = TODAY - timedelta(days=1)


def test_window_bounds_span_the_declared_days_ending_yesterday():
    assert window_bounds("daily", TODAY) == (YESTERDAY, YESTERDAY)
    assert window_bounds("weekly", TODAY) == (YESTERDAY - timedelta(days=6), YESTERDAY)
    assert window_bounds("annual", TODAY) == (YESTERDAY - timedelta(days=364), YESTERDAY)


def test_window_bounds_default_to_today():
    yesterday = date.today() - timedelta(days=1)
    assert window_bounds("daily") == (yesterday, yesterday)


def test_window_bounds_rejects_unknown_window():
    with pytest.raises(KeyError):
        window_bounds("bogus")


def test_resolve_when_from_window_name():
    assert resolve_when("daily", None, None, TODAY) == (YESTERDAY, YESTERDAY, "daily")


def test_resolve_when_since_overrides_window_and_defaults_until_to_yesterday():
    assert resolve_when("daily", date(2020, 1, 1), None, TODAY) == (
        date(2020, 1, 1),
        YESTERDAY,
        "backfill",
    )


def test_resolve_when_explicit_since_and_until():
    assert resolve_when(None, date(2020, 1, 1), date(2020, 6, 30)) == (
        date(2020, 1, 1),
        date(2020, 6, 30),
        "backfill",
    )


def test_resolve_when_needs_window_or_since():
    with pytest.raises(ValueError):
        resolve_when(None, None, None)


@pytest.mark.parametrize(
    ("day", "window"),
    [
        (date(2026, 1, 1), "annual"),
        (date(2026, 5, 1), "annual"),
        (date(2026, 9, 1), "annual"),  # a Tuesday
        (date(2026, 3, 9), "monthly"),  # a Monday
        (date(2026, 3, 10), "weekly"),
        (date(2026, 3, 15), "weekly"),  # a Sunday
    ],
)
def test_cadence_picks_the_widest_window_that_applies(day, window):
    assert cadence_window(day) == window


def test_annual_wins_over_monday():
    monday_first_of_june = date(2026, 6, 1)
    assert monday_first_of_june.isoweekday() == 1
    assert cadence_window(monday_first_of_june) == "monthly"  # 1 June is not an annual day
    assert cadence_window(date(2029, 1, 1)) == "annual"  # a Monday and an annual day
    assert date(2029, 1, 1).isoweekday() == 1
