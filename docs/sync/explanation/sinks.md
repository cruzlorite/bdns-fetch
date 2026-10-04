# Bases de datos de destino

Toda la lógica de sincronización está escrita en SQL portable (subconsultas `EXISTS` y `NOT EXISTS` correlacionadas, sin `MERGE` ni `UPDATE ... FROM`, que dependen de cada motor), así que puedes usar como destino cualquier base de datos que tenga dialecto de SQLAlchemy. Estas son las que están probadas:

| Destino | Estado | Notas |
|---|---|---|
| SQLite | Probada con todos los tests | No necesita nada más |
| DuckDB | Probada con todos los tests | Necesita `duckdb-engine` y `pytz`. Es local y no necesita servidor, y para análisis con mucho volumen funciona mejor que SQLite |
| BigQuery | Probada contra el servicio real, con el ciclo SCD2 completo | Necesita el extra `bigquery`; más detalles abajo |
| PostgreSQL | Probada con todos los tests, también contra un servidor real en la integración continua | Necesita `psycopg2` |

## Cómo está organizado

El almacenamiento está detrás de la interfaz [`Sink`][bdns.sync.sinks.Sink] ([`bdns.sync.sinks`](../reference/api/sinks.md)): la parte que descarga entrega lotes de registros y el sink se encarga de todo lo demás (el versionado SCD2, la detección de bajas y el registro de ejecuciones). La única implementación por ahora es [`SQLSink`](../reference/api/sinks.sql.md), que sirve para cualquier motor con dialecto de SQLAlchemy; lo que cambia de un motor a otro está aislado en sus adaptadores ([`bdns.sync.sinks.sql.dialects`](../reference/api/sinks.sql.dialects.md)). Un destino que no fuera SQL, como Parquet, sería otra implementación de [`Sink`][bdns.sync.sinks.Sink], sin tocar la parte que descarga.

Mientras se carga el staging, la descarga del siguiente lote se hace a la vez que la escritura del actual, con una cola de tamaño limitado entre las dos ([`pipeline.py`](../reference/api/pipeline.md)) para que la descarga espere si la escritura va más lenta. Las cifras están en [rendimiento](sync-behavior.md#performance).

## BigQuery

```bash
export BDNS_SYNC_TARGET_URL="bigquery://<proyecto>/<dataset>"
```

- **Autenticación**: con las credenciales por defecto de la aplicación (`gcloud auth application-default login`) o con una cuenta de servicio a través de `GOOGLE_APPLICATION_CREDENTIALS`.
- **Permisos mínimos**: `roles/bigquery.dataEditor` sobre el dataset y `roles/bigquery.jobUser` sobre el proyecto.
- **Índices**: BigQuery no tiene índices secundarios, así que el adaptador no los crea y, en su lugar, agrupa las tablas con `CLUSTER BY (_natural_key, _is_current)`, que son las columnas por las que filtra todo el proceso SCD2.
- **Escritura con *load jobs* en lugar de DML**: el staging se carga con `load_table_from_json` y no con sentencias `INSERT`, lo que es entre tres y cuatro veces más rápido y además **gratis**, porque los *load jobs* no cuentan para la cuota de bytes de consultas y DML. En la misma carga histórica contra el servicio real, con DML por lotes se escribían entre 250 y 325 filas por segundo, y con *load jobs*, entre 900 y 1.300.
- **Las escrituras van siempre de una en una**: BigQuery limita a un ritmo fijo y bajo las operaciones de actualización sobre una misma tabla, y si se lanzan varios *load jobs* a la vez aparece el error `429 too many table update operations`, que es un límite de la plataforma y no una cuota que se pueda ampliar.
- **Sin autoincremento**: los identificadores de las tablas de control (`run_id` y `error_id`) los genera la aplicación a partir de los microsegundos transcurridos desde 1970, no la base de datos.
- El resto de diferencias (el tipo JSON no admite parámetros, `DELETE` exige `WHERE`, los `NULL` literales necesitan un tipo explícito) están resueltas y explicadas en [`dialects`](../reference/api/sinks.sql.dialects.md) y en el código de `sinks/sql/`.
