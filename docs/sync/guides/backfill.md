# Cargas iniciales y backfills

La cadencia diaria alcanza como mucho 365 días de fecha de registro. Para
traer el histórico completo a un destino nuevo hace falta una carga
inicial:

```console
$ BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset bdns-sync backfill
```

Primero sincroniza las entidades completas y después carga cada entidad
de ventana **año a año**, desde el inicio de su histórico hasta ayer.
Para ver el plan sin ejecutar nada:

```console
$ bdns-sync backfill --dry-run
target      bigquery://proyecto/dataset
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
  sectores: complete state
  ...
  concesiones_busqueda: backfill [2020-01-01 .. 2020-12-31]
  concesiones_busqueda: backfill [2021-01-01 .. 2021-12-31]
  ...
```

!!! warning "Es un arranque para un destino **nuevo**"

    Lanzarlo contra uno ya poblado cierra de un golpe las filas almacenadas
    que la API ya no sirve: pasados unos años, todo lo que superó su
    periodo de publicación (4 años naturales tras la concesión para
    `concesiones`, 10 para `ayudasestado` y `minimis`).

    Esas filas se cierran con motivo `removed`, la fecha y el `run_id`
    del backfill, no con la fecha en que caducaron. No se rompe nada, y la
    cadencia normal nunca hace esto porque su ventana más ancha llega a
    365 días; pero el cierre masivo se confunde fácilmente con un evento
    real. Ver [bajas por caducidad frente a retiradas reales](../explanation/data-caveats.md).

## Por qué año a año

Cada año es una ejecución propia, con su propio diff SCD2 confirmado, así
que una caída pierde como mucho el año en vuelo, nunca un backfill de
varias horas. Una entidad que falla no detiene a las demás; al final se
informa de cuáles fallaron y el código de salida es 1.

No hay reanudación dentro de una ejecución. Se recupera volviendo a
lanzar, y repetir es seguro: SCD2 es idempotente, un registro ya
sincronizado solo se marca como visto, no se duplica.

## Una entidad, o un rango concreto

```console
$ bdns-sync backfill --entity convocatorias --entity convocatorias_busqueda
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31
```

`--entity` limita el backfill a esas entidades. `sync --since` carga un
rango a mano; `--until` por defecto es ayer. Las dos ejecuciones quedan
anotadas como `backfill` en `_sync_runs`, con el rango que cubrieron.

## Hasta dónde llega el histórico

Cada entidad de ventana declara en el
[registro de entidades][bdns.sync.entities] desde cuándo cargarla. Son
**suelos conservadores, no los primeros registros**: la API retiene un
histórico acotado, y consultar antes solo devuelve semanas vacías con una
llamada barata cada una. Ver
[hasta dónde llega el histórico](../explanation/sync-behavior.md#history-depth).

## Qué esperar

Duraciones medidas en una carga inicial completa real (julio de 2026,
destino BigQuery, una sola máquina). El cuello de botella es siempre la
API de origen, nunca el destino:

| Carga | Filas | Duración |
|---|---|---|
| Las entidades completas | ~150.000 | ~10 s la mayoría; `planesestrategicos` y `planesestrategicos_vigencia`, ~4 min cada una (detalle por clave); `grandesbeneficiarios_busqueda`, ~2 min |
| `concesiones_busqueda` (desde 2020) | 27,7 M | ~2,5 h |
| `ayudasestado_busqueda` (desde 2015) | 6,4 M | ~2 h |
| `minimis_busqueda` (desde 2015) | 4,3 M | ~30 min |
| `convocatorias_busqueda` (desde 2013) | 636 K | ~6 min |
| `partidospoliticos_busqueda` (desde 2020) | 6 K | ~2 min |
| `convocatorias` (desde 2013) | 636 K | **~19 h** |

En total, una carga inicial completa ronda las **24 horas**, y casi todo
es `convocatorias`: cada código descubierto exige su propia llamada de
detalle, al ritmo que permite la API. Es coste de API puro, no depende del
motor de destino. Los cortes puntuales de la API (timeouts, mantenimiento
nocturno) los absorben los reintentos del cliente
([rendimiento](../explanation/sync-behavior.md#performance)).

Al terminar, ten presente que una carga histórica masiva en una sola
pasada puede dejar algún par de duplicados residuales por la
inestabilidad de la paginación en fechas recientes. Cómo detectarlos y
limpiarlos: [duplicados residuales](../explanation/data-caveats.md).
