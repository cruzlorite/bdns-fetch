# Descargas incrementales

Esta guía explica cómo descargar lo registrado entre dos fechas sin perder ni repetir ningún día, incluso cuando el rango abarca varios años.

## Usa la fecha de registro, no la de concesión

Si lo que quieres es detectar altas y cambios, filtra por `fechaRegInicio` y `fechaRegFin`, que corresponden a la fecha en que el registro entró en la BDNS. `fechaDesde` y `fechaHasta` filtran por otra fecha (en las búsquedas de concesiones, la de concesión), y un registro dado de alta hoy puede tener una fecha de concesión de hace meses. Es lo mismo que recomiendan las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

La fecha de registro está disponible en `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda` y `partidospoliticos-busqueda`.

## Pide un rango cerrado y deja que el cliente lo traduzca

`fechaRegFin` **no incluye** el propio día, mientras que `fechaHasta` **sí lo incluye** ([por qué importa](../explanation/api-behavior.md#upper-bound)). Para no tener que acordarte de a cuál hay que sumarle un día, usa las funciones de [`dates`][bdns.fetch.dates]:

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import period_range, registration_range

client = BDNSClient()

# Todo lo registrado en enero, del 1 al 31, ambos incluidos.
enero = client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31)))

# Las convocatorias recibidas el 15 de enero.
dia = client.fetch_convocatorias_busqueda(**period_range(date(2024, 1, 15), date(2024, 1, 15)))
```

## Divide los rangos largos en semanas

Una consulta de varios años falla de vez en cuando con `ERR_MANTENIMIENTO_BBDD`, y la misma consulta dividida en semanas no falla ([las pruebas](../explanation/api-behavior.md#range-reliability)). Esto es lo que hace posibles las descargas grandes. [`split_range`][bdns.fetch.dates.split_range] divide un rango en tramos consecutivos de siete días como máximo:

```python
from bdns.fetch.dates import registration_range, split_range

def registradas(primero: date, ultimo: date):
    for desde, hasta in split_range(primero, ultimo):
        yield from client.fetch_concesiones_busqueda(**registration_range(desde, hasta))
```

Como cada tramo trata bien el extremo final, el resultado es el mismo sea cual sea el tamaño del tramo.

## No incluyas el día de hoy

El día en curso sigue recibiendo registros hasta la mañana siguiente, así que una descarga diaria debería terminar **ayer**. Si incluye hoy, deja un día a medias que nadie volverá a revisar.

## Comprueba que la API no ha cambiado

Todo lo anterior se apoya en un comportamiento que se ha medido, pero que la API no documenta. Antes de una descarga programada conviene comprobar que sigue siendo así:

```console
$ bdns-fetch check-api
Probed 2026-09-03: date semantics and record shape unchanged.
```

Solo termina con código 1 si la API devuelve datos válidos que contradicen ese comportamiento. Si el día de prueba no tiene datos o hay un error pasajero, lo indica y termina con 0. Desde Python tienes [`check_api_contract`][bdns.fetch.contract.check_api_contract].

## Si necesitas guardar el histórico

Detectar qué ha cambiado entre descargas, cerrar los registros que desaparecen y conservar todas las versiones es justo lo que hace [`bdns-sync`](https://cruzlorite.github.io/bdns-sync/), que se apoya en esta librería.
