from datetime import date

import pytest

from bdns.fetch.dates import MAX_RANGE_DAYS, period_range, registration_range, split_range

D = date(2024, 1, 1)


def test_registration_range_makes_the_exclusive_bound_cover_the_last_day():
    assert registration_range(D, date(2024, 1, 7)) == {
        "fechaRegInicio": D,
        "fechaRegFin": date(2024, 1, 8),
    }


def test_period_range_is_inclusive():
    assert period_range(D, date(2024, 1, 7)) == {"fechaDesde": D, "fechaHasta": date(2024, 1, 7)}


def test_split_range_covers_every_day_once_in_order():
    pieces = list(split_range(D, date(2024, 1, 20)))
    assert pieces == [
        (date(2024, 1, 1), date(2024, 1, 7)),
        (date(2024, 1, 8), date(2024, 1, 14)),
        (date(2024, 1, 15), date(2024, 1, 20)),
    ]
    assert MAX_RANGE_DAYS == 7


def test_split_range_of_one_day():
    assert list(split_range(D, D)) == [(D, D)]


@pytest.mark.parametrize(("first", "last", "days"), [(D, date(2023, 12, 31), 7), (D, D, 0)])
def test_split_range_rejects_nonsense(first, last, days):
    with pytest.raises(ValueError):
        list(split_range(first, last, days))
