# Cómo se genera el dataset

Mientras no haya una versión publicada, la única forma de tener el dataset es generarlo tú a partir de una copia de `bdns-sync`. Todo el proceso es SQL de DuckDB: los pasos son ficheros en [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), que se pueden leer, revisar y volver a ejecutar tal cual, y `dataset/build.sql` los lanza en orden.

## Lo que necesitas

- Una base de datos de `bdns-sync` con, al menos, las concesiones. Si todavía no la tienes, sigue antes sus [primeros pasos](../sync/getting-started.md).
- La [línea de comandos de DuckDB](https://duckdb.org/docs/installation/). Está probado con la versión 1.5.
- Una copia del repositorio, porque el SQL se lanza desde su raíz:

```console
$ git clone https://github.com/cruzlorite/bdns-tools.git
$ cd bdns-tools
```

## Generarlo

DuckDB se conecta a tu base de datos en modo solo lectura y trabaja en un fichero propio, que tiene que estar en un sitio privado, porque guarda tablas intermedias con datos personales. Los ficheros Parquet se escriben en la carpeta que indiques en `output_dir`, que tiene que existir. Con la copia en SQLite de los primeros pasos de `bdns-sync`:

```console
$ mkdir -p ~/bdns-dataset/salida
$ duckdb ~/bdns-dataset/privado.duckdb \
    -cmd "ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
$ ls ~/bdns-dataset/salida
ayudas_estado_entidades.parquet  concesiones_entidades.parquet  concesiones_personas.parquet  minimis_entidades.parquet
```

Mientras trabaja, muestra la hora a la que empieza cada paso y, al final, `done`, así que puedes seguir una generación larga y ver cuánto tarda cada paso. Estos son los tiempos reales de una copia con 30 millones de concesiones desde 2022:

```text
20:53:45  01_beneficiarios.sql
20:53:45  02_privacy.sql
20:53:45  03_publish.sql
20:53:45  04_versions.sql
20:53:45  10_concesiones.sql
20:57:50  11_ayudas_estado.sql
20:59:22  12_minimis.sql
21:00:12  20_entidades.sql
21:00:39  30_personas.sql
21:01:05  90_checks.sql
21:01:12  95_export.sql
21:01:17  done
```

Si olvidas `output_dir`, se para con el mensaje `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build`.

<a id="attach"></a>
### Con otra base de datos

El SQL lee las tablas de `bdns-sync` con el nombre `sync`, así que solo cambia el `ATTACH`. DuckDB descarga la extensión que necesita la primera vez.

| Base de datos | `ATTACH` | Probado |
|---|---|---|
| SQLite | `ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Sí |
| DuckDB | `ATTACH '/ruta/a/bdns.duckdb' AS sync (READ_ONLY)` | Sí |
| PostgreSQL | `ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY)` | Todavía no |
| BigQuery | Con la extensión de la comunidad [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) y una vista por tabla ([cómo](#bigquery)) | Sí |

<a id="bigquery"></a>
### Desde BigQuery

La extensión [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) nombra las tablas con su dataset (`bq.TU_DATASET.concesiones_busqueda`), así que hacen falta tres vistas con el nombre que espera el SQL. Los datos llegan comprimidos, y solo las columnas que se usan: con 30 millones de concesiones son unos 4,5 GB por la red, y la lectura cuesta céntimos. Necesitas las credenciales de `gcloud auth application-default login`:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "
    SET memory_limit = '4GB';
    SET threads = 4;
    SET preserve_insertion_order = false;
    INSTALL bigquery FROM community; LOAD bigquery;
    ATTACH 'project=TU_PROYECTO' AS bq (TYPE bigquery, READ_ONLY);
    ATTACH ':memory:' AS sync;
    CREATE VIEW sync.concesiones_busqueda  AS SELECT * FROM bq.TU_DATASET.concesiones_busqueda;
    CREATE VIEW sync.ayudasestado_busqueda AS SELECT * FROM bq.TU_DATASET.ayudasestado_busqueda;
    CREATE VIEW sync.minimis_busqueda      AS SELECT * FROM bq.TU_DATASET.minimis_busqueda;
    SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
```

