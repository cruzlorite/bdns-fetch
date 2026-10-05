# How the dataset is built

Until a version is published, the only way to have the dataset is to build it yourself from a `bdns-sync` copy. The whole process is DuckDB SQL: the steps are files in [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), which can be read, reviewed and rerun as they are, and `dataset/build.sql` runs them in order.

## What you need

- A `bdns-sync` database with, at least, the awards. If you do not have one yet, follow its [get started](../sync/getting-started.md) first.
- The [DuckDB command line](https://duckdb.org/docs/installation/). It is tested with version 1.5.
- A copy of the repository, since the SQL runs from its root:

```console
$ git clone https://github.com/cruzlorite/bdns-tools.git
$ cd bdns-tools
```

## Building it

DuckDB attaches your database read-only and works in a file of its own, which must be somewhere private, because it keeps intermediate tables with personal data. The Parquet files are written to the folder you set in `output_dir`, which must exist. With the SQLite copy from `bdns-sync`'s get started:

```console
$ mkdir -p ~/bdns-dataset/salida
$ duckdb ~/bdns-dataset/privado.duckdb \
    -cmd "ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
$ ls ~/bdns-dataset/salida
ayudas_estado_entidades.parquet  concesiones_entidades.parquet  concesiones_personas.parquet  minimis_entidades.parquet
```

If all goes well, the command prints nothing. If you forget `output_dir`, it stops with the message `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build`.

<a id="attach"></a>
### With another database

The SQL reads `bdns-sync`'s tables under the name `sync`, so only the `ATTACH` changes. DuckDB downloads the extension it needs the first time.

| Database | `ATTACH` | Tested |
|---|---|---|
| SQLite | `ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Yes |
| DuckDB | `ATTACH '/path/to/bdns.duckdb' AS sync (READ_ONLY)` | Yes |
| PostgreSQL | `ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY)` | Not yet |
| BigQuery | With the [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) community extension | Not yet |

<a id="checks"></a>
## When a check stops the build

Before writing the files, the build checks what it is about to publish, and if it finds anything that could identify a natural person it stops without writing anything. For example, if the title of a call awarded to a company held a DNI:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_entidades: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

The command exits with code 1 and the folder stays as it was. These are all the possible messages, always preceded by the table's name:

| Message | What it found |
|---|---|
| `N rows of protected beneficiaries` | Rows of natural persons or other protected beneficiaries in an entity table |
| `N rows with something shaped like a personal tax ID` | A value shaped like a DNI, NIE or masked tax ID, in any column |
| `identifying columns: ...` | A column that identifies someone in the natural-person summary |
| `N rows below 10 beneficiaries` | Summary rows gathering fewer than 10 people |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Summary rows with the 10th or 90th percentiles and fewer than 20 people |

Any of them points to a fault in the dataset's SQL, so if it happens to you, open an [issue](https://github.com/cruzlorite/bdns-tools/issues) with the message, without copying any data from the rows that caused it.

<a id="steps"></a>
## The steps

Intermediate tables stay in the private file, and only those in the `publish` schema are written as Parquet files.

| File | What it does |
|---|---|
| `01_beneficiarios.sql` | Defines how each beneficiary is classified by its tax ID |
| `02_privacy.sql` | Defines the building blocks of the privacy checks and the [thresholds](#thresholds) |
| `03_publish.sql` | Creates the `publish` schema, where everything to be published goes |
| `04_versions.sql` | Defines how each record's last version is chosen, without loading every `payload` at once |
| `10_concesiones.sql` | Reads awards from `bdns-sync`, each one's last version, with typed columns. Private |
| `11_ayudas_estado.sql` | The same for state aid. Private |
| `12_minimis.sql` | The same for de minimis aid. Private |
| `20_entidades.sql` | Writes the three entity tables to `publish`, record by record |
| `30_personas.sql` | Writes the per-call summary of natural persons to `publish` |
| `90_checks.sql` | Checks what is about to be published and stops the run if it finds anything |
| `95_export.sql` | Writes each table in `publish` as a Parquet file in `output_dir` |

<a id="thresholds"></a>
## Thresholds

They are defined once, as macros in `02_privacy.sql`, and both the summary and the checks use them. What each one protects is explained in [the rules](privacy.md#rules).

| Macro | Value | What it controls |
|---|---|---|
| `min_beneficiaries()` | 10 | People each summary row must gather at least |
| `max_dominant_share()` | 0.5 | Share of a row's amount a single person may hold at most |
| `min_beneficiaries_for_tails()` | 20 | People from which the 10th and 90th percentiles are published |
