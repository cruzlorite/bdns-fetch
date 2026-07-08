# Bases de datos de destino (sinks)

Toda la lógica de sincronización usa SQL portable (subconsultas `EXISTS`/`NOT EXISTS` correlacionadas, sin `MERGE` ni `UPDATE ... FROM` específicos de un motor), por lo que cualquier base de datos con dialecto de SQLAlchemy sirve como destino. Verificado:

| Destino | Estado | Notas |
|---|---|---|
| SQLite | Verificado (suite de tests completa) | Sin configuración adicional |
| BigQuery | Verificado (en vivo, ciclo SCD2 completo) | Requiere el extra `bigquery`; ver más abajo |
| PostgreSQL / MySQL | Compatible por diseño (SQL portable) | Requieren instalar su driver (`psycopg2`, `pymysql`, ...) |

## Arquitectura

El almacenamiento está detrás de una interfaz `Sink` ([`bdns/sync/sinks/`](../bdns/sync/sinks/)): la capa de fetch entrega lotes de registros y el sink es dueño de todo lo demás (versionado SCD2, detección de bajas, registro de ejecuciones). La implementación actual es [`SQLSink`](../bdns/sync/sinks/sql/__init__.py), que cubre cualquier motor con dialecto de SQLAlchemy; las diferencias por motor se concentran en sus adaptadores internos ([`bdns/sync/sinks/sql/dialects.py`](../bdns/sync/sinks/sql/dialects.py)). Un futuro destino no SQL (p. ej. Parquet) sería otra implementación de `Sink`, sin tocar la capa de fetch.

La carga del staging solapa el fetch del lote siguiente con la escritura del actual mediante un pipeline productor/consumidor genérico ([`bdns/sync/pipeline.py`](../bdns/sync/pipeline.py)), con cola acotada como contrapresión. Cifras y justificación en la [sección 7 de bdns-api-behavior.md](bdns-api-behavior.md#7-rendimiento-medido).

## BigQuery

```bash
export BDNS_SYNC_TARGET_URL="bigquery://<proyecto>/<dataset>"
```

- **Autenticación**: credenciales por defecto de la aplicación (`gcloud auth application-default login`) o cuenta de servicio vía `GOOGLE_APPLICATION_CREDENTIALS`.
- **Permisos mínimos**: `roles/bigquery.dataEditor` sobre el dataset y `roles/bigquery.jobUser` sobre el proyecto.
- **Índices**: BigQuery no tiene índices secundarios; el adaptador los omite y en su lugar las tablas se crean con `CLUSTER BY (_natural_key, _is_current)`, las columnas por las que filtra toda la maquinaria SCD2.
- **Escritura por load jobs, no DML**: la carga del staging usa `load_table_from_json` en vez de sentencias INSERT, ~3-4x más rápido y **gratis** (los load jobs no cuentan contra la cuota de bytes de query/DML). Medido en vivo sobre el mismo backfill: ~250-325 filas/s con DML por lotes frente a ~900-1.300 filas/s con load jobs.
- **Escrituras estrictamente en serie**: BigQuery limita las operaciones de actualización por tabla a un ritmo fijo bajo; el envío concurrente de load jobs dispara `429 too many table update operations`, un límite duro de plataforma, no una cuota ampliable.
- **Sin autoincremento**: los identificadores de las tablas de control (`run_id`, `error_id`) los genera la aplicación (microsegundos de época), no la base de datos.
- El resto de diferencias (tipo JSON sin soporte de parámetros bind, `DELETE` que exige `WHERE`, literales `NULL` que requieren tipo explícito) están resueltas y documentadas en [`dialects.py`](../bdns/sync/sinks/sql/dialects.py) y el código de `sinks/sql/`.
