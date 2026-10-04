"""The contract check, against fake APIs that keep or break the documented semantics."""

from datetime import date, timedelta

from bdns.fetch.contract import check_api_contract

DAY = date(2024, 3, 13)


def _records(day: date, n: int = 3, prefix: str = "") -> list[dict]:
    iso = day.isoformat()
    return [
        {
            "idConcesion": f"{prefix}{iso}-{i}",
            "numeroConvocatoria": f"{iso}-{i}",
            "fechaRegistro": iso,
            "fechaRecepcion": iso,
        }
        for i in range(n)
    ]


class FakeAPI:
    """Serves 3 records a day. `exclusive_reg_fin` / `inclusive_hasta` set the semantics."""

    def __init__(self, exclusive_reg_fin=True, inclusive_hasta=True, empty_days=()):
        self.exclusive_reg_fin = exclusive_reg_fin
        self.inclusive_hasta = inclusive_hasta
        self.empty_days = set(empty_days)

    def _days(self, first, last):
        day = first
        while day <= last:
            if day not in self.empty_days:
                yield day
            day += timedelta(days=1)

    def fetch_minimis_busqueda(self, *, fechaRegInicio, fechaRegFin):
        last = fechaRegFin - timedelta(days=1) if self.exclusive_reg_fin else fechaRegFin
        return [r for d in self._days(fechaRegInicio, last) for r in _records(d)]

    def fetch_convocatorias_busqueda(self, *, fechaDesde, fechaHasta):
        last = fechaHasta if self.inclusive_hasta else fechaHasta - timedelta(days=1)
        return [r for d in self._days(fechaDesde, last) for r in _records(d)]


def test_documented_semantics_pass():
    report = check_api_contract(FakeAPI(), day=DAY)
    assert report.status == "ok", report.messages


def test_an_inclusive_fecha_reg_fin_is_a_change():
    report = check_api_contract(FakeAPI(exclusive_reg_fin=False), day=DAY)
    assert report.status == "changed"
    assert any("fechaRegFin looks INCLUSIVE" in m for m in report.messages)


def test_an_exclusive_fecha_hasta_is_a_change():
    report = check_api_contract(FakeAPI(inclusive_hasta=False), day=DAY)
    assert report.status == "changed"
    assert any("fechaHasta looks EXCLUSIVE" in m for m in report.messages)


def test_empty_days_are_skipped_for_an_earlier_one():
    report = check_api_contract(FakeAPI(empty_days={DAY}), day=DAY)
    assert report.status == "ok"
    assert str(DAY - timedelta(days=1)) in report.messages[0]


def test_errors_on_every_day_are_inconclusive():
    class Down:
        def fetch_minimis_busqueda(self, **kwargs):
            raise ConnectionError("down")

    report = check_api_contract(Down(), day=DAY)
    assert report.status == "inconclusive"
