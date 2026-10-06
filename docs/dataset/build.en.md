# How the dataset is built

Until a version is published, the only way to have the dataset is to build it yourself from a `bdns-sync` copy. The whole process is DuckDB SQL: the steps are files in [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), which can be read, reviewed and rerun as they are, and `dataset/build.sql` runs them in order.

## What you need

- A `bdns-sync` database with every entity, like the one `bdns-sync delta` keeps. If you do not have one yet, follow its [get started](../sync/getting-started.md) first.
- The [DuckDB command line](https://duckdb.org/docs/installation/). It is tested with version 1.5.
- A copy of the repository, since the SQL runs from its root:

```console
$ git clone https://github.com/cruzlorite/bdns-tools.git
$ cd bdns-tools
```

## Building it

DuckDB attaches your database read-only and works in memory, without a file of its own. Whatever does not fit goes to its temp folder, personal data included, so you must give it one somewhere private (`temp_directory`); otherwise the build does not start. DuckDB empties it at the end, and only a run cut short would leave remains for you to delete. The Parquet files are written to the folder you set in `output_dir`, which must exist. With the SQLite copy from `bdns-sync`'s get started:

```console
$ mkdir -p ~/bdns-dataset/salida ~/bdns-dataset/tmp
$ duckdb -cmd "SET temp_directory = '$HOME/bdns-dataset/tmp';
               ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
               SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
$ ls ~/bdns-dataset/salida
ayudasestado_personas_fisicas.parquet    grandesbeneficiarios.parquet
ayudasestado_personas_juridicas.parquet  minimis_personas_fisicas.parquet
catalogos.parquet                        minimis_personas_juridicas.parquet
concesiones_personas_fisicas.parquet     partidospoliticos.parquet
concesiones_personas_juridicas.parquet   planesestrategicos.parquet
convocatorias.parquet
```

While it works, it prints the time each step starts and, at the end, `done`, so you can follow a long build and see how long each step takes. These are the real timings for a copy with 30 million awards since 2022, read from BigQuery with a working file ([in memory](#memory) it takes about a third longer):

```text
19:16:13  01_beneficiarios.sql
19:16:13  02_privacy.sql
19:16:13  03_publish.sql
19:16:13  04_versions.sql
19:16:13  05_schemas.sql
19:16:13  06_summaries.sql
19:16:13  10_concesiones.sql
19:23:23  11_ayudasestado.sql
19:24:31  12_minimis.sql
19:25:14  13_partidospoliticos.sql
19:25:17  14_grandesbeneficiarios.sql
19:25:21  15_convocatorias.sql
19:26:03  16_planesestrategicos.sql
19:26:05  17_catalogos.sql
19:26:27  80_schema_drift.sql
19:26:27  90_checks.sql
19:26:37  95_export.sql
19:26:47  done
```

If you forget `output_dir`, it stops with the message `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build`.

<a id="attach"></a>
### With another database

The SQL reads `bdns-sync`'s tables under the name `sync`, so only the `ATTACH` changes. DuckDB downloads the extension it needs the first time.

| Database | `ATTACH` | Tested |
|---|---|---|
| SQLite | `ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Yes |
| DuckDB | `ATTACH '/path/to/bdns.duckdb' AS sync (READ_ONLY)` | Yes |
| PostgreSQL | `ATTACH 'postgresql://user@host/bdns' AS sync (TYPE postgres, READ_ONLY)` | Yes |
| BigQuery | With the [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) community extension ([how](#bigquery)) | Yes |

<a id="bigquery"></a>
### From BigQuery

The [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) extension attaches your project and, given the dataset in the `ATTACH`, finds the tables under the names the SQL expects. Data arrives compressed, and only the columns in use: with 30 million awards that is about 4.5 GB over the network, and the read costs cents. You need the credentials from `gcloud auth application-default login`:

```console
$ duckdb -cmd "
    SET temp_directory = '$HOME/bdns-dataset/tmp';
    SET memory_limit = '3GB';
    SET threads = 4;
    SET preserve_insertion_order = false;
    INSTALL bigquery FROM community; LOAD bigquery;
    ATTACH 'project=YOUR_PROJECT dataset=YOUR_DATASET' AS sync (TYPE bigquery, READ_ONLY);
    SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
```

<a id="memory"></a>
### With a long history

By default DuckDB uses up to 80% of the machine's memory, and with other programs open at the same time the system may stop it for lack of memory. To avoid that, give it a limit at the start of `-cmd`, as in the BigQuery example; whatever does not fit goes to its temp folder. Bear in mind two things. First, the process takes quite a lot more than that limit, because the BigQuery extension uses memory of its own. Second, what goes to disk is not compressed, so with a long history the temp folder grows a lot: with 30 million awards it reached about 35 GB, and the process about 7 GB of memory. If you are short of disk, you can give `duckdb` a working file as its first argument (for example, `~/bdns-dataset/privado.duckdb`): it keeps the same, compressed, in about 3 GB, and is somewhat faster, but you have to delete it yourself afterwards.

<a id="checks"></a>
## When a check stops the build

Before writing the files, the build checks what it is about to publish, and if it finds anything that could identify a natural person it stops without writing anything. For example, if the title of a call awarded to a company held a DNI:

```console
$ duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_personas_juridicas: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

The command exits with code 1 and the folder stays as it was. The checks are not written table by table: they look at every table in `publish` and tell each one's kind by its columns, so a new table is checked without touching anything. These are all the possible messages, always preceded by the table's name:

| Message | What it found |
|---|---|
| `N rows of protected beneficiaries` | Rows of natural persons or other protected beneficiaries in an entity table |
| `N rows with something shaped like a personal tax ID` | A value shaped like a DNI, NIE or masked tax ID, in any column |
| `identifying columns: ...` | A column that identifies someone in the natural-person summary |
| `N rows below 10 beneficiaries` | Summary rows gathering fewer than 10 people |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Summary rows with the 10th or 90th percentiles and fewer than 20 people |

Any of them points to a fault in the dataset's SQL, so if it happens to you, open an [issue](https://github.com/cruzlorite/bdns-tools/issues) with the message, without copying any data from the rows that caused it.

At the end, the export also stops if a table in `publish` was left without its file (`Published but not exported`), since each table needs its line in `95_export.sql`.

<a id="drift"></a>
## When the API stops sending a field

The fields the dataset reads are listed in `05_schemas.sql`. If the API renames or drops one, or changes its format, that field would arrive empty without anyone noticing, so the build warns when one came empty in every record `bdns-sync` stored in its table's last 30 days:

```text
warning: planesestrategicos.tipoPlan is empty in every record stored in its last 30 days
```

It is a warning, not an error, since a rare field can stay empty for a month. If it repeats, compare a recent API record with `05_schemas.sql`. New fields the API adds give no warning: they are ignored until someone declares them, so nothing is ever published by surprise.

<a id="steps"></a>
## The steps

Intermediate tables stay in the main database, which is private, and only those in the separate `publish` database are written as Parquet files.

| File | What it does |
|---|---|
| `01_beneficiarios.sql` | Defines how each beneficiary is classified by its tax ID |
| `02_privacy.sql` | Defines the building blocks of the privacy checks and the [thresholds](#thresholds) |
| `03_publish.sql` | Opens the `publish` database, apart from the private one, where everything to be published goes |
| `04_versions.sql` | Defines how each record's last version is chosen, without loading every `payload` at once |
| `05_schemas.sql` | The API's data model: the fields the dataset reads from each entity, with their names and types |
| `06_summaries.sql` | Defines the per-call summary of natural persons, with [its rules](privacy.md#rules), the same for the three entities |
| `10_concesiones.sql` | Reads awards and writes to `publish` those to legal persons, record by record, and the summary of those to natural persons |
| `11_ayudasestado.sql`, `12_minimis.sql` | The same for state aid and de minimis aid |
| `13_partidospoliticos.sql`, `14_grandesbeneficiarios.sql` | The same for aid to political parties and for the large beneficiaries that are legal persons |
| `15_convocatorias.sql`, `16_planesestrategicos.sql`, `17_catalogos.sql` | The same for calls, strategic plans and catalogues |
| `80_schema_drift.sql` | Looks for [fields that stopped coming](#drift) |
| `90_checks.sql` | Detaches `bdns-sync`, no longer needed, checks everything about to be published and stops the run if it finds anything |
| `95_export.sql` | Writes each table in `publish` as a Parquet file in `output_dir`, and fails if any is left without one |

<a id="thresholds"></a>
## Thresholds

They are defined once, as macros in `02_privacy.sql`, and both the summary and the checks use them. What each one protects is explained in [the rules](privacy.md#rules).

| Macro | Value | What it controls |
|---|---|---|
| `MIN_BENEFICIARIES()` | 10 | People each summary row must gather at least |
| `MAX_DOMINANT_SHARE()` | 0.5 | Share of a row's amount a single person may hold at most |
| `MIN_BENEFICIARIES_FOR_TAILS()` | 20 | People from which the 10th and 90th percentiles are published |
