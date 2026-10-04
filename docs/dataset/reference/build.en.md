# Build

The whole process is DuckDB SQL, without a line of Python. The steps are files in [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), which can be read, reviewed and rerun as they are, and `dataset/build.sql` runs them in order with the DuckDB command line, from the repository root:

```console
$ duckdb /private/path/dataset.duckdb \
    -cmd "ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '/path/to/output'" \
    -f dataset/build.sql
```

The DuckDB file (`dataset.duckdb` in the example) must be somewhere private, because it keeps intermediate tables with personal data. The run stops at the first error, so if a check fails no file is written. Each step's results are not printed, and you only see something if there is an error.

<a id="attach"></a>
## Attaching the `bdns-sync` database

The SQL reads `bdns-sync`'s tables under the name `sync`, so all it takes is attaching your database under that name, read-only. DuckDB downloads the extension it needs the first time.

| Database | `ATTACH` | Tested |
|---|---|---|
| SQLite | `ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Yes |
| DuckDB | `ATTACH '/path/to/bdns.duckdb' AS sync (READ_ONLY)` | Yes |
| PostgreSQL | `ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY)` | Not yet |
| BigQuery | With the [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) community extension | Not yet |

## Variables

| Variable | What it is |
|---|---|
| `output_dir` | Folder the Parquet files are written to. It must exist. If you do not set it, the export stops with the message `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build` |

<a id="steps"></a>
## The steps

Intermediate tables stay in the private file, and only those in the `publish` schema are written as Parquet files.

| File | What it does |
|---|---|
| `01_beneficiarios.sql` | Defines how each beneficiary is classified by its tax ID ([the SQL](#sql)) |
| `02_privacy.sql` | Defines the building blocks of the privacy checks and the [thresholds](#thresholds) |
| `03_publish.sql` | Creates the `publish` schema, where everything to be published goes |
| `10_concesiones.sql` | Reads awards from `bdns-sync`, each one's last version, with typed columns. Private |
| `11_ayudas_estado.sql` | The same for state aid. Private |
| `12_minimis.sql` | The same for de minimis aid. Private |
| `20_entidades.sql` | Writes the three entity tables to `publish`, record by record |
| `30_personas.sql` | Writes the per-call summary of natural persons to `publish` |
| `90_checks.sql` | Checks what is about to be published and stops the run if it finds anything ([the checks](#checks)) |
| `95_export.sql` | Writes each table in `publish` as a Parquet file in `output_dir` |

<a id="thresholds"></a>
## Thresholds

They are defined once, as macros in `02_privacy.sql`, and both the summary and the checks use them. What each one protects is explained in [the rules](../explanation/anonymisation.md#rules).

| Macro | Value | What it controls |
|---|---|---|
| `min_beneficiaries()` | 10 | People each summary row must gather at least |
| `max_dominant_share()` | 0.5 | Share of a row's amount a single person may hold at most |
| `min_beneficiaries_for_tails()` | 20 | People from which the 10th and 90th percentiles are published |

<a id="checks"></a>
## Checks and messages

If a check finds something, the run exits with code 1 and one of these messages, preceded by `Invalid Input Error:` and the table's name:

| Message | What it found |
|---|---|
| `N rows of protected beneficiaries` | Rows of natural persons or other protected beneficiaries in an entity table |
| `N rows with something shaped like a personal tax ID` | A value shaped like a DNI, NIE or masked tax ID, in any column |
| `identifying columns: ...` | A column that identifies someone in the natural-person summary |
| `N rows below 10 beneficiaries` | Summary rows gathering fewer than 10 people |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Summary rows with the 10th or 90th percentiles and fewer than 20 people |

Any of them points to a fault in an earlier step. If it happens to you, open an [issue](https://github.com/cruzlorite/bdns-tools/issues) with the message, without copying any data from the rows that caused it.

<a id="sql"></a>
## The SQL

This is the step that classifies beneficiaries, shown straight from the code:

```sql
--8<-- "dataset/sql/01_beneficiarios.sql"
```
