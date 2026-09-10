# Scheduled operation

`bdns-sync` does not know what day it is. One invocation syncs one
endpoint over the range you give it, and that is all. The cadence lives
outside, in an orchestration script.

The repository ships one ready to use:
[`scripts/delta_load.sh`](https://github.com/cruzlorite/bdns-sync/blob/main/scripts/delta_load.sh).

## One cron line

```crontab
0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/delta_load.sh
```

That is all. The script decides which window applies today.

## Why one window a day

The windows are **nested, not independent**: they all end yesterday, so
on any given day `annual ⊃ monthly ⊃ weekly ⊃ daily`. Running the widest
one that applies today already covers every narrower one for free.

The script's calendar:

| When | Window | Reach |
| --- | --- | --- |
| Every day | `weekly` | 7 days of registration date |
| Mondays | `monthly` | 30 days |
| 1 January, May and September | `annual` | 365 days |

## Why the baseline is weekly, not daily

Two reasons, and both are about correctness rather than convenience:

- A record can surface with a registration date days in the past. A
  one-day window would never see it.
- Deletion detection only looks inside the window it runs with. With a
  one-day window, a withdrawal registered three days ago goes unnoticed
  until the next wide pass.

Seven days of lookback every day catches both.

## Why the script does not stop at the first failure

One failing endpoint must not cancel the other 21. They are independent
syncs sharing nothing but the target, so aborting the whole day over one
of them only widens the outage.

It happened: on 2 September 2026 `sectores` — a 24-row catalog — hit the
BigQuery daily quota and took the other 22 entities down with it. That
day left 1 run instead of 23.

So the script does not use `set -e`. It collects the failures, reports
them at the end, and still exits non-zero so the job is marked failed and
the alert fires. `-u` and `pipefail` stay: they catch bugs in the script
itself.

## Check the API has not changed

Once, before the day's cadence:

```console
$ bdns-sync check-api
```

It only fails when the API returned valid data contradicting an
invariant. Transient blips block nothing. See
[`check-api`](../reference/cli.md#check-api).

## Knowing whether a day went well

A run's state is its latest event in `_sync_runs`. The operating rule is
the same on every engine: **no `success` event, run it again.** The tool
is idempotent.

```python
import sqlite3

db = sqlite3.connect("bdns.db")
for row in db.execute(
    "SELECT table_name, run_type, event, occurred_at"
    " FROM _sync_runs WHERE event != 'started'"
    " ORDER BY occurred_at DESC LIMIT 25"
):
    print(row)
```

The per-engine guarantees are detailed in
[the data model](../reference/data-model.md).
