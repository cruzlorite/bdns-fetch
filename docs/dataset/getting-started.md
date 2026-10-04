# Primeros pasos

Mientras no haya una versión publicada, la única forma de tener el dataset es generarlo tú a partir de una copia de `bdns-sync`. En esta página vas a hacerlo con la copia en SQLite que se crea en los [primeros pasos de bdns-sync](../sync/getting-started.md), vas a hacer tu primera consulta a los ficheros y vas a ver qué pasa si un control encuentra algo que no debería publicarse.

## 1. Lo que necesitas

- Una base de datos de `bdns-sync` con, al menos, las concesiones. Si todavía no la tienes, sigue antes sus primeros pasos.
- La [línea de comandos de DuckDB](https://duckdb.org/docs/installation/). Está probado con la versión 1.5.
- Una copia del repositorio, porque el SQL se lanza desde su raíz:

```console
$ git clone https://github.com/cruzlorite/bdns-tools.git
$ cd bdns-tools
```

## 2. Genera el dataset

DuckDB se conecta a tu base de datos en modo solo lectura y trabaja en un fichero propio, que tiene que estar en un sitio privado, porque hasta el final contiene datos personales. Los ficheros Parquet se escriben en la carpeta que indiques en `output_dir`, que tiene que existir:

```console
$ mkdir -p ~/bdns-dataset/salida
$ duckdb ~/bdns-dataset/privado.duckdb \
    -cmd "ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
$ ls ~/bdns-dataset/salida
ayudas_estado_entidades.parquet  concesiones_entidades.parquet  concesiones_personas.parquet  minimis_entidades.parquet
```

Si todo va bien, el comando no muestra nada. Si tu copia está en otra base de datos, solo cambia el `ATTACH`, como se explica en la [referencia](reference/build.md#attach).

## 3. Tu primera consulta

DuckDB lee los ficheros Parquet directamente, sin importarlos antes. Empieza por las concesiones a empresas y entidades, que se publican registro a registro (en esta página los datos son inventados):

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

Las concesiones a personas físicas, en cambio, solo aparecen como un resumen por convocatoria, sin nada que se refiera a una persona concreta:

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

Fíjate en la última fila. Las convocatorias con menos de diez personas se juntan, sin su número, en una fila de resto por año, y aquí son dos convocatorias de 2026, una con seis personas y otra con siete. Por qué se hace así lo explica [cómo se protege a las personas físicas](explanation/anonymisation.md), y en la [guía de consultas](guides/queries.md) tienes más ejemplos.

## 4. Cuando un control para la generación

Antes de escribir los ficheros, la generación revisa lo que va a publicar, y si encuentra algo que podría identificar a una persona física se para sin escribir nada. Por ejemplo, si el título de una convocatoria a una empresa incluyera un DNI:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_entidades: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

El comando termina con código 1 y la carpeta se queda como estaba. Un mensaje así indica un error en el SQL del dataset, así que, si te ocurre, abre una [incidencia](https://github.com/cruzlorite/bdns-tools/issues) con el mensaje, pero sin copiar ningún dato de la fila que lo ha provocado. Todos los controles y sus mensajes están en la [referencia](reference/build.md#checks).
