# Línea de comandos

No hay fichero de configuración: todo se indica con opciones, y cada una tiene su variable de entorno para cuando se ejecuta de forma desatendida.

```console
$ bdns-sync [--version] COMANDO [OPCIONES]
```

| Comando | Para qué sirve |
| --- | --- |
| [`delta`](#delta) | La sincronización diaria, la que se programa |
| [`backfill`](#backfill) | La carga del histórico, que se hace una vez |
| [`sync`](#sync) | Sincronizar una sola entidad, con el periodo o el rango que le indiques |
| [`list`](#list) | Ver los nombres de las entidades |
| [`check-api`](#check-api) | Comprobar que la API no ha cambiado |

Los comandos que escriben en la base de datos admiten `--dry-run`, que muestra lo que harían, con las fechas concretas, sin tocar la API ni la base de datos. Usa exactamente el mismo código que una ejecución real.

## Opciones comunes

| Opción | Variable de entorno | Por defecto | Para qué sirve |
| --- | --- | --- | --- |
| `--target-url` | `BDNS_SYNC_TARGET_URL` | *obligatoria* | URL de SQLAlchemy de la base de datos de destino |
| `--max-retries` | `BDNS_SYNC_MAX_RETRIES` | `5` | Reintentos por petición cuando la API falla de forma pasajera |
| `--wait-time` | `BDNS_SYNC_WAIT_TIME` | `10` | Primera espera entre reintentos, en segundos; se duplica en cada uno hasta un máximo de 60 |
| `--max-workers` | `BDNS_SYNC_MAX_WORKERS` | `1` | Llamadas a la vez (páginas y detalles). Las buenas prácticas oficiales piden una; con más solo se va más rápido |
| `--rate-limit` | `BDNS_SYNC_RATE_LIMIT` | `9.5` | Peticiones por segundo (como mucho 10). El límite es por IP |
| `--max-reject-ratio` | | `0.10` | Parte del lote que puede ser inservible antes de rechazarlo |
| `--max-rejects` | | sin límite | Número máximo de registros inservibles, sea cual sea la proporción |
| `--dry-run` | | no | Muestra lo que haría y se detiene |

Con los valores por defecto, cada petición aguanta unos tres o cuatro minutos de problemas del servidor antes de que falle la ejecución. Los dos límites de rechazo son tolerancias de funcionamiento, no afirmaciones sobre los datos, así que se fijan en cada ejecución; por qué hay dos lo explica [`RejectLimits`][bdns.sync.sinks.RejectLimits].

## `delta`

```console
$ bdns-sync delta [--window PERIODO] [--skip-api-check] [OPCIONES COMUNES]
```

Comprueba que la API sigue tratando las fechas como siempre y, después, sincroniza todas las entidades completas y todas las incrementales con el periodo que toque ese día: `annual` el 1 de enero, el 1 de mayo y el 1 de septiembre, `monthly` los lunes y `weekly` el resto de días ([`cadence_window`][bdns.sync.windows.cadence_window]). Con `--window` puedes forzar otro.

Si la comprobación de la API detecta un cambio, no sincroniza nada y termina con código 1. Si falla una entidad, sigue con las demás y al terminar devuelve código 1 si alguna ha fallado. Lo explicamos en [sincronización diaria](../guides/scheduling.md).

## `backfill`

```console
$ bdns-sync backfill [--entity ENTIDAD]... [OPCIONES COMUNES]
```

Sincroniza las entidades completas y carga cada entidad incremental año a año, desde el principio de su histórico hasta ayer. Con `--entity`, que puedes repetir, limitas la carga a esas entidades. Lo explicamos en [carga inicial](../guides/backfill.md).

## `sync`

```console
$ bdns-sync sync ENTIDAD [--window PERIODO | --since FECHA [--until FECHA]] [OPCIONES COMUNES]
```

Sincroniza una entidad. Una entidad incremental necesita un periodo, ya sea con `--window` (`daily`, `weekly`, `monthly` o `annual`) o con un rango concreto (`--since` y, si quieres, `--until`, que por defecto es ayer). Una entidad completa no admite ninguno de los dos. Las fechas se escriben como `AAAA-MM-DD`.

En el nombre de la entidad da igual usar guiones o guiones bajos, así que `concesiones-busqueda`, que es como se llama el comando en `bdns-fetch`, también vale.

## `list`

```console
$ bdns-sync list [--kind full|windowed]
```

Escribe los nombres de las entidades, uno por línea y en el orden en que las sincroniza `delta`. `full` son las que se sincronizan enteras y `windowed`, las que se sincronizan por fecha de registro (también se acepta `search` en lugar de `windowed`).

## `check-api`

```console
$ bdns-sync check-api [--day AAAA-MM-DD]
```

Lanza contra el servicio real la comprobación de `bdns-fetch`, que confirma que `fechaRegFin` sigue sin incluir el último día, que `fechaHasta` sí lo incluye y que dos días seguidos no comparten registros. `delta` la ejecuta por su cuenta antes de sincronizar.

**Solo** termina con un código distinto de cero si la API devuelve datos válidos que contradicen ese comportamiento, que es el único caso en el que merece la pena pararlo todo. Si el problema es pasajero (una página de error, una parada por mantenimiento, un día de prueba sin datos), lo indica y termina con cero: bloquear un día entero por un bache costaría más de lo que se ahorra, y si la API está caída de verdad, las sincronizaciones fallarán igualmente.

## Entidades

=== "Completas"

    `sectores` · `actividades` · `finalidades` · `beneficiarios` ·
    `instrumentos` · `objetivos` · `organos` · `organos_agrupacion` ·
    `regiones` · `reglamentos` · `sanciones_busqueda` ·
    `grandesbeneficiarios_anios` · `grandesbeneficiarios_busqueda` ·
    `planesestrategicos_busqueda` · `planesestrategicos` ·
    `planesestrategicos_vigencia`

=== "Incrementales"

    `concesiones_busqueda` · `ayudasestado_busqueda` ·
    `minimis_busqueda` · `partidospoliticos_busqueda` ·
    `convocatorias_busqueda` · `convocatorias`

La lista actualizada te la da `bdns-sync list`, y su definición está en el [registro de entidades][bdns.sync.entities.ENTITIES].
