# Descargas incrementales

Cómo descargar "lo que se registró entre tal día y tal otro" sin perder ni duplicar un solo día, también en rangos de años.

## Usa la fecha de registro, no la de concesión

Para detectar altas y cambios, filtra por `fechaRegInicio`/`fechaRegFin`, la fecha en que el registro entró en la BDNS. `fechaDesde`/`fechaHasta` filtran por otra fecha (la de concesión, en las búsquedas de concesiones): un registro dado de alta hoy puede tener una fecha de concesión de hace meses. Así lo indican también las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

La fecha de registro existe en `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda` y `partidospoliticos-busqueda`.

## Pide un rango inclusivo y deja que el cliente traduzca

`fechaRegFin` es **exclusivo** y `fechaHasta` **inclusivo** ([por qué importa](../explanation/api-behavior.md#upper-bound)). En vez de recordar a qué familia sumarle un día, usa los helpers de [`dates`][bdns.fetch.dates]:

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import period_range, registration_range

client = BDNSClient()

# Todo lo registrado en enero, del 1 al 31 incluidos.
enero = client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31)))

# Convocatorias recibidas el 15 de enero.
dia = client.fetch_convocatorias_busqueda(**period_range(date(2024, 1, 15), date(2024, 1, 15)))
```

## Trocea los rangos largos

Un rango de varios años falla de forma intermitente con `ERR_MANTENIMIENTO_BBDD`; uno de una semana no ([medición](../explanation/api-behavior.md#range-reliability)). [`split_range`][bdns.fetch.dates.split_range] parte un rango en tramos contiguos de 7 días como máximo:

```python
from bdns.fetch.dates import registration_range, split_range

def registradas(primero: date, ultimo: date):
    for desde, hasta in split_range(primero, ultimo):
        yield from client.fetch_concesiones_busqueda(**registration_range(desde, hasta))
```

Como cada tramo usa el extremo correcto, el resultado no depende del tamaño del tramo.

## No pidas el día de hoy

El día en curso sigue recibiendo registros hasta la mañana siguiente. Una descarga incremental diaria debería terminar en **ayer**; si incluye hoy, deja un día a medias que nada vuelve a mirar.

## Comprueba que la API no ha cambiado

Todo lo anterior descansa en una semántica medida, no documentada. Antes de una descarga programada, comprueba que sigue siendo cierta:

```console
$ bdns-fetch check-api
Probed 2026-09-03: date semantics and record shape unchanged.
```

Sale con código 1 solo si la API devolvió datos válidos que contradicen la semántica; un día vacío o un error pasajero se informan y salen con 0. Desde Python: [`check_api_contract`][bdns.fetch.contract.check_api_contract].

## Si quieres histórico versionado

Detectar qué cambió entre descargas, cerrar registros dados de baja y guardar el histórico es justo lo que hace [`bdns-sync`](https://cruzlorite.github.io/bdns-sync/), sobre esta misma librería.
