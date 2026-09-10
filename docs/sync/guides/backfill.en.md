# Initial loads and backfills

The daily cadence reaches 365 days of registration date at its widest.
Bringing the full history into a new target takes an initial load.

The repository ships one:
[`scripts/full_load.sh`](https://github.com/cruzlorite/bdns-sync/blob/main/scripts/full_load.sh).

```console
$ BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/full_load.sh
```

Full-replace catalogs first, then the deep backfill of the incremental
endpoints.

!!! warning "A bootstrap for a **new** target"

    Running it against a populated one closes, in one go, every stored
    row the API no longer serves — after a few years, everything past its
    publication period: 4 calendar years after the concession for
    `concesiones`, 10 for `ayudasestado` and `minimis`.

    Those rows are closed with the date the backfill ran, not the date
    they expired. Nothing breaks, and the normal cadence never does this
    because its widest window reaches 365 days. But the bulk closure is
    easy to mistake for a real event. See
    [expiry closures versus real withdrawals](../explanation/data-caveats.md).

## Why it is sliced by year

Backfills are split into one-year slices with `--since`/`--until`. Each
slice commits its own SCD2 diff, so a crash loses at most the slice in
flight, never the whole multi-hour backfill.

There is no resume within a run. Recovery is simply running again from
the failed slice down, and repeating is safe: SCD2 is idempotent, and an
already-synced record is just marked as seen, not duplicated.

## Backfilling a single entity

```console
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31
```

`--since` wins over `--window`, and `--until` defaults to yesterday. The
run is recorded as `backfill` in `_sync_runs`, distinct from cadence
runs.

Check what it would do first:

```console
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31 --dry-run
```

## How far back the history goes

`bdns-sync` does not know: it is a primitive and has no idea how far back
each endpoint's data reaches. Just as `delta_load.sh` owns the cadence,
`full_load.sh` owns the start dates and passes them with `--since`.

The per-entity dates in the script are **conservative floors, not the
exact first records**. The API retains a bounded history, and querying
before it only returns empty weeks, one cheap call each.

The depth measured per endpoint is in
[historical depth](../explanation/bdns-api-behavior.md#history-depth).

## What to expect

Durations measured on a real full bootstrap (July 2026, BigQuery
target, single machine). The bottleneck is always the source API, never
the target:

| Load | Rows | Duration |
|---|---|---|
| The full-replace catalogs | ~150K | ~10 s most; `planesestrategicos` and `planesestrategicos_vigencia` ~4 min each (per-key detail), `grandesbeneficiarios_busqueda` ~2 min |
| `concesiones_busqueda` (since 2020) | 27.7 M | ~2.5 h |
| `ayudasestado_busqueda` (since 2015) | 6.4 M | ~2 h |
| `minimis_busqueda` (since 2015) | 4.3 M | ~30 min |
| `convocatorias_busqueda` (since 2013) | 636 K | ~6 min |
| `partidospoliticos_busqueda` (since 2020) | 6 K | ~2 min |
| `convocatorias` (since 2013) | 636 K | **~19 h** |

A full bootstrap totals around **24 hours**, almost all of it
`convocatorias`: every discovered code needs its own detail call,
parallelized just under the official cap of 10 requests per second. It is
pure API cost, independent of the target engine. Transient API outages —
timeouts, nightly maintenance — are absorbed by the client's backoff
retries.

The figures for throughput, rate limit and producer/consumer overlap are
in [measured performance](../explanation/bdns-api-behavior.md#performance).

One thing to keep in mind once it finishes: a large historical load in a
single pass can leave the odd residual duplicate pair, because pagination
is unstable on recent dates. How to find and clean them is in
[residual duplicates](../explanation/data-caveats.md).
