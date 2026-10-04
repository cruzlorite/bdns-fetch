# Scheduled operation

A production setup runs **one command a day**:

```console
$ bdns-sync delta
```

`delta` checks that the API has not changed, syncs the 16 full entities
and then the 6 windowed ones, with the window that day calls for. If one
entity fails, it carries on with the rest and exits with code 1 so the
alert fires.

Before scheduling it, run the historical load once: see
[initial loads and backfills](backfill.md). To see what it would do today
without touching anything: `bdns-sync delta --dry-run`.

## One cron line

```crontab
0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://project/dataset bdns-sync delta
```

If you would rather not keep a machine of your own, the container image
runs `bdns-sync delta` by default and there is a recipe for a scheduled
cloud job: see [deployment](deployment.md).

## Which window runs each day

Windows are **nested, not independent**: they all end yesterday, so on
any day `annual ⊃ monthly ⊃ weekly ⊃ daily`. Running the widest one that
applies already covers every narrower one, so `delta` runs exactly one
([`cadence_window`][bdns.sync.windows.cadence_window]):

| When | Window | Reach |
| --- | --- | --- |
| Daily | `weekly` | 7 days of registration date |
| Mondays | `monthly` | 30 days |
| 1 January, May and September | `annual` | 365 days |

`--window` forces another, for instance to recover a given month after an
outage.

## Why the baseline is weekly, not daily

Two reasons, both about correctness, not convenience:

- A record can appear with a registration date some days back. A one-day
  window would never see it.
- Deletion detection only looks inside the window it runs with. With a
  one-day window, a deletion registered three days ago is not detected
  until the next wide pass.

Looking back seven days every day catches both.

## Why it does not stop at the first failure

One entity failing must not cancel the other 21. They are independent
syncs sharing nothing but the target, so aborting the whole day over one
of them only widens the outage. It really happened: on 2 September 2026
`sectores`, a 24-row catalog, exhausted the BigQuery daily quota and,
with an orchestrator that stopped at the first failure, took the other 22
entities down with it.

`delta` records each failure in `_sync_runs`, carries on with the rest
and reports at the end:

```console
ok      sectores                         fetched=24 new=0 changed=0 unchanged=24 removed=0 skipped=0
FAILED  concesiones_busqueda             BDNSTransientError: HTTP 503: Server error
...
1 of 22 sync(s) failed
```

## The API check is built in

Before syncing, `delta` runs `bdns-fetch`'s contract check: that
`fechaRegFin` is still exclusive, `fechaHasta` inclusive, and consecutive
days disjoint. If the API returns valid data contradicting any of that,
**nothing is synced** and it exits with code 1. A passing error or an
empty day does not block ([why](../explanation/sync-behavior.md#boundary-check)).
`--skip-api-check` skips it.

## Knowing whether a day went well

A run's state is its last event in `_sync_runs`. The operating rule is
the same on every engine: **no `success` event means re-run.** The tool
is idempotent.

```sql
SELECT table_name, run_type, event, occurred_at, window_start, window_end,
       rows_inserted, rows_changed, rows_soft_deleted, rows_skipped, error
FROM _sync_runs
WHERE event != 'started'
ORDER BY occurred_at DESC
LIMIT 25;
```

Watch `rows_skipped` too: a run can succeed while skipping malformed
records, which are kept in `_sync_errors`. The per-engine guarantees are
in [the data model](../reference/data-model.md).
