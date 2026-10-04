---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "In preparation"

    No version has been published yet. This section explains what the dataset will be and how it is being built, and its SQL is experimental: it may change at any time until the first version is published.

A ready-to-use dataset with **the whole history** of the BDNS that `bdns-sync` keeps, not only the years the portal still publishes ([why it matters](../sync/index.md#why-history)). It will always be **anonymised and aggregated**: protecting natural persons comes first, and the whole process must comply with the IGAE's reuse conditions, the GDPR and Spain's LOPDGDD.

It is a set of Parquet files, one per table, that DuckDB, pandas, R or any other data tool can open:

| Table | What it holds | Detail |
|---|---|---|
| `concesiones_entidades` | Awards to legal persons and public bodies | One row per award |
| `ayudas_estado_entidades` | State aid to legal persons and public bodies | One row per aid |
| `minimis_entidades` | De minimis aid to legal persons and public bodies | One row per aid |
| `concesiones_personas` | Awards to natural persons | One summary per call |

The table and column names are in Spanish, like the BDNS data itself. For example, to see which bodies awarded the most to companies and organisations, query the file directly (the data is made up):

```console
$ duckdb -c "
    SELECT nivel3 AS organo, count(*) AS concesiones, sum(importe) AS importe
    FROM 'concesiones_entidades.parquet'
    GROUP BY organo
    ORDER BY importe DESC
    LIMIT 3"
┌─────────────────────────────┬─────────────┬───────────────┐
│           organo            │ concesiones │    importe    │
│           varchar           │    int64    │ decimal(38,2) │
├─────────────────────────────┼─────────────┼───────────────┤
│ CONSEJERÍA DE AGRICULTURA   │           3 │     145000.00 │
│ CONSEJERÍA DE EDUCACIÓN     │           1 │      90000.00 │
│ SERVICIO REGIONAL DE EMPLEO │           3 │      28000.00 │
└─────────────────────────────┴─────────────┴───────────────┘
```

## Where to start

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **First time here**

    ---

    Build the dataset from your `bdns-sync` copy and run your first query.

    [:octicons-arrow-right-24: Get started](getting-started.md)

- :material-magnify:{ .lg .middle } **I want to analyse the data**

    ---

    Example queries with DuckDB and pandas, and how to read the natural-person summaries.

    [:octicons-arrow-right-24: How-to guides](guides/queries.md)

- :material-shield-account:{ .lg .middle } **I want to know how people are protected**

    ---

    Which beneficiaries are protected, what is published about them and what is checked before anything is written.

    [:octicons-arrow-right-24: Explanation](explanation/anonymisation.md)

- :material-code-braces:{ .lg .middle } **I am looking for a detail**

    ---

    Every table and its columns, and the build steps.

    [:octicons-arrow-right-24: Reference](reference/tables.md)

</div>

## Status

- [x] The design decision, as a proposal ([decision 0002](../adr/0002-anonymised-dataset.md))
- [x] Beneficiary classification and the building blocks of the privacy checks, in SQL
- [x] Awards, read straight from `bdns-sync` with each one's last known version, including those the API has already withdrawn, with their columns and the beneficiary's kind
- [x] Awards, state aid and de minimis aid to legal persons and public bodies, record by record, without the bulletin link or the BDNS internal identifier, and the checks that guard them
- [x] The Parquet export, which runs only if every check passes
- [x] Awards to natural persons, as one summary per call: number of awards and beneficiaries, total amount, mean, standard deviation, median and quartiles of the amount, and the same percentiles of the award date
- [ ] The same for state aid and de minimis aid
- [ ] The dataset card, the schema and the publication
- [ ] The risk assessment and the legal review, before the first version
