# Cargas iniciales y backfills

La cadencia diaria solo alcanza 365 días de fecha de registro en su
ventana más ancha. Para traer el histórico completo a un destino nuevo
hace falta una carga inicial.

El repositorio trae una:
[`scripts/full_load.sh`](https://github.com/cruzlorite/bdns-sync/blob/main/scripts/full_load.sh).

```console
$ BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset /ruta/a/scripts/full_load.sh
```

Primero los catálogos de reemplazo completo, después el backfill profundo
de los incrementales.

!!! warning "Es un arranque para un destino **nuevo**"

    Lanzarlo contra uno ya poblado cierra de un golpe todas las filas
    almacenadas que la API ya no sirve — pasados unos años, todo lo que
    superó su periodo de publicación: 4 años naturales tras la concesión
    para `concesiones`, 10 para `ayudasestado` y `minimis`.

    Esas filas se cierran con la fecha en que corrió el backfill, no con
    la fecha en que caducaron. No se rompe nada, y la cadencia normal
    nunca hace esto porque su ventana más ancha llega a 365 días. Pero el
    cierre masivo se confunde fácilmente con un evento real. Ver
    [bajas por caducidad frente a retiradas reales](../explanation/data-caveats.md).

## Por qué se trocea en años

Los backfills se parten en tramos de un año con `--since`/`--until`. Cada
tramo confirma su propio diff SCD2, así que una caída pierde como mucho el
tramo en vuelo, nunca el backfill entero de varias horas.

No hay reanudación dentro de una ejecución. La recuperación es
sencillamente volver a lanzar desde el tramo que falló hacia abajo, y
repetir es seguro: SCD2 es idempotente, un registro ya sincronizado
simplemente se marca como visto, no se duplica.

## Backfill de una entidad suelta

```console
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31
```

`--since` manda sobre `--window`, y `--until` por defecto es ayer. La
ejecución queda anotada como `backfill` en `_sync_runs`, distinguible de
las de cadencia.

Comprueba antes qué haría:

```console
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31 --dry-run
```

## Hasta dónde llega el histórico

`bdns-sync` no lo sabe: es una pieza básica y no tiene idea de hasta dónde
llegan los datos de cada endpoint. Igual que `delta_load.sh` posee la
cadencia, `full_load.sh` posee las fechas de inicio y las pasa con
`--since`.

Las fechas por entidad del script son **suelos conservadores, no los
primeros registros exactos**. La API retiene un histórico acotado, y
consultar antes de esa retención solo devuelve semanas vacías con una
llamada barata cada una.

La profundidad medida por endpoint está en
[profundidad histórica](../explanation/bdns-api-behavior.md#history-depth).

## Qué esperar

Duraciones medidas en una carga inicial completa real (julio de 2026,
destino BigQuery, una sola máquina). El cuello de botella es siempre la
API de origen, nunca el destino:

| Carga | Filas | Duración |
|---|---|---|
| Los catálogos de reemplazo completo | ~150.000 | ~10 s la mayoría; `planesestrategicos` y `planesestrategicos_vigencia`, ~4 min cada uno (detalle por clave); `grandesbeneficiarios_busqueda`, ~2 min |
| `concesiones_busqueda` (desde 2020) | 27,7 M | ~2,5 h |
| `ayudasestado_busqueda` (desde 2015) | 6,4 M | ~2 h |
| `minimis_busqueda` (desde 2015) | 4,3 M | ~30 min |
| `convocatorias_busqueda` (desde 2013) | 636 K | ~6 min |
| `partidospoliticos_busqueda` (desde 2020) | 6 K | ~2 min |
| `convocatorias` (desde 2013) | 636 K | **~19 h** |

En total, una carga inicial completa ronda las **24 horas**, y se la lleva
casi entera `convocatorias`: cada código descubierto exige su propia
llamada de detalle, paralelizada justo por debajo del límite oficial de 10
peticiones por segundo. Es coste de API puro, no depende del motor de
destino. Los cortes puntuales de la API —timeouts, mantenimiento
nocturno— los absorben los reintentos con backoff del cliente.

Las cifras de throughput, límite de peticiones y solape
productor/consumidor están en
[rendimiento medido](../explanation/bdns-api-behavior.md#performance).

Un detalle a tener presente al terminar: una carga histórica masiva en una
sola pasada puede dejar algún par de duplicados residuales por la
inestabilidad de la paginación en fechas recientes. Cómo detectarlos y
limpiarlos está en
[duplicados residuales](../explanation/data-caveats.md).