<a id="memory"></a>
### Con mucho histórico

DuckDB usa por defecto hasta el 80 % de la memoria del equipo, y si a la vez tienes otros programas abiertos, el sistema puede llegar a pararlo por falta de memoria. Para evitarlo, ponle un límite al principio de `-cmd`, como en el ejemplo de BigQuery; lo que no quepa lo vuelca a disco, junto al fichero de trabajo. Con `memory_limit = '4GB'` y `threads = 4`, en un portátil de 12 GB, la copia de 30 millones de concesiones se generó en unos ocho minutos sin que DuckDB pasara de 5 GB.

<a id="checks"></a>
## Cuando un control para la generación

Antes de escribir los ficheros, la generación revisa lo que va a publicar, y si encuentra algo que podría identificar a una persona física se para sin escribir nada. Por ejemplo, si el título de una convocatoria a una empresa incluyera un DNI:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_entidades: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

El comando termina con código 1 y la carpeta se queda como estaba. Estos son todos los mensajes posibles, que siempre van precedidos del nombre de la tabla:

| Mensaje | Qué ha encontrado |
|---|---|
| `N rows of protected beneficiaries` | Filas de personas físicas o de otros beneficiarios protegidos en una tabla de entidades |
| `N rows with something shaped like a personal tax ID` | Un valor con forma de DNI, NIE o NIF enmascarado, en cualquier columna |
| `identifying columns: ...` | Una columna que identifica a alguien en el resumen de personas físicas |
| `N rows below 10 beneficiaries` | Filas del resumen que juntan a menos de 10 personas |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Filas del resumen con los percentiles 10 o 90 y menos de 20 personas |

Cualquiera de ellos indica un error en el SQL del dataset, así que, si te ocurre, abre una [incidencia](https://github.com/cruzlorite/bdns-tools/issues) con el mensaje, pero sin copiar ningún dato de las filas que lo han provocado.

<a id="steps"></a>
## Los pasos

Las tablas intermedias se quedan en el fichero privado, y solo las del esquema `publish` se escriben como ficheros Parquet.

| Fichero | Qué hace |
|---|---|
| `01_beneficiarios.sql` | Define cómo se clasifica a cada beneficiario a partir de su NIF |
| `02_privacy.sql` | Define las piezas de los controles de privacidad y los [umbrales](#thresholds) |
| `03_publish.sql` | Crea el esquema `publish`, donde va todo lo que se publica |
| `04_versions.sql` | Define cómo se elige la última versión de cada registro, sin cargar todos los `payload` a la vez |
| `10_concesiones.sql` | Lee las concesiones de `bdns-sync`, con la última versión de cada una y sus columnas con tipo. Privada |
| `11_ayudas_estado.sql` | Lo mismo con las ayudas de Estado. Privada |
| `12_minimis.sql` | Lo mismo con las ayudas de minimis. Privada |
| `20_entidades.sql` | Escribe en `publish` las tres tablas de entidades, registro a registro |
| `30_personas.sql` | Escribe en `publish` el resumen por convocatoria de las personas físicas |
| `90_checks.sql` | Comprueba lo que va a publicarse y para la ejecución si encuentra algo |
| `95_export.sql` | Escribe cada tabla de `publish` como un fichero Parquet en `output_dir` |

<a id="thresholds"></a>
## Umbrales

Están definidos una sola vez, como macros en `02_privacy.sql`, y los usan tanto el resumen como los controles. Qué protege cada uno lo explican [las reglas](privacy.md#rules).

| Macro | Valor | Qué controla |
|---|---|---|
| `min_beneficiaries()` | 10 | Personas que tiene que juntar como mínimo cada fila del resumen |
| `max_dominant_share()` | 0,5 | Parte del importe de una fila que puede tener una sola persona, como máximo |
| `min_beneficiaries_for_tails()` | 20 | Personas a partir de las que se publican los percentiles 10 y 90 |
