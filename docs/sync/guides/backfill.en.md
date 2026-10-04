# Initial loads and backfills

The daily cadence reaches at most 365 days of registration date. Bringing
the full history into a new target takes an initial load:

```console
$ BDNS_SYNC_TARGET_URL=bigquery://project/dataset bdns-sync backfill
```

It syncs the full entities first, then loads each windowed entity **year
by year**, from the start of its history up to yesterday. To see the plan
without running anything:

```console
$ bdns-sync backfill --dry-run
target      bigquery://project/dataset
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
  sectores: complete state
  ...
  concesiones_busqueda: backfill [2020-01-01 .. 2020-12-31]
  concesiones_busqueda: backfill [2021-01-01 .. 2021-12-31]
  ...
```

!!! warning "It is a bootstrap for a **new** target"

    Run against a populated one, it closes at once the stored rows the API
    no longer serves: after a few years, everything past its publication
    period (4 calendar years after the award for `concesiones`, 10 for
    `ayudasestado` and `minimis`).

    Those rows are closed with reason `removed`, the date and the `run_id`
    of the backfill, not the date they expired. Nothing breaks, and the
    normal cadence never does this because its widest window reaches 365
    days; but the mass closing is easily mistaken for a real event. See
    [expiry versus real withdrawals](../explanation/data-caveats.md).

## Why year by year

Each year is a run of its own, with its own committed SCD2 diff, so a
crash loses at most the year in flight, never a backfill of several
hours. One entity failing does not stop the others; at the end the failed
ones are reported and the exit code is 1.

There is no resuming within a run. Recovery is running it again, and
repeating is safe: SCD2 is idempotent, an already-synced record is only
marked as seen, never duplicated.

## One entity, or a given range

```console
$ bdns-sync backfill --entity convocatorias --entity convocatorias_busqueda
$ bdns-sync sync concesiones_busqueda --since 2020-01-01 --until 2020-12-31
```

`--entity` limits the backfill to those entities. `sync --since` loads a
range by hand; `--until` defaults to yesterday. Both runs are recorded as
`backfill` in `_sync_runs`, with the range they covered.

## How far back the history goes

Each windowed entity declares in the
[entity registry][bdns.sync.entities] the date to load it from. They are
**conservative floors, not first records**: the API retains a bounded
history, and asking for earlier dates only returns empty weeks, one cheap
call each. See
[how far back the history goes](../explanation/sync-behavior.md#history-depth).

## What to expect

Durations measured on a real full initial load (July 2026, BigQuery
target, a single machine). The bottleneck is always the source API, never
the target:

| Load | Rows | Duration |
|---|---|---|
| The full entities | ~150,000 | ~10 s most; `planesestrategicos` and `planesestrategicos_vigencia`, ~4 min each (detail per key); `grandesbeneficiarios_busqueda`, ~2 min |
| `concesiones_busqueda` (since 2020) | 27.7 M | ~2.5 h |
| `ayudasestado_busqueda` (since 2015) | 6.4 M | ~2 h |
| `minimis_busqueda` (since 2015) | 4.3 M | ~30 min |
| `convocatorias_busqueda` (since 2013) | 636 K | ~6 min |
| `partidospoliticos_busqueda` (since 2020) | 6 K | ~2 min |
| `convocatorias` (since 2013) | 636 K | **between a day and a half and two weeks** one call at a time (estimated from the time per call); ~19 h, measured, with 8 concurrent calls |

Nearly all the time goes to `convocatorias`, since each code needs its own detail call, and that time depends on the API, not on the target database. The official good practices ask for no concurrent calls, so by default they are made one at a time; if you need to finish sooner you can raise `--max-workers`, knowing it departs from that recommendation. Occasional API outages (timeouts, nightly maintenance) are absorbed by the client's retries ([performance](../explanation/sync-behavior.md#performance)).

When it finishes, keep in mind that a massive one-pass historical load
may leave a residual duplicate pair, due to unstable pagination on recent
dates. How to find and clean them: [residual duplicates](../explanation/data-caveats.md).
