# Get started

Until a version is published, the only way to have the dataset is to build it yourself from a `bdns-sync` copy. On this page you will do so with the SQLite copy created in [bdns-sync's get started](../sync/getting-started.md), run your first query on the files and see what happens when a check finds something that must not be published.

## 1. What you need

- A `bdns-sync` database with, at least, the awards. If you do not have one yet, follow its get started first.
- The [DuckDB command line](https://duckdb.org/docs/installation/). It is tested with version 1.5.
- A copy of the repository, since the SQL runs from its root:

```console
$ git clone https://github.com/cruzlorite/bdns-tools.git
$ cd bdns-tools
```

## 2. Build the dataset

DuckDB attaches your database read-only and works in a file of its own, which must be somewhere private, because it holds personal data until the end. The Parquet files are written to the folder you set in `output_dir`, which must exist:

```console
$ mkdir -p ~/bdns-dataset/salida
$ duckdb ~/bdns-dataset/privado.duckdb \
    -cmd "ATTACH '/path/to/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
$ ls ~/bdns-dataset/salida
ayudas_estado_entidades.parquet  concesiones_entidades.parquet  concesiones_personas.parquet  minimis_entidades.parquet
```

If all goes well, the command prints nothing. If your copy lives in another database, only the `ATTACH` changes, as the [reference](reference/build.md#attach) explains.

## 3. Your first query

DuckDB reads Parquet files directly, without importing them first. Start with the awards to companies and organisations, published record by record (the data on this page is made up):

```console
$ cd ~/bdns-dataset/salida
$ duckdb -c "SELECT nif, nombre, importe, convocatoria FROM 'concesiones_entidades.parquet' LIMIT 3"
┌───────────┬───────────────────────────┬───────────────┬──────────────────────────────────────────┐
│    nif    │          nombre           │    importe    │               convocatoria               │
│  varchar  │          varchar          │ decimal(18,2) │                 varchar                  │
├───────────┼───────────────────────────┼───────────────┼──────────────────────────────────────────┤
│ B12345678 │ CONSTRUCCIONES EJEMPLO SL │      12000.00 │ Ayudas a la contratación indefinida 2026 │
│ B23456789 │ TALLERES MODELO SL        │       8000.00 │ Ayudas a la contratación indefinida 2026 │
│ B12345678 │ CONSTRUCCIONES EJEMPLO SL │       8000.00 │ Ayudas a la contratación indefinida 2026 │
└───────────┴───────────────────────────┴───────────────┴──────────────────────────────────────────┘
```

Awards to natural persons, on the other hand, only appear as one summary per call, with nothing about any one person:

```console
$ duckdb -c "
    SELECT numero_convocatoria, es_resto, ejercicio, concesiones, beneficiarios, importe_mediana
    FROM 'concesiones_personas.parquet'
    ORDER BY beneficiarios DESC"
┌─────────────────────┬──────────┬───────────┬─────────────┬───────────────┬─────────────────┐
│ numero_convocatoria │ es_resto │ ejercicio │ concesiones │ beneficiarios │ importe_mediana │
│       varchar       │ boolean  │   int64   │    int64    │     int64     │  decimal(18,2)  │
├─────────────────────┼──────────┼───────────┼─────────────┼───────────────┼─────────────────┤
│ 900101              │ false    │      NULL │         250 │           250 │         2400.00 │
│ 900102              │ false    │      NULL │          40 │            40 │          240.00 │
│ 900103              │ false    │      NULL │          14 │            14 │         3000.00 │
│ NULL                │ true     │      2026 │          13 │            13 │         8000.00 │
└─────────────────────┴──────────┴───────────┴─────────────┴───────────────┴─────────────────┘
```

Look at the last row. Calls with fewer than ten people are gathered, without their number, into one rest row per year, and here it holds two 2026 calls, one with six people and one with seven. [How natural persons are protected](explanation/anonymisation.md) explains why, and the [queries guide](guides/queries.md) has more examples.

## 4. When a check stops the build

Before writing the files, the build checks what it is about to publish, and if it finds anything that could identify a natural person it stops without writing anything. For example, if the title of a call awarded to a company held a DNI:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_entidades: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

The command exits with code 1 and the folder stays as it was. Such a message points to a fault in the dataset's SQL, so if it happens to you, open an [issue](https://github.com/cruzlorite/bdns-tools/issues) with the message, without copying any data from the row that caused it. Every check and its message are in the [reference](reference/build.md#checks).
