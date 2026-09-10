# Get started

From nothing to a synced, queryable table. About ten minutes, with no
cloud account and no database to install: it uses SQLite, which is a
file.

## 1. Install

```console
$ pip install bdns-sync
$ bdns-sync --version
bdns-sync 0.5.0
```

## 2. Pick a target

The target is given as a SQLAlchemy URL. Here, a local file:

```console
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
```

Every command reads that variable, so you do not repeat it. `--target-url`
works too.

## 3. Sync something small

`sectores` is a catalog: a couple of dozen rows, one call. A good first
step because it finishes in seconds.

```console
$ bdns-sync sync sectores
```

There is data now. Python is enough to look at it, and you already have
it:

```console
$ python -c "import sqlite3; print(sqlite3.connect('bdns.db').execute('SELECT COUNT(*) FROM sectores').fetchone()[0])"
24
```

## 4. Look at how it was stored

The table has no column per field. The record is stored whole in
`payload`, and everything else is versioning metadata:

```python
import sqlite3

db = sqlite3.connect("bdns.db")
for key, current, payload in db.execute(
    "SELECT _natural_key, _is_current, payload FROM sectores LIMIT 2"
):
    print(key, current, payload)
```

```text
[10] 1 {"descripcion": "Productos transformados a base de frutas y hortalizas (parte X)", "id": 10}
[11] 1 {"descripcion": "Plátanos (parte XI)", "id": 11}
```

Why it works this way, and what it buys you, is in
[the data model](reference/data-model.md).

## 5. Sync again

Run exactly the same command again:

```console
$ bdns-sync sync sectores
```

Compare the counters in the log. The first time:

```text
fetched=24 inserted=24 updated=0 touched=0 soft_deleted=0 skipped=0
```

The second:

```text
fetched=24 inserted=0 updated=0 touched=24 soft_deleted=0 skipped=0
```

Everything landed in `touched`: the records were seen again and had not
changed, so **no new version was created**. Only the last-seen timestamp
moved.

That is the central idea of the tool. What counts as a change, and what
does not, is explained in
[what is stored, and what counts as a change](explanation/payload-policy.md).

## 6. An incremental endpoint

The big endpoints are not synced whole: they are requested by
registration-date range. Before running one, see what it would do:

```console
$ bdns-sync sync concesiones_busqueda --window daily --dry-run
target      sqlite:///bdns.db  ->  table concesiones_busqueda
run type    daily
range       2026-09-06 .. 2026-09-06  (1 day(s), 1 chunk(s) of at most 7)
policy      drop=[] hash_exclude=['beneficiario'] delimited_lists=[] canonical_arrays=True
limits      max_ratio=10% max_count=none min_to_enforce_ratio=5
dry run     nothing fetched, nothing written
```

`--dry-run` resolves the range, the policy and the limits, prints them,
and stops. It touches neither the API nor the target. Drop it to run for
real:

```console
$ bdns-sync sync concesiones_busqueda --window daily
```

`daily` asks for yesterday. Not today, because today is still receiving
registrations and would leave a partial day behind that nothing revisits.

## 7. Read the run log

Every run is recorded in the target, next to the data:

```python
for row in db.execute(
    "SELECT run_id, table_name, run_type, event, rows_fetched"
    " FROM _sync_runs ORDER BY occurred_at DESC LIMIT 4"
):
    print(row)
```

```text
(1788734182609786, 'sectores', 'full', 'success', 24)
(1788734182609786, 'sectores', 'full', 'started', None)
(1788734171434519, 'sectores', 'full', 'success', 24)
(1788734171434519, 'sectores', 'full', 'started', None)
```

Two rows per run: a `started` and a `success`. If you ever see a lone
`started`, that process died halfway through — exactly the information a
mutable status column could never give you.

## What next

- Run it every day: [scheduled operation](guides/scheduling.md).
- Load the full history: [initial loads and backfills](guides/backfill.md).
- Take it to the cloud: [deployment](guides/deployment.md).
- Before querying in earnest: [before querying the data](explanation/data-caveats.md).
