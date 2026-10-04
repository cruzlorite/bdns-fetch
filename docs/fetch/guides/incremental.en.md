# Incremental downloads

How to download "what was registered between this day and that one" without losing or duplicating a single day, even over ranges of years.

## Use the registration date, not the award date

To detect new and changed records, filter by `fechaRegInicio`/`fechaRegFin`, the date the record entered the BDNS. `fechaDesde`/`fechaHasta` filter by another date (the award date, on the award searches): a record registered today can carry an award date months back. The [official good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) say the same.

The registration date exists on `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda` and `partidospoliticos-busqueda`.

## Add a day to `fechaRegFin`

`fechaRegFin` is **exclusive** and `fechaHasta` **inclusive** ([why it matters](../explanation/api-behavior.md#upper-bound)), so to ask up to a given day by registration date you pass the day after:

```python
from datetime import date

from bdns.fetch import BDNSClient

client = BDNSClient()

# Everything registered in January, 1st to 31st: fechaRegFin is 1 February.
awards = client.fetch_concesiones_busqueda(fechaRegInicio=date(2024, 1, 1), fechaRegFin=date(2024, 2, 1))

# Calls received on 15 January: fechaHasta is that same day.
calls = client.fetch_convocatorias_busqueda(fechaDesde=date(2024, 1, 15), fechaHasta=date(2024, 1, 15))
```

## Split long ranges

A multi-year range fails intermittently with `ERR_MANTENIMIENTO_BBDD`; a week-long one does not ([measurement](../explanation/api-behavior.md#range-reliability)). [`split_range`][bdns.fetch.dates.split_range] cuts a range into contiguous pieces of at most 7 days:

```python
from datetime import timedelta

from bdns.fetch.dates import split_range

def registered(first: date, last: date):
    for start, end in split_range(first, last):
        yield from client.fetch_concesiones_busqueda(fechaRegInicio=start, fechaRegFin=end + timedelta(days=1))
```

Since each piece uses the right bound, the result does not depend on the piece size.

## Do not ask for today

The current day keeps receiving records until the next morning. A daily incremental download should end **yesterday**; including today leaves a half-finished day behind that nothing revisits.

## Check that the API has not changed

All of the above rests on measured, undocumented semantics. Before a scheduled download, check they still hold:

```console
$ bdns-fetch check-api
Probed 2026-09-03: date semantics and record shape unchanged.
```

It exits 1 only when the API returned valid data contradicting the semantics; an empty day or a passing error is reported and exits 0. From Python: [`check_api_contract`][bdns.fetch.contract.check_api_contract].

## If you want versioned history

Detecting what changed between downloads, closing withdrawn records and keeping history is exactly what [`bdns-sync`](../../sync/index.md) does, on top of this library.
