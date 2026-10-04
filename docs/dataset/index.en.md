---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "In preparation"

    No version has been published yet. This section explains what the dataset will be and how it is being built, and its SQL is experimental: it may change at any time until the first version is published.

A ready-to-use dataset with **the whole history** of the BDNS that `bdns-sync` keeps, not only the years the portal still publishes ([why it matters](../sync/index.md#why-history)). It will always be **anonymised and aggregated**: protecting natural persons comes first, and the whole process must comply with the IGAE's reuse conditions, the GDPR and Spain's LOPDGDD. What is published, at what detail and why is in [decision 0002](../adr/0002-anonymised-dataset.md), still a proposal.

## How natural persons are protected

Each beneficiary is classified by its tax ID, never by its name, and anything not recognised is treated as a natural person. For example (names and tax IDs are made up):

| How it appears in the BDNS | Classified as | In the dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | Natural person | Aggregated only |
| `E12345678 APELLIDO Y APELLIDO CB` | Entity made of persons | Aggregated only |
| `123456789012 FOREIGN COMPANY LTD` | Doubtful | Aggregated only |
| `B12345678 EMPRESA DE EJEMPLO SL` | Legal person | Record by record |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | Public body | Record by record |

Communities of property and civil partnerships have a tax ID of their own, but are usually named after their members, so they are protected like natural persons.

Before writing anything, the build checks what it is about to publish and **stops** if it finds a value shaped like a DNI, NIE or masked tax ID, a column that identifies someone (the beneficiary, their BDNS identifier, the bulletin link...) or a summary gathering fewer than ten people. It does not clean up what it finds: it reports it, because such a finding points to an earlier fault that needs fixing.

<a id="sql"></a>
## The SQL

The whole process is DuckDB SQL, without a line of Python. DuckDB connects to the `bdns-sync` database (SQLite, PostgreSQL, DuckDB or BigQuery), reads its tables and leaves the result in a private file, since it holds personal data until the end. The steps are SQL files in [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), which can be read, reviewed and rerun as they are, and are all run from the repository root with the DuckDB command line:

```console
$ duckdb /private/path/dataset.duckdb \
    -cmd "ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY);
          SET VARIABLE output_dir = '/path/to/output'" \
    -f dataset/build.sql
```

This is the step that classifies beneficiaries, shown straight from the code:

```sql
--8<-- "dataset/sql/01_beneficiarios.sql"
```

## Status

- [x] The design decision, as a proposal ([decision 0002](../adr/0002-anonymised-dataset.md))
- [x] Beneficiary classification and the building blocks of the privacy checks, in SQL
- [x] Awards, read straight from `bdns-sync` with each one's last known version, including those the API has withdrawn, with typed columns and the beneficiary's kind
- [x] Awards, state aid and de minimis aid to legal persons and public bodies, record by record, without the bulletin link or the BDNS internal identifier, and the checks that guard them
- [x] The Parquet export, which only happens if every check passes
- [x] Awards to natural persons, as a summary per call: number of awards and beneficiaries, total amount, mean, standard deviation, median and quartiles of the amount, and the same percentiles of the award date
- [ ] The same for state and de minimis aid
- [ ] The dataset card, the schema and publication
- [ ] The risk assessment and legal review, before the first version
