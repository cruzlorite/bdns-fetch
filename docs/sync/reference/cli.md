# CLI

Sin fichero de configuración: todo va en opciones, cada una con su
variable de entorno para el uso desatendido.

```console
$ bdns-sync [--version] COMANDO [OPCIONES]
```

| Comando | Para qué |
| --- | --- |
| [`delta`](#delta) | La sincronización diaria, la que se programa |
| [`backfill`](#backfill) | La carga histórica, una vez |
| [`sync`](#sync) | Una entidad suelta, con la ventana o el rango que se le diga |
| [`list`](#list) | Los nombres de las entidades |
| [`check-api`](#check-api) | Comprobar que la API no ha cambiado |

Los comandos que escriben en el destino aceptan `--dry-run`: imprimen lo
que harían, con las fechas concretas, sin tocar la API ni el destino, por
el mismo camino de código que una ejecución real.

## Opciones comunes

| Opción | Variable de entorno | Por defecto | Qué hace |
| --- | --- | --- | --- |
| `--target-url` | `BDNS_SYNC_TARGET_URL` | *obligatoria* | URL de SQLAlchemy del destino |
| `--max-retries` | `BDNS_SYNC_MAX_RETRIES` | `5` | Reintentos por petición ante fallos transitorios de la API |
| `--wait-time` | `BDNS_SYNC_WAIT_TIME` | `10` | Espera inicial entre reintentos (s); se duplica, hasta 60 |
| `--rate-limit` | `BDNS_SYNC_RATE_LIMIT` | `9.5` | Peticiones por segundo (máximo 10). El límite es por IP |
| `--max-reject-ratio` | | `0.10` | Fracción del lote que puede ser inservible antes de rechazarlo |
| `--max-rejects` | | sin tope | Tope absoluto de registros inservibles, sea cual sea la fracción |
| `--dry-run` | | no | Imprime qué haría y para |

Con los valores por defecto, una petición aguanta unos 3-4 minutos de
problemas del servidor antes de que falle la ejecución. Los dos límites de
rechazo son tolerancias operativas, no afirmaciones sobre los datos, así
que se fijan por ejecución; el porqué de tener dos está en
[`RejectLimits`][bdns.sync.sinks.RejectLimits].

## `delta`

```console
$ bdns-sync delta [--window VENTANA] [--skip-api-check] [OPCIONES COMUNES]
```

Comprueba que la semántica de fechas de la API no ha cambiado, sincroniza
todas las entidades completas y después todas las de ventana, con la
ventana que toca hoy: `annual` el 1 de enero, mayo y septiembre, `monthly`
los lunes, `weekly` el resto
([`cadence_window`][bdns.sync.windows.cadence_window]). `--window` fuerza
otra.

Si la comprobación de la API detecta un cambio, no sincroniza nada y sale
con código 1. Si falla una entidad, sigue con las demás, y al terminar sale
con código 1 si alguna falló. Ver [operación programada](../guides/scheduling.md).

## `backfill`

```console
$ bdns-sync backfill [--entity ENTIDAD]... [OPCIONES COMUNES]
```

Sincroniza las entidades completas y carga cada entidad de ventana año a
año, desde el inicio de su histórico hasta ayer. `--entity`, repetible,
limita la carga a esas entidades. Ver [cargas iniciales y backfills](../guides/backfill.md).

## `sync`

```console
$ bdns-sync sync ENTIDAD [--window VENTANA | --since FECHA [--until FECHA]] [OPCIONES COMUNES]
```

Sincroniza una entidad. Una entidad de ventana necesita un rango: una
`--window` (`daily`, `weekly`, `monthly` o `annual`) o un rango explícito
con `--since`, y opcionalmente `--until` (por defecto, ayer). Una entidad
completa no admite ninguno. Las fechas van en `AAAA-MM-DD`.

Guiones y guiones bajos son intercambiables en el nombre:
`concesiones-busqueda`, el nombre del comando en `bdns-fetch`, también
vale.

## `list`

```console
$ bdns-sync list [--kind full|windowed]
```

Escribe los nombres de las entidades, uno por línea, en el orden en que
las sincroniza `delta`. `full` son las que se sincronizan enteras;
`windowed`, las que se sincronizan por ventana de fecha de registro
(`search` se acepta como sinónimo de `windowed`).

## `check-api`

```console
$ bdns-sync check-api [--day AAAA-MM-DD]
```

Ejecuta la comprobación de contrato de `bdns-fetch` contra el servicio
real: que `fechaRegFin` sigue siendo exclusivo, `fechaHasta` inclusivo y
los días consecutivos disjuntos. `delta` la ejecuta sola antes de
sincronizar.

Sale con código distinto de cero **solo** cuando la API devolvió datos
válidos que contradicen la semántica, que es el caso por el que merece la
pena parar. Un problema transitorio (una página de error, una ventana de
mantenimiento, un día de prueba vacío) se informa y sale con cero:
bloquear un día entero por un bache costaría más de lo que ahorra, y una
API realmente caída hace fallar las sincronizaciones de todas formas.

## Entidades

=== "Completas"

    `sectores` · `actividades` · `finalidades` · `beneficiarios` ·
    `instrumentos` · `objetivos` · `organos` · `organos_agrupacion` ·
    `regiones` · `reglamentos` · `sanciones_busqueda` ·
    `grandesbeneficiarios_anios` · `grandesbeneficiarios_busqueda` ·
    `planesestrategicos_busqueda` · `planesestrategicos` ·
    `planesestrategicos_vigencia`

=== "Por ventana de fecha de registro"

    `concesiones_busqueda` · `ayudasestado_busqueda` ·
    `minimis_busqueda` · `partidospoliticos_busqueda` ·
    `convocatorias_busqueda` · `convocatorias`

La lista viva la da `bdns-sync list`, y su definición es el
[registro de entidades][bdns.sync.entities.ENTITIES].
