# BDNS Fetch

Python client and CLI for the API of Spain's [National Subsidies
Database](https://www.infosubvenciones.es/) (BDNS). All 29 query
endpoints, with pagination, retries and the API's rate limit applied by
default.

```console
$ pip install bdns
$ bdns-fetch convocatorias-busqueda --fechaDesde 2024-01-01 --num-pages 0 > convocatorias.jsonl
```

```python
from bdns.fetch import BDNSClient

client = BDNSClient()
for convocatoria in client.fetch_convocatorias_busqueda(descripcion="investigación"):
    print(convocatoria["numeroConvocatoria"], convocatoria["descripcion"])
```

## Where to start

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Never used it**

    ---

    A first query from the terminal and from Python, in five minutes.

    [:octicons-arrow-right-24: Get started](getting-started.md)

- :material-calendar-sync:{ .lg .middle } **Download incrementally**

    ---

    Date ranges without losing or duplicating days, errors, and endpoints with no method of their own.

    [:octicons-arrow-right-24: How-to guides](guides/incremental.md)

- :material-lightbulb-on:{ .lg .middle } **Understand the API**

    ---

    How the API actually behaves, measured against the live service, and why the client does what it does.

    [:octicons-arrow-right-24: Explanation](explanation/api-behavior.md)

- :material-code-braces:{ .lg .middle } **Look something up**

    ---

    The CLI and the Python API, generated from the docstrings.

    [:octicons-arrow-right-24: Reference](reference/cli.md)

</div>

## The family

`bdns-fetch` is the **extraction** layer: it knows everything there is to know about the API and nothing about storage. [`bdns-sync`](../sync/index.md) builds on it to keep a local, versioned (SCD2) copy of the same data in any database with a SQLAlchemy dialect.

## Notice

A personal, unofficial project with no relationship to the Intervención General de la Administración del Estado (IGAE), which runs the BDNS. Some endpoints return names and tax IDs of natural persons, and their reuse is limited by the IGAE's conditions, summarised in the [legal notice](../legal.md).
