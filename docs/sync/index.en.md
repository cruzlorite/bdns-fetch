# BDNS Sync

Sync engine that keeps target databases in **SCD2** form from the
[Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/)
API — Spain's national subsidies database.

One command a day keeps the target up to date: it checks that the API has
not changed, syncs the 22 entities with the window that day calls for,
and records every run. No configuration file.

```console
$ pip install bdns
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
$ bdns-sync backfill        # once: the history
$ bdns-sync delta           # daily
```

It builds on [`bdns-fetch`](../fetch/index.md),
which knows everything there is to know about the API; `bdns-sync` adds
versioned history, deletion detection and the run log.

## Where to start

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Never used it**

    ---

    From nothing to a synced, queryable table in about ten minutes,
    without leaving your machine.

    [:octicons-arrow-right-24: Get started](getting-started.md)

- :material-calendar-clock:{ .lg .middle } **Run it for real**

    ---

    Daily cadence, initial loads, and cloud deployment.

    [:octicons-arrow-right-24: How-to guides](guides/scheduling.md)

- :material-lightbulb-on:{ .lg .middle } **Understand why**

    ---

    What counts as a change, how the source API behaves, and what to know
    before querying the tables.

    [:octicons-arrow-right-24: Explanation](explanation/payload-policy.md)

- :material-code-braces:{ .lg .middle } **Look something up**

    ---

    The CLI, the table schema, and the Python API generated from the
    docstrings.

    [:octicons-arrow-right-24: Reference](reference/cli.md)

</div>

## The data model in one sentence

Every endpoint gets one table with a fixed schema: the record is stored
whole in `payload`, and every other column is versioning metadata. Closed
versions are never deleted — history is append-only.

| Column | What it is |
| --- | --- |
| `_natural_key` | The record's identity, serialized from its key fields |
| `_row_hash` | Content hash; a different hash is a new version |
| `_valid_from` / `_valid_to` | This version's validity. Null `_valid_to` means current |
| `_is_current` | Whether this is the live version |
| `_synced_at` | Last time the record was seen |
| `_reg_date` | The record's own registration date, where the entity exposes one |
| `payload` | The record exactly as the API returned it |
| `_created_run_id` / `_closed_run_id` | The run that wrote the version and the one that closed it |
| `_closed_reason` | Why it was closed: `superseded` or `removed` |

For example, an award is registered on 10 January with €1,000, on 5 March its amount is corrected to €1,200, and on 20 June the API stops serving it. This is what the table holds:

| `_valid_from` | `_valid_to` | `_is_current` | `_closed_reason` | Amount in `payload` |
|---|---|---|---|---|
| 2026-01-10 | 2026-03-05 | no | `superseded` | €1,000 |
| 2026-03-05 | 2026-06-20 | no | `removed` | €1,200 |

Had the award been seen again unchanged in between, there would be no extra row: only `_synced_at` moves.

## Notice

A personal, unofficial project with no relationship to the Intervención General de la Administración del Estado (IGAE), which runs the BDNS. Several tables hold names and tax IDs of natural persons, and their reuse is limited by the IGAE's conditions, summarised in the [legal notice](../legal.md).
