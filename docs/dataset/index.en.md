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

Companies and public bodies appear record by record, with their tax ID and name, while for natural persons only per-call summaries are published, which identify no one.

<div class="grid cards" markdown>

- :material-table:{ .lg .middle } **What it contains**

    ---

    The tables, their columns and what is worth knowing to read them right.

    [:octicons-arrow-right-24: Contents](contents.md)

- :material-shield-account:{ .lg .middle } **How people are protected**

    ---

    Which beneficiaries are protected, what is published about them and what is checked before publishing.

    [:octicons-arrow-right-24: Anonymisation](privacy.md)

- :material-cog:{ .lg .middle } **How it is built**

    ---

    How to build the dataset from your `bdns-sync` copy, with the DuckDB command line.

    [:octicons-arrow-right-24: Build](build.md)

</div>

## Status

- [x] The design decision, as a proposal ([decision 0020](../adr/0020-anonymised-dataset.md))
- [x] Beneficiary classification and the building blocks of the privacy checks, in SQL
- [x] Awards, read straight from `bdns-sync` with each one's last known version, including those the API has already withdrawn, with their columns and the beneficiary's kind
- [x] Awards, state aid and de minimis aid to legal persons and public bodies, record by record, without the bulletin link or the BDNS internal identifier, and the checks that guard them
- [x] The Parquet export, which runs only if every check passes
- [x] Awards to natural persons, as one summary per call: number of awards and beneficiaries, total amount, mean, standard deviation, median and quartiles of the amount, and the same percentiles of the award date
- [ ] The same for state aid and de minimis aid
- [ ] The dataset card, the schema and the publication
- [ ] The risk assessment and the legal review, before the first version
