# Bases de datos de destino (sinks)

Toda la lógica de sincronización se escribe en SQL portable (subconsultas `EXISTS`/`NOT EXISTS` correlacionadas, sin `MERGE` ni `UPDATE ... FROM` propios de un motor concreto), así que sirve como destino cualquier base de datos con dialecto de SQLAlchemy. Lo comprobado hasta ahora:

| Destino | Estado | Notas |
|---|---|---|
| SQLite | Comprobado (suite de tests completa) | Sin configuración adicional |
| BigQuery | Comprobado contra el servicio real (ciclo SCD2 completo) | Requiere el extra `bigquery`; ver más abajo |
| PostgreSQL / MySQL | Compatibles por diseño (SQL portable) | Hay que instalar su driver (`psycopg2`, `pymysql`, ...) |

## Arquitectura

El almacenamiento queda detrás de una interfaz `Sink` ([`bdns/sync/sinks/`](../bdns/sync/sinks/)): la capa de fetch entrega lotes de registros y el sink se encarga de todo lo demás (versionado SCD2, detección de bajas, registro de ejecuciones). La implementación actual es [`SQLSink`](../bdns/sync/sinks/sql/__init__.py), que cubre cualquier motor con dialecto de SQLAlchemy; las diferencias entre motores se concentran en sus adaptadores internos ([`bdns/sync/sinks/sql/dialects.py`](../bdns/sync/sinks/sql/dialects.py)). Un destino futuro que no sea SQL (Parquet, por ejemplo) sería otra implementación de `Sink`, sin tocar la capa de fetch.

Al cargar el staging se solapa la descarga del lote siguiente con la escritura del actual, mediante un pipeline productor/consumidor genérico ([`bdns/sync/pipeline.py`](../bdns/sync/pipeline.py)), con una cola acotada que hace de contrapresión. Las cifras y el porqué están en la [sección 7 de bdns-api-behavior.md](bdns-api-behavior.md#7-rendimiento-medido).

## BigQuery

```bash
export BDNS_SYNC_TARGET_URL="bigquery://<proyecto>/<dataset>"
```

- **Autenticación**: credenciales por defecto de la aplicación (`gcloud auth application-default login`) o cuenta de servicio con `GOOGLE_APPLICATION_CREDENTIALS`.
- **Permisos mínimos**: `roles/bigquery.dataEditor` sobre el dataset y `roles/bigquery.jobUser` sobre el proyecto.
- **Índices**: BigQuery no tiene índices secundarios; el adaptador los omite y, en su lugar, crea las tablas con `CLUSTER BY (_natural_key, _is_current)`, que son las columnas por las que filtra toda la maquinaria SCD2.
- **Escritura con load jobs, no con DML**: el staging se carga con `load_table_from_json` en vez de con sentencias INSERT, entre 3 y 4 veces más rápido y además **gratis** (los load jobs no cuentan para la cuota de bytes de query/DML). Medido sobre la misma carga histórica contra el servicio real: entre 250 y 325 filas/s con DML por lotes, frente a entre 900 y 1.300 filas/s con load jobs.
- **Escrituras estrictamente en serie**: BigQuery limita a un ritmo fijo y bajo las operaciones de actualización sobre una misma tabla; si se envían load jobs en paralelo salta `429 too many table update operations`, un límite duro de la plataforma y no una cuota que se pueda ampliar.
- **Sin autoincremento**: los identificadores de las tablas de control (`run_id`, `error_id`) los genera la aplicación (microsegundos desde el epoch), no la base de datos.
- El resto de diferencias (el tipo JSON no admite parámetros bind, `DELETE` exige `WHERE`, los literales `NULL` necesitan tipo explícito) están resueltas y explicadas en [`dialects.py`](../bdns/sync/sinks/sql/dialects.py) y en el código de `sinks/sql/`.
