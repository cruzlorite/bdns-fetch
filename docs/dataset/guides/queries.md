# Consultar los datos

Esta guía reúne consultas de ejemplo sobre los ficheros del dataset. Están escritas para DuckDB, que lee Parquet directamente, y al final tienes cómo hacer lo mismo con pandas. Los resultados son de unos datos inventados, y las columnas de cada tabla están en la [referencia](../reference/tables.md).

## Quién recibe más

Un mismo NIF puede aparecer con el nombre escrito de varias formas, así que agrupa por NIF y quédate con el nombre de su concesión más reciente:

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

Las concesiones que la API ya ha retirado siguen en el dataset, con `retirada = true`. Son justo las que no puedes conseguir de otra forma, así que no las quites sin pensarlo; fíltralas (`WHERE NOT retirada`) solo si quieres ver lo mismo que muestra hoy el portal.

## Cómo se reparte una convocatoria entre personas físicas

Cada fila de `concesiones_personas` resume una convocatoria. Los percentiles se calculan sobre las concesiones, de modo que una persona con dos concesiones cuenta dos veces en ellos, aunque en `beneficiarios` cuente una:

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

Se lee así: la mitad de las concesiones fue de entre 1.800 y 2.400 euros, y el 80 % de entre 1.200 y 3.600. El percentil 10 y el 90 solo se publican cuando la fila junta al menos a 20 personas, así que en las convocatorias pequeñas esas columnas vienen vacías. El mínimo y el máximo no se publican nunca.

## Cuándo se concedieron

Las fechas tienen los mismos percentiles, y cada uno es una fecha de concesión real. Entre `fecha_p10` y `fecha_p90` cae el 80 % de las concesiones, así que esta consulta busca las convocatorias en las que ese 80 % se concedió en un mismo mes:

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

## Una convocatoria entera: empresas y personas

Una convocatoria puede tener beneficiarios de los dos tipos. Las empresas y entidades están en `concesiones_entidades`, una fila por concesión, y las personas, en el resumen, así que para verla entera junta las dos tablas por `numero_convocatoria`:

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

Ten en cuenta que, si una convocatoria usa varios instrumentos (por ejemplo, subvenciones y préstamos), tiene un resumen por cada uno, y entonces conviene agrupar también por `instrumento`.

## Totales por año

Las filas de resto no dicen qué convocatorias juntan, pero sí su año (`ejercicio`), que es el de la fecha mediana de cada una de ellas. Si usas el mismo criterio para las convocatorias publicadas, puedes sumarlo todo por año:

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

Aun así, el total se queda algo corto, porque las concesiones que no llegan a ninguna fila publicable (por ejemplo, una convocatoria pequeña que es la única de su año) no están en el dataset.

## Con pandas

pandas lee los mismos ficheros con `read_parquet`, para lo que necesita `pyarrow` (`pip install pandas pyarrow`):

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
