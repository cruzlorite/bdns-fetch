# BDNS Sync

Sync engine that keeps target databases in **SCD2** form from the
[Base de Datos Nacional de Subvenciones](https://www.infosubvenciones.es/)
API — Spain's national subsidies database.

One invocation syncs one endpoint. No configuration file, no knowledge of
cadence: what to sync and when belongs to whoever orchestrates it.

```console
$ pip install bdns-sync
$ export BDNS_SYNC_TARGET_URL=sqlite:///bdns.db
$ bdns-sync sync concesiones_busqueda --window daily
```

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
