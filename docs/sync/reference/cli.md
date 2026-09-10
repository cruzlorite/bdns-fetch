# CLI

Una invocación sincroniza un endpoint. Sin fichero de configuración: todo
va en flags, y qué sincronizar y cuándo lo decide quien orquesta.

```console
$ bdns-sync [--version] COMANDO [OPCIONES]
```

## `sync`

```console
$ bdns-sync sync ENDPOINT [OPCIONES]
```

Sincroniza un endpoint. Los incrementales (los grandes de búsqueda, más
`convocatorias`) necesitan un rango de fecha de registro: o un `--window`
en cascada, o un `--since`/`--until` explícito. Los de reemplazo completo
ignoran los tres.

| Opción | Qué hace |
| --- | --- |
| `--target-url` | URL de SQLAlchemy del destino. **Obligatoria.** Variable de entorno: `BDNS_SYNC_TARGET_URL` |
| `--window` | Ventana en cascada: `daily`, `weekly`, `monthly` o `annual` |
| `--since` | Inicio de un backfill (`YYYY-MM-DD`). Manda sobre `--window` |
| `--until` | Fin del backfill. Por defecto, ayer. Solo con `--since` |
| `--max-reject-ratio` | Fracción del lote que puede ser inservible antes de rechazarlo. Por defecto `0.10` |
| `--max-rejects` | Tope absoluto de registros inservibles, sea cual sea la fracción |
| `--dry-run` | Resuelve e imprime qué haría, y para. No toca ni la API ni el destino |

Los dos límites de rechazo son tolerancias operativas, no afirmaciones
sobre los datos, así que se fijan por ejecución. El porqué de tener dos, y
no uno, está en
[`RejectLimits`](api/sinks.md#bdns.sync.sinks.RejectLimits).

## `list`

```console
$ bdns-sync list [--kind full|search]
```

Escribe los nombres de endpoint conocidos, uno por línea, para consumir
desde un script sin listas escritas a mano.

`full` son los de reemplazo completo; `search` los incrementales por fecha
de registro.

## `check-api`

```console
$ bdns-sync check-api [--day YYYY-MM-DD]
```

Pregunta al servicio real si sigue comportándose como el motor supone.

Sale con código distinto de cero **solo** cuando la API devolvió datos
válidos que contradicen un invariante, que es el caso por el que merece la
pena parar. Un problema transitorio —una página de error, una ventana de
mantenimiento, un día de sondeo vacío— se informa y sale con cero:
bloquear la cadencia de un día entero por un bache costaría mucho más de
lo que ahorra, y una API realmente caída hace fallar las sincronizaciones
de todas formas.

Pensado para lanzarlo una vez antes de la cadencia del día, no dentro de
cada sincronización.

## Endpoints

=== "Reemplazo completo"

    `sectores` · `actividades` · `finalidades` · `beneficiarios` ·
    `instrumentos` · `objetivos` · `regiones` · `sanciones_busqueda` ·
    `organos` · `organos_agrupacion` · `reglamentos` ·
    `grandesbeneficiarios_anios` · `grandesbeneficiarios_busqueda` ·
    `planesestrategicos_busqueda` · `planesestrategicos` ·
    `planesestrategicos_vigencia`

=== "Incrementales por fecha de registro"

    `concesiones_busqueda` · `ayudasestado_busqueda` ·
    `minimis_busqueda` · `partidospoliticos_busqueda` ·
    `convocatorias_busqueda` · `convocatorias`

La lista viva la da `bdns-sync list`; esta es solo para leer.
