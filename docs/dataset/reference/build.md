# Generación

Todo el proceso es SQL de DuckDB, sin una línea de Python. Los pasos son ficheros en [`dataset/sql/`](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql), que se pueden leer, revisar y volver a ejecutar tal cual, y `dataset/build.sql` los lanza en orden con la línea de comandos de DuckDB, desde la raíz del repositorio:

```console
$ duckdb /ruta/privada/dataset.duckdb \
    -cmd "ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY);
          SET VARIABLE output_dir = '/ruta/de/salida'" \
    -f dataset/build.sql
```

El fichero de DuckDB (`dataset.duckdb` en el ejemplo) tiene que estar en un sitio privado, porque guarda tablas intermedias con datos personales. La ejecución se para en el primer error, de modo que, si falla un control, no se escribe ningún fichero. Los resultados de cada paso no se muestran, y solo verás algo si hay un error.

<a id="attach"></a>
## Conectar la base de datos de `bdns-sync`

El SQL lee las tablas de `bdns-sync` con el nombre `sync`, así que basta con conectar tu base de datos con ese nombre y en modo solo lectura. DuckDB descarga la extensión que necesita la primera vez.

| Base de datos | `ATTACH` | Probado |
|---|---|---|
| SQLite | `ATTACH '/ruta/a/bdns.db' AS sync (TYPE sqlite, READ_ONLY)` | Sí |
| DuckDB | `ATTACH '/ruta/a/bdns.duckdb' AS sync (READ_ONLY)` | Sí |
| PostgreSQL | `ATTACH 'postgresql://usuario@servidor/bdns' AS sync (TYPE postgres, READ_ONLY)` | Todavía no |
| BigQuery | Con la extensión de la comunidad [`bigquery`](https://duckdb.org/community_extensions/extensions/bigquery.html) | Todavía no |

## Variables

| Variable | Qué es |
|---|---|
| `output_dir` | Carpeta en la que se escriben los ficheros Parquet. Tiene que existir. Si no la indicas, la exportación se para con el mensaje `No output folder: run SET VARIABLE output_dir = '/path/to/output' before the build` |

<a id="steps"></a>
## Los pasos

Las tablas intermedias se quedan en el fichero privado, y solo las del esquema `publish` se escriben como ficheros Parquet.

| Fichero | Qué hace |
|---|---|
| `01_beneficiarios.sql` | Define cómo se clasifica a cada beneficiario a partir de su NIF ([el SQL](#sql)) |
| `02_privacy.sql` | Define las piezas de los controles de privacidad y los [umbrales](#thresholds) |
| `03_publish.sql` | Crea el esquema `publish`, donde va todo lo que se publica |
| `10_concesiones.sql` | Lee las concesiones de `bdns-sync`, con la última versión de cada una y sus columnas con tipo. Privada |
| `11_ayudas_estado.sql` | Lo mismo con las ayudas de Estado. Privada |
| `12_minimis.sql` | Lo mismo con las ayudas de minimis. Privada |
| `20_entidades.sql` | Escribe en `publish` las tres tablas de entidades, registro a registro |
| `30_personas.sql` | Escribe en `publish` el resumen por convocatoria de las personas físicas |
| `90_checks.sql` | Comprueba lo que va a publicarse y para la ejecución si encuentra algo ([los controles](#checks)) |
| `95_export.sql` | Escribe cada tabla de `publish` como un fichero Parquet en `output_dir` |

<a id="thresholds"></a>
## Umbrales

Están definidos una sola vez, como macros en `02_privacy.sql`, y los usan tanto el resumen como los controles. Qué protege cada uno lo explican [las reglas](../explanation/anonymisation.md#rules).

| Macro | Valor | Qué controla |
|---|---|---|
| `min_beneficiaries()` | 10 | Personas que tiene que juntar como mínimo cada fila del resumen |
| `max_dominant_share()` | 0,5 | Parte del importe de una fila que puede tener una sola persona, como máximo |
| `min_beneficiaries_for_tails()` | 20 | Personas a partir de las que se publican los percentiles 10 y 90 |

<a id="checks"></a>
## Controles y mensajes

Si un control encuentra algo, la ejecución termina con código 1 y uno de estos mensajes, precedido de `Invalid Input Error:` y del nombre de la tabla:

| Mensaje | Qué ha encontrado |
|---|---|
| `N rows of protected beneficiaries` | Filas de personas físicas o de otros beneficiarios protegidos en una tabla de entidades |
| `N rows with something shaped like a personal tax ID` | Un valor con forma de DNI, NIE o NIF enmascarado, en cualquier columna |
| `identifying columns: ...` | Una columna que identifica a alguien en el resumen de personas físicas |
| `N rows below 10 beneficiaries` | Filas del resumen que juntan a menos de 10 personas |
| `N rows with 10th or 90th percentiles below 20 beneficiaries` | Filas del resumen con los percentiles 10 o 90 y menos de 20 personas |

Cualquiera de ellos indica un error en un paso anterior. Si te ocurre, abre una [incidencia](https://github.com/cruzlorite/bdns-tools/issues) con el mensaje, sin copiar ningún dato de las filas que lo han provocado.

<a id="sql"></a>
## El SQL

Este es el paso que clasifica a los beneficiarios, mostrado directamente desde el código:

```sql
--8<-- "dataset/sql/01_beneficiarios.sql"
```
