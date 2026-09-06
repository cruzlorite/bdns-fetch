"""The live API contract check.

The point of this check is that nothing else in the project looks at the
real service. `tests/fake_client.py` models the date semantics the engine
assumes, so if the BDNS ever changes them, every other test stays green
while production loses a day per chunk boundary. These tests therefore
have to prove the check actually fires, not just that it passes on
well-behaved input.
"""

from datetime import date, timedelta

from bdns.sync.api_contract import check_api_contract

DAY = date(2026, 8, 1)
NEXT = DAY + timedelta(days=1)


def minimis(day, n, start_id=0):
    return [
        {"idConcesion": f"{day.isoformat()}-{i + start_id}", "fechaRegistro": day.isoformat()}
        for i in range(n)
    ]


def convocatorias(day, n):
    return [
        {"numeroConvocatoria": f"C{day.isoformat()}-{i}", "fechaRecepcion": day.isoformat()}
        for i in range(n)
    ]


class FakeApi:
    """Models both date-parameter families, with each behavior switchable
    so a test can express "the API changed" precisely.
    """

    def __init__(self, *, reg_exclusive=True, hasta_inclusive=True, days=None, extra=None):
        self.reg_exclusive = reg_exclusive
        self.hasta_inclusive = hasta_inclusive
        self.days = days if days is not None else {DAY: 20, NEXT: 15}
        self.extra = extra or {}

    def _minimis_for(self, day):
        rows = minimis(day, self.days.get(day, 0))
        return [dict(row, **self.extra) for row in rows]

    def fetch_minimis_busqueda(self, fechaRegInicio, fechaRegFin, num_pages=1):
        day = fechaRegInicio
        while day < fechaRegFin if self.reg_exclusive else day <= fechaRegFin:
            yield from self._minimis_for(day)
            day += timedelta(days=1)

    def fetch_convocatorias_busqueda(self, fechaDesde, fechaHasta, num_pages=1):
        day = fechaDesde
        while day <= fechaHasta if self.hasta_inclusive else day < fechaHasta:
            yield from convocatorias(day, self.days.get(day, 0))
            day += timedelta(days=1)


def test_a_well_behaved_api_passes():
    status, messages = check_api_contract(FakeApi(), day=DAY)
    assert status == "ok", messages


def test_an_exclusive_upper_bound_turning_inclusive_is_caught():
    """If `fechaRegFin` started including its own day, every window would
    silently over-fetch a day at each chunk boundary.
    """
    status, messages = check_api_contract(FakeApi(reg_exclusive=False), day=DAY)
    assert status == "changed"
    assert any("fechaRegFin looks INCLUSIVE" in m for m in messages)


def test_an_inclusive_upper_bound_turning_exclusive_is_caught():
    """The mirror image on convocatorias' family. `fechaHasta=D` returning
    nothing for day D means discovery would drop its last day.
    """
    status, messages = check_api_contract(FakeApi(hasta_inclusive=False), day=DAY)
    assert status == "changed"
    assert any("fechaHasta looks EXCLUSIVE" in m for m in messages)


def test_overlapping_adjacent_days_are_caught():
    class Overlapping(FakeApi):
        def _minimis_for(self, day):
            # the same record shows up on both days
            return super()._minimis_for(day) + [
                {"idConcesion": "SHARED", "fechaRegistro": day.isoformat()}
            ]

    status, messages = check_api_contract(Overlapping(), day=DAY)
    assert status == "changed"
    assert any("adjacent days overlap" in m for m in messages)


def test_a_range_that_is_not_the_union_of_its_days_is_caught():
    """Chunking a window is only safe because a range equals the sum of its
    days. If that stopped holding, every monthly and annual window would
    lose records at the seams.
    """

    class Lossy(FakeApi):
        def fetch_minimis_busqueda(self, fechaRegInicio, fechaRegFin, num_pages=1):
            rows = list(super().fetch_minimis_busqueda(fechaRegInicio, fechaRegFin, num_pages))
            span_days = (fechaRegFin - fechaRegInicio).days
            yield from (rows[:-3] if span_days >= 2 else rows)

    status, messages = check_api_contract(Lossy(), day=DAY)
    assert status == "changed"
    assert any("not the union of its two days" in m for m in messages)


def test_records_without_a_usable_natural_key_are_caught():
    status, messages = check_api_contract(FakeApi(extra={"idConcesion": None}), day=DAY)
    assert status == "changed"
    assert any("no usable idConcesion" in m for m in messages)


def test_a_registration_date_that_stops_matching_the_filter_is_caught():
    """If the date parameters started filtering on a different field, the
    records would look fine and land under the wrong `_reg_date`, which is
    what window-scoped deletion detection compares against.
    """
    status, messages = check_api_contract(FakeApi(extra={"fechaRegistro": "1999-01-01"}), day=DAY)
    assert status == "changed"
    assert any("carry a different fechaRegistro" in m for m in messages)


# --- failing open ----------------------------------------------------------
#
# Transient trouble must never block a day's cadence. That would be the
# `set -e` mistake in another costume: this source has documented, regular
# maintenance blips, and the syncs themselves already fail loudly when the
# API is genuinely unreachable.


def test_empty_probe_days_are_inconclusive_not_a_failure():
    status, messages = check_api_contract(FakeApi(days={}), day=DAY)
    assert status == "inconclusive"
    assert any("Not treated as a failure" in m for m in messages)


def test_an_api_error_is_inconclusive_not_a_failure():
    class Broken(FakeApi):
        def fetch_minimis_busqueda(self, *args, **kwargs):
            raise RuntimeError("ERR_MANTENIMIENTO_BBDD")
            yield  # pragma: no cover

    status, _ = check_api_contract(Broken(), day=DAY)
    assert status == "inconclusive"


def test_a_quiet_day_falls_back_to_an_earlier_one():
    """A probe day can legitimately be empty (a holiday, a quiet weekend),
    so the check walks back rather than giving up on the first try.
    """
    quiet = {DAY - timedelta(days=2): 20, DAY - timedelta(days=1): 15}
    status, messages = check_api_contract(FakeApi(days=quiet), day=DAY)
    assert status == "ok", messages
