# Query the data

This guide gathers example queries on the dataset's files. They are written for DuckDB, which reads Parquet directly, and the end shows how to do the same with pandas. The results come from made-up data, and each table's columns are in the [reference](../reference/tables.md).

## Who receives the most

The same tax ID may appear with its name spelt in several ways, so group by tax ID and keep the name of its latest award:

```sql
SELECT
    nif,
    arg_max(nombre, fecha_concesion) AS nombre,
    count(*) AS concesiones,
    sum(importe) AS importe
FROM 'concesiones_entidades.parquet'
GROUP BY nif
ORDER BY importe DESC
LIMIT 3;
```

```text
┌───────────┬─────────────────────────────────────────┬─────────────┬───────────────┐
│    nif    │                 nombre                  │ concesiones │    importe    │
│  varchar  │                 varchar                 │    int64    │ decimal(38,2) │
├───────────┼─────────────────────────────────────────┼─────────────┼───────────────┤
│ F45678901 │ COOPERATIVA AGRARIA EJEMPLO             │           2 │     100000.00 │
│ G78901234 │ FUNDACIÓN PARA LA INVESTIGACIÓN EJEMPLO │           1 │      90000.00 │
│ A34567890 │ ENERGÍAS DEL EJEMPLO SA                 │           1 │      45000.00 │
└───────────┴─────────────────────────────────────────┴─────────────┴───────────────┘
```

Awards the API has already withdrawn stay in the dataset, with `retirada = true`. They are precisely the ones you cannot get any other way, so do not drop them without thinking; filter them out (`WHERE NOT retirada`) only if you want to see what the portal shows today.

## How a call is shared out among natural persons

Each row of `concesiones_personas` summarises one call. Percentiles are computed over awards, so a person with two awards counts twice in them, though only once in `beneficiarios`:

```sql
SELECT concesiones, beneficiarios, importe_total,
       importe_p10, importe_p25, importe_mediana, importe_p75, importe_p90
FROM 'concesiones_personas.parquet'
WHERE numero_convocatoria = '900101';
```

```text
┌─────────────┬───────────────┬───────────────┬───────────────┬───────────────┬─────────────────┬───────────────┬───────────────┐
│ concesiones │ beneficiarios │ importe_total │  importe_p10  │  importe_p25  │ importe_mediana │  importe_p75  │  importe_p90  │
│    int64    │     int64     │ decimal(38,2) │ decimal(18,2) │ decimal(18,2) │  decimal(18,2)  │ decimal(18,2) │ decimal(18,2) │
├─────────────┼───────────────┼───────────────┼───────────────┼───────────────┼─────────────────┼───────────────┼───────────────┤
│         250 │           250 │     588000.00 │       1200.00 │       1800.00 │         2400.00 │       2400.00 │       3600.00 │
└─────────────┴───────────────┴───────────────┴───────────────┴───────────────┴─────────────────┴───────────────┴───────────────┘
```

It reads like this: half the awards were between 1,800 and 2,400 euros, and 80% between 1,200 and 3,600. The 10th and 90th percentiles are only published when the row gathers at least 20 people, so in small calls those columns are empty. The smallest and largest values are never published.

## When they were awarded

Dates have the same percentiles, and each one is a real award date. Between `fecha_p10` and `fecha_p90` lie 80% of the awards, so this query finds the calls where that 80% was awarded within one month:

```sql
SELECT numero_convocatoria, beneficiarios, fecha_p10, fecha_mediana, fecha_p90
FROM 'concesiones_personas.parquet'
WHERE date_trunc('month', fecha_p10) = date_trunc('month', fecha_p90);
```

```text
┌─────────────────────┬───────────────┬────────────┬───────────────┬────────────┐
│ numero_convocatoria │ beneficiarios │ fecha_p10  │ fecha_mediana │ fecha_p90  │
│       varchar       │     int64     │    date    │     date      │    date    │
├─────────────────────┼───────────────┼────────────┼───────────────┼────────────┤
│ 900102              │            40 │ 2025-10-06 │ 2025-10-08    │ 2025-10-10 │
└─────────────────────┴───────────────┴────────────┴───────────────┴────────────┘
```

## A whole call: companies and people

A call may have beneficiaries of both kinds. Companies and organisations are in `concesiones_entidades`, one row per award, and people in the summary, so to see the whole call join both tables on `numero_convocatoria`:

```sql
WITH entidades AS (
    SELECT numero_convocatoria, count(*) AS concesiones, sum(importe) AS importe
    FROM 'concesiones_entidades.parquet'
    GROUP BY numero_convocatoria
)
SELECT
    p.numero_convocatoria,
    p.concesiones AS concesiones_personas,
    p.importe_total AS importe_personas,
    e.concesiones AS concesiones_entidades,
    e.importe AS importe_entidades
FROM 'concesiones_personas.parquet' p
LEFT JOIN entidades e USING (numero_convocatoria)
WHERE NOT p.es_resto
ORDER BY p.numero_convocatoria;
```

```text
┌─────────────────────┬──────────────────────┬──────────────────┬───────────────────────┬───────────────────┐
│ numero_convocatoria │ concesiones_personas │ importe_personas │ concesiones_entidades │ importe_entidades │
│       varchar       │        int64         │  decimal(38,2)   │         int64         │   decimal(38,2)   │
├─────────────────────┼──────────────────────┼──────────────────┼───────────────────────┼───────────────────┤
│ 900101              │                  250 │        588000.00 │                  NULL │              NULL │
│ 900102              │                   40 │          8580.00 │                  NULL │              NULL │
│ 900103              │                   14 │         51000.00 │                     1 │          90000.00 │
└─────────────────────┴──────────────────────┴──────────────────┴───────────────────────┴───────────────────┘
```

Bear in mind that a call using several instruments (grants and loans, for example) has one summary per instrument, and then you should group by `instrumento` too.

## Totals per year

Rest rows do not say which calls they gather, but they do give their year (`ejercicio`), the year of each call's median award date. Using the same rule for the published calls, you can add everything up per year:

```sql
SELECT
    coalesce(ejercicio, year(fecha_mediana)) AS ejercicio,
    sum(concesiones) AS concesiones,
    sum(importe_total) AS importe
FROM 'concesiones_personas.parquet'
GROUP BY ALL
ORDER BY ejercicio;
```

```text
┌───────────┬─────────────┬───────────────┐
│ ejercicio │ concesiones │    importe    │
│   int64   │   int128    │ decimal(38,2) │
├───────────┼─────────────┼───────────────┤
│      2025 │          40 │       8580.00 │
│      2026 │         277 │     734000.00 │
└───────────┴─────────────┴───────────────┘
```

Even so, the total falls somewhat short, because awards that reach no publishable row (a small call that is the only one in its year, for example) are not in the dataset.

## With pandas

pandas reads the same files with `read_parquet`, which needs `pyarrow` (`pip install pandas pyarrow`):

```python
import pandas as pd

personas = pd.read_parquet("concesiones_personas.parquet")
convocatorias = personas[~personas["es_resto"]]
print(convocatorias.nlargest(3, "beneficiarios")[["numero_convocatoria", "beneficiarios", "importe_mediana"]])
```

```text
  numero_convocatoria  beneficiarios importe_mediana
1              900101            250         2400.00
2              900102             40          240.00
0              900103             14         3000.00
```
