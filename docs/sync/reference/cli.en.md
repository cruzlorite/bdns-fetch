# Command line

No configuration file: everything is an option, each with its
environment variable for unattended use.

```console
$ bdns-sync [--version] COMMAND [OPTIONS]
```

| Command | What for |
| --- | --- |
| [`delta`](#delta) | The daily sync, the one you schedule |
| [`backfill`](#backfill) | The historical load, once |
| [`sync`](#sync) | A single entity, with the window or range given |
| [`list`](#list) | The entity names |
| [`check-api`](#check-api) | Check that the API has not changed |

Commands that write to the target take `--dry-run`: they print what they
would do, with concrete dates, without touching the API or the target,
through the same code path as a real run.

## Common options

| Option | Environment variable | Default | What it does |
| --- | --- | --- | --- |
| `--target-url` | `BDNS_SYNC_TARGET_URL` | *required* | SQLAlchemy URL of the target |
| `--max-retries` | `BDNS_SYNC_MAX_RETRIES` | `5` | Retries per request on transient API failures |
| `--wait-time` | `BDNS_SYNC_WAIT_TIME` | `10` | Initial wait between retries (s); doubles, up to 60 |
| `--max-workers` | `BDNS_SYNC_MAX_WORKERS` | `1` | Concurrent calls (pages and details). The official good practices ask for one; more only go faster |
| `--rate-limit` | `BDNS_SYNC_RATE_LIMIT` | `9.5` | Requests per second (at most 10). The limit is per IP |
| `--max-reject-ratio` | | `0.10` | Share of a batch that may be unusable before it is refused |
| `--max-rejects` | | no cap | Absolute cap on unusable records, whatever the share |
| `--dry-run` | | off | Print what would be done and stop |

With the defaults, a request rides out about 3-4 minutes of server
trouble before the run fails. The two reject limits are operational
tolerances, not statements about the data, so they are set per run; why
there are two is in [`RejectLimits`][bdns.sync.sinks.RejectLimits].

## `delta`

```console
$ bdns-sync delta [--window WINDOW] [--skip-api-check] [COMMON OPTIONS]
```

Checks that the API's date semantics have not changed, syncs every full
entity and then every windowed one, with the window today calls for:
`annual` on 1 January, May and September, `monthly` on Mondays, `weekly`
otherwise ([`cadence_window`][bdns.sync.windows.cadence_window]).
`--window` forces another.

If the API check detects a change, nothing is synced and it exits with
code 1. If an entity fails, it carries on with the rest, and exits with
code 1 at the end if any failed. See [scheduled operation](../guides/scheduling.md).

## `backfill`

```console
$ bdns-sync backfill [--entity ENTITY]... [COMMON OPTIONS]
```

Syncs the full entities and loads each windowed entity year by year, from
the start of its history up to yesterday. `--entity`, repeatable, limits
the load to those entities. See [initial loads and backfills](../guides/backfill.md).

## `sync`

```console
$ bdns-sync sync ENTITY [--window WINDOW | --since DATE [--until DATE]] [COMMON OPTIONS]
```

Syncs one entity. A windowed entity needs a range: a `--window` (`daily`,
`weekly`, `monthly` or `annual`) or an explicit range with `--since` and
optionally `--until` (default yesterday). A full entity takes neither.
Dates are `YYYY-MM-DD`.

Hyphens and underscores are interchangeable in the name:
`concesiones-busqueda`, the command name in `bdns-fetch`, works too.

## `list`

```console
$ bdns-sync list [--kind full|windowed]
```

Writes the entity names, one per line, in the order `delta` syncs them.
`full` are the ones synced whole; `windowed`, the ones synced by
registration-date window (`search` is accepted as a synonym).

## `check-api`

```console
$ bdns-sync check-api [--day YYYY-MM-DD]
```

Runs `bdns-fetch`'s contract check against the live service: that
`fechaRegFin` is still exclusive, `fechaHasta` inclusive and consecutive
days disjoint. `delta` runs it on its own before syncing.

It exits non-zero **only** when the API returned valid data contradicting
the semantics, the one case worth stopping for. Transient trouble (an
error page, a maintenance window, an empty probe day) is reported and
exits zero: blocking a whole day over a blip would cost more than it
saves, and a genuinely unreachable API makes the syncs fail anyway.

## Entities

=== "Full"

    `sectores` · `actividades` · `finalidades` · `beneficiarios` ·
    `instrumentos` · `objetivos` · `organos` · `organos_agrupacion` ·
    `regiones` · `reglamentos` · `sanciones_busqueda` ·
    `grandesbeneficiarios_anios` · `grandesbeneficiarios_busqueda` ·
    `planesestrategicos_busqueda` · `planesestrategicos` ·
    `planesestrategicos_vigencia`

=== "By registration-date window"

    `concesiones_busqueda` · `ayudasestado_busqueda` ·
    `minimis_busqueda` · `partidospoliticos_busqueda` ·
    `convocatorias_busqueda` · `convocatorias`

The live list comes from `bdns-sync list`, and its definition is the
[entity registry][bdns.sync.entities.ENTITIES].
