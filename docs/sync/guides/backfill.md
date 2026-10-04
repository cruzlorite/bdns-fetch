# Carga inicial

La sincronización diaria repasa como mucho los últimos 365 días de fecha de registro, así que para tener el histórico completo en una base de datos nueva hay que hacer antes una carga inicial:

```console
$ BDNS_SYNC_TARGET_URL=bigquery://proyecto/dataset bdns-sync backfill
```

Primero sincroniza las entidades completas y después carga cada entidad incremental **año a año**, desde el principio de su histórico hasta ayer. Si quieres ver el plan sin ejecutar nada:

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

!!! warning "Está pensada para una base de datos **nueva**"

    Si la lanzas sobre una base de datos que ya tiene datos, cerrará de golpe todas las filas guardadas que la API ya no devuelve, es decir, todo lo que haya superado su periodo de visualización (cuatro años naturales después de la concesión en `concesiones` y diez en `ayudasestado` y `minimis`).

    Esas filas se cierran con el motivo `removed` y con la fecha y el `run_id` de la carga, no con la fecha en que caducaron. No se rompe nada, y la sincronización diaria nunca lo hace porque su periodo más largo es de 365 días, pero un cierre masivo así se confunde fácilmente con algo que ha pasado de verdad. Lo explicamos en [bajas por caducidad y bajas de verdad](../explanation/data-caveats.md).

## Por qué año a año

Cada año se carga en una ejecución independiente que confirma sus propios cambios, así que si algo falla solo se pierde el año que estaba en curso y no una carga de varias horas. Si falla una entidad, las demás siguen, y al terminar se muestra cuáles han fallado y el comando devuelve código 1.

No se puede retomar una ejecución a medias. Para recuperarte basta con volver a lanzarla, y repetirla no da problemas: un registro que ya está sincronizado solo se marca como visto, no se duplica.

## Una sola entidad o un rango concreto

```console
$ bdns-sync backfill --entity convocatorias --entity convocatorias_busqueda
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31
```

Con `--entity` limitas la carga a esas entidades. Con `sync --since` cargas un rango a mano; si no indicas `--until`, llega hasta ayer. Las dos ejecuciones quedan anotadas en `_sync_runs` como `backfill`, junto con el rango que cubrieron.

## Hasta dónde llega el histórico

Cada entidad incremental indica en el [registro de entidades][bdns.sync.entities] desde qué fecha cargarla. Son **fechas prudentes, no la del primer registro**: la API solo guarda un histórico limitado, y pedir fechas anteriores solo devuelve semanas vacías, cada una con una sola llamada. Lo explicamos en [hasta dónde llega el histórico](../explanation/sync-behavior.md#history-depth).

## Cuánto tarda

Estos tiempos se midieron en una carga inicial completa real (julio de 2026, con BigQuery como destino, desde una sola máquina y con varias llamadas a la vez: 5 al paginar y 8 en los detalles). Lo que marca el ritmo es siempre la API o la escritura, nunca nuestro código:

| Carga | Filas | Duración |
|---|---|---|
| Las entidades completas, casi todas | unas 150.000 en total | unos 10 segundos cada una |
| `grandesbeneficiarios_busqueda` | | unos 2 minutos |
| `planesestrategicos` y `planesestrategicos_vigencia`, que piden el detalle de cada plan | | unos 4 minutos cada una |
| `concesiones_busqueda` (desde 2020) | 27,7 millones | unas 2 horas y media |
| `ayudasestado_busqueda` (desde 2015) | 6,4 millones | unas 2 horas |
| `minimis_busqueda` (desde 2015) | 4,3 millones | unos 30 minutos |
| `convocatorias_busqueda` (desde 2013) | 636.000 | unos 6 minutos |
| `partidospoliticos_busqueda` (desde 2020) | 6.000 | unos 2 minutos |
| `convocatorias` (desde 2013) | 636.000 | **unas 19 horas** |

Casi todo el tiempo se lo lleva `convocatorias`, porque cada código necesita su propia llamada para pedir el detalle y son 636.000 llamadas al máximo de peticiones por segundo que permite la API: ni con más llamadas a la vez puede bajar de unas 18 horas y media. Con una llamada cada vez tardará lo mismo si el servidor responde rápido, y más si va cargado.

Con una llamada cada vez, que es lo que hace por defecto, las búsquedas paginadas (`concesiones_busqueda`, `ayudasestado_busqueda` y `minimis_busqueda`) sí tardarán más que en la tabla. En nuestras pruebas, sincronizar una semana de concesiones con SQLite como destino pasó de 27 a 63 segundos; con BigQuery la diferencia debería ser menor, porque escribir allí es más lento que descargar, pero no lo hemos medido. Si necesitas terminar antes, puedes subir `--max-workers` sabiendo que te apartas de la recomendación oficial ([rendimiento](../explanation/sync-behavior.md#performance)). Los cortes puntuales de la API (tiempos de espera agotados, mantenimiento nocturno) los resuelven los reintentos del cliente.

Cuando termine, ten en cuenta que una carga histórica muy grande hecha de una sola vez puede dejar alguna pareja de duplicados por cómo pagina la API las fechas recientes. Cómo encontrarlos y eliminarlos lo tienes en [duplicados que pueden quedar tras una carga histórica](../explanation/data-caveats.md).
