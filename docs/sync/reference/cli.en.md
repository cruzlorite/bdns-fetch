# CLI

One invocation syncs one endpoint. No configuration file: everything goes
in flags, and what to sync and when is decided by whoever orchestrates.

```console
$ bdns-sync [--version] COMMAND [OPTIONS]
```

## `sync`

```console
$ bdns-sync sync ENDPOINT [OPTIONS]
```

Syncs one endpoint. The incremental ones (the big search endpoints, plus
`convocatorias`) need a registration-date range: either a cascade
`--window` or an explicit `--since`/`--until`. Full-replace endpoints
ignore all three.

| Option | What it does |
| --- | --- |
| `--target-url` | SQLAlchemy URL of the target. **Required.** Environment variable: `BDNS_SYNC_TARGET_URL` |
| `--window` | Cascade window: `daily`, `weekly`, `monthly` or `annual` |
| `--since` | Start of a backfill (`YYYY-MM-DD`). Wins over `--window` |
| `--until` | End of the backfill. Defaults to yesterday. Only with `--since` |
| `--max-reject-ratio` | Share of the batch that may be unusable before the run refuses it. Defaults to `0.10` |
| `--max-rejects` | Absolute cap on unusable records, whatever the share |
| `--dry-run` | Resolve and print what it would do, then stop. Touches neither the API nor the target |

Both reject limits are operational tolerances, not statements about the
data, so they are set per run. Why there are two rather than one is in
[`RejectLimits`](api/sinks.md#bdns.sync.sinks.RejectLimits).

## `list`

```console
$ bdns-sync list [--kind full|search]
```

Prints the known endpoint names, one per line, for scripts to consume
without hand-maintained lists.

`full` are the full-replace endpoints; `search` the registration-date
incremental ones.

## `check-api`

```console
$ bdns-sync check-api [--day YYYY-MM-DD]
```

Asks the real service whether it still behaves the way the engine
assumes.

It exits non-zero **only** when the API returned valid data that
contradicts an invariant, which is the case worth stopping for. Transient
trouble — an error page, a maintenance window, an empty probe day — is
reported and exits zero: blocking a whole day's cadence over a blip would
cost far more than it saves, and a genuinely unreachable API makes the
syncs fail anyway.

Meant to run once before the day's cadence, not inside every sync.

## Endpoints

=== "Full replace"

    `sectores` · `actividades` · `finalidades` · `beneficiarios` ·
    `instrumentos` · `objetivos` · `regiones` · `sanciones_busqueda` ·
    `organos` · `organos_agrupacion` · `reglamentos` ·
    `grandesbeneficiarios_anios` · `grandesbeneficiarios_busqueda` ·
    `planesestrategicos_busqueda` · `planesestrategicos` ·
    `planesestrategicos_vigencia`

=== "Registration-date incremental"

    `concesiones_busqueda` · `ayudasestado_busqueda` ·
    `minimis_busqueda` · `partidospoliticos_busqueda` ·
    `convocatorias_busqueda` · `convocatorias`

The live list comes from `bdns-sync list`; this one is only for reading.
