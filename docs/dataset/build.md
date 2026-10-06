# Cómo se genera el dataset

Mientras no haya una versión publicada, la única forma de tener el dataset es generarlo tú a partir de una copia de `bdns-sync`. Todo el proceso es SQL de DuckDB: los pasos son ficheros en [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), que se pueden leer, revisar y volver a ejecutar tal cual, y `dataset/build.sql` los lanza en orden.

## Lo que necesitas

- Una base de datos de `bdns-sync` con todas las entidades, como la que deja `bdns-sync delta`. Si todavía no la tienes, sigue antes sus [primeros pasos](../sync/getting-started.md).
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
ayudasestado_personas_juridicas.parquet  concesiones_personas_juridicas.parquet  concesiones_personas_fisicas.parquet  minimis_personas_juridicas.parquet
```

Mientras trabaja, muestra la hora a la que empieza cada paso y, al final, `done`, así que puedes seguir una generación larga y ver cuánto tarda cada paso. Estos son los tiempos reales de una copia con 30 millones de concesiones desde 2022, leída desde BigQuery:

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

Si olvidas `output_dir`, se para con el mensaje `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build`.

<a id="attach"></a>
### Con otra base de datos

El SQL lee las tablas de `bdns-sync` con el nombre `sync`, así que solo cambia el `ATTACH`. DuckDB descarga la extensión que necesita la primera vez.

| Base de datos | `ATTACH` | Probado |
|---|---|---|
| SQLite | `ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Sí |
| DuckDB | `ATTACH '/ruta/a/bdns.duckdb' AS sync (READ_ONLY)` | Sí |
| PostgreSQL | `ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY)` | Sí |
| BigQuery | Con la extensión de la comunidad [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) ([cómo](#bigquery)) | Sí |

<a id="bigquery"></a>
### Desde BigQuery

La extensión [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) conecta tu proyecto y, si le indicas el dataset en el `ATTACH`, encuentra las tablas con el nombre que espera el SQL. Los datos llegan comprimidos, y solo las columnas que se usan: con 30 millones de concesiones son unos 4,5 GB por la red, y la lectura cuesta céntimos. Necesitas las credenciales de `gcloud auth application-default login`:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "
    SET memory_limit = '3GB';
    SET threads = 4;
    SET preserve_insertion_order = false;
    INSTALL bigquery FROM community; LOAD bigquery;
    ATTACH 'project=TU_PROYECTO dataset=TU_DATASET' AS sync (TYPE bigquery, READ_ONLY);
    SET VARIABLE output_dir = '$HOME/bdns-dataset/salida'" \
    -f dataset/build.sql
```

<a id="memory"></a>
### Con mucho histórico

DuckDB usa por defecto hasta el 80 % de la memoria del equipo, y si a la vez tienes otros programas abiertos, el sistema puede llegar a pararlo por falta de memoria. Para evitarlo, ponle un límite al principio de `-cmd`, como en el ejemplo de BigQuery; lo que no quepa lo vuelca a disco, junto al fichero de trabajo. Ten en cuenta que el proceso ocupa bastante más que ese límite, porque la extensión de BigQuery usa memoria por su cuenta: con `memory_limit = '3GB'` y `threads = 4`, en un portátil de 12 GB, la copia de 30 millones de concesiones se generó en 11 minutos y el proceso llegó a 7,6 GB.

<a id="checks"></a>
## Cuando un control para la generación

Antes de escribir los ficheros, la generación revisa lo que va a publicar, y si encuentra algo que podría identificar a una persona física se para sin escribir nada. Por ejemplo, si el título de una convocatoria a una empresa incluyera un DNI:

```console
$ duckdb ~/bdns-dataset/privado.duckdb -cmd "..." -f dataset/build.sql
Invalid Input Error: publish.concesiones_personas_juridicas: 1 rows with something shaped like a personal tax ID
$ ls ~/bdns-dataset/salida
$
```

El comando termina con código 1 y la carpeta se queda como estaba. Los controles no van tabla a tabla: revisan todas las tablas de `publish` y reconocen el tipo de cada una por sus columnas, así que una tabla nueva queda controlada sin tocar nada. Estos son todos los mensajes posibles, que siempre van precedidos del nombre de la tabla:

| Mensaje | Qué ha encontrado |
|---|---|
| `N rows of protected beneficiaries` | Filas de personas físicas o de otros beneficiarios protegidos en una tabla de entidades |
| `N rows with something shaped like a personal tax ID` | Un valor con forma de DNI, NIE o NIF enmascarado, en cualquier columna |
| `identifying columns: ...` | Una columna que identifica a alguien en el resumen de personas físicas |
| `N rows below 10 beneficiaries` | Filas del resumen que juntan a menos de 10 personas |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Filas del resumen con los percentiles 10 o 90 y menos de 20 personas |

Cualquiera de ellos indica un error en el SQL del dataset, así que, si te ocurre, abre una [incidencia](https://github.com/cruzlorite/bdns-tools/issues) con el mensaje, pero sin copiar ningún dato de las filas que lo han provocado.

Al final, la exportación también se para si una tabla de `publish` se ha quedado sin su fichero (`Published but not exported`), porque cada tabla necesita su línea en `95_export.sql`.

<a id="drift"></a>
## Cuando la API deja de mandar un campo

Los campos que lee el dataset están listados en `05_schemas.sql`. Si la API renombra o retira uno, o cambia su formato, ese campo llegaría vacío sin que nadie se diera cuenta, así que la generación avisa cuando uno ha venido vacío en todos los registros que `bdns-sync` guardó en los últimos 30 días de su tabla:

```text
warning: planesestrategicos.tipoPlan is empty in every record stored in its last 30 days
```

Es un aviso y no un error, porque un campo poco frecuente puede pasar un mes vacío. Si se repite, compara un registro reciente de la API con `05_schemas.sql`. Los campos nuevos que añada la API no dan aviso: se ignoran hasta que alguien los declara, así que nunca se publica nada por sorpresa.

<a id="steps"></a>
## Los pasos

Las tablas intermedias se quedan en el fichero privado, y solo las de la base `publish`, que va aparte, se escriben como ficheros Parquet.

| Fichero | Qué hace |
|---|---|
| `01_beneficiarios.sql` | Define cómo se clasifica a cada beneficiario a partir de su NIF |
| `02_privacy.sql` | Define las piezas de los controles de privacidad y los [umbrales](#thresholds) |
| `03_publish.sql` | Abre la base `publish`, aparte de la privada, donde va todo lo que se publica |
| `04_versions.sql` | Define cómo se elige la última versión de cada registro, sin cargar todos los `payload` a la vez |
| `05_schemas.sql` | El modelo de datos de la API: los campos que lee el dataset de cada entidad, con sus nombres y sus tipos |
| `06_summaries.sql` | Define el resumen por convocatoria de las personas físicas, con [sus reglas](privacy.md#rules), igual para las tres entidades |
| `10_concesiones.sql` | Lee las concesiones y escribe en `publish` las de personas jurídicas, registro a registro, y el resumen de las de personas físicas |
| `11_ayudasestado.sql`, `12_minimis.sql` | Lo mismo con las ayudas de Estado y las de minimis |
| `13_partidospoliticos.sql`, `14_grandesbeneficiarios.sql` | Lo mismo con las ayudas a partidos políticos y con los grandes beneficiarios que son personas jurídicas |
| `15_convocatorias.sql`, `16_planesestrategicos.sql`, `17_catalogos.sql` | Lo mismo con las convocatorias, los planes estratégicos y los catálogos |
| `80_schema_drift.sql` | Busca los [campos que han dejado de llegar](#drift) |
| `90_checks.sql` | Desconecta `bdns-sync`, que ya no hace falta, comprueba todo lo que va a publicarse y para la ejecución si encuentra algo |
| `95_export.sql` | Escribe cada tabla de `publish` como un fichero Parquet en `output_dir`, y falla si alguna se queda sin fichero |

<a id="thresholds"></a>
## Umbrales

Están definidos una sola vez, como macros en `02_privacy.sql`, y los usan tanto el resumen como los controles. Qué protege cada uno lo explican [las reglas](privacy.md#rules).

| Macro | Valor | Qué controla |
|---|---|---|
| `MIN_BENEFICIARIES()` | 10 | Personas que tiene que juntar como mínimo cada fila del resumen |
| `MAX_DOMINANT_SHARE()` | 0,5 | Parte del importe de una fila que puede tener una sola persona, como máximo |
| `MIN_BENEFICIARIES_FOR_TAILS()` | 20 | Personas a partir de las que se publican los percentiles 10 y 90 |
