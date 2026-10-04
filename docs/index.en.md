# BDNS

Tools to download, keep and reuse the data of Spain's [National Subsidies Database](https://www.infosubvenciones.es/) (BDNS) through its public API.

```console
$ pip install bdns                # for BigQuery: pip install "bdns[bigquery]"
```

The package brings two tools, each with its own command and Python module:

<div class="grid cards" markdown>

- :material-cloud-download:{ .lg .middle } **BDNS Fetch**

    ---

    Python client and command-line tool for the API. It covers the 29 query endpoints and handles pagination, retries and the rate limit. Use it to query the API or download data to files.

    [:octicons-arrow-right-24: Go to bdns-fetch](fetch/index.md)

- :material-database-sync:{ .lg .middle } **BDNS Sync**

    ---

    Keeps a copy of the BDNS, with the history of every version, in your database (SQLite, PostgreSQL, DuckDB or BigQuery), with one command a day. It uses `bdns-fetch` underneath.

    [:octicons-arrow-right-24: Go to bdns-sync](sync/index.md)

</div>

An anonymised, aggregated dataset with the whole history, ready to use, will follow ([roadmap](roadmap.md#dataset)).

## Notice

This is a personal, unofficial project, not affiliated with the Intervención General de la Administración del Estado (IGAE), which runs the BDNS. If you reuse the data, you must meet its reuse conditions, summarised in the [README's legal notice](https://github.com/cruzlorite/bdns/blob/main/README.en.md#legal-notice).
