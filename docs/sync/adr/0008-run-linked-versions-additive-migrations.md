# 0008. Versiones enlazadas a su ejecución, y migraciones solo aditivas

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Quien consulta un histórico SCD2 hace preguntas que el esquema tiene que
poder contestar sin adivinar:

- ¿Qué cambió en la ejecución de ayer? Con solo `_valid_from` se
  aproxima por fecha, y dos ejecuciones el mismo día se confunden.
- ¿Este registro se dio de baja, o cambió? Una versión cerrada por un
  cambio y otra cerrada porque el registro desapareció quedan iguales; la
  diferencia solo se deduce buscando si existe una versión posterior.
- ¿Qué rango cubrió cada ejecución por ventana? Sin el rango en el
  registro de ejecuciones, no se puede auditar si falta algún tramo del
  histórico.

Añadir columnas a destinos ya en producción, algunos con decenas de
millones de filas en BigQuery, exige una migración. Una herramienta de
migraciones completa (versiones, scripts de subida y bajada) es mucho
para un esquema que cambia rara vez, y renombrar o cambiar tipos de
columnas en BigQuery es caro y arriesgado.

## Decisión

Cada versión registra la ejecución que la creó (`_created_run_id`) y, al
cerrarse, la que la cerró y por qué (`_closed_run_id`, `_closed_reason`:
`superseded` si la sustituye un payload distinto, `removed` si la fuente
dejó de servir la clave). `_sync_runs` registra también las claves
cambiadas y sin cambios (`rows_changed`, `rows_unchanged`) y el rango de
una ejecución por ventana (`window_start`, `window_end`).

El esquema **solo crece, y solo con columnas que admiten nulos**. Al
empezar cada ejecución,
[`add_missing_columns`][bdns.sync.sinks.sql.migrate.add_missing_columns]
añade a las tablas existentes las columnas que les falten. Nunca se
renombra, se cambia de tipo ni se borra una columna.

## Consecuencias

- "Qué cambió en la ejecución X" y "qué se dio de baja" son consultas
  directas.
- Un destino escrito por una versión anterior se actualiza solo; las
  filas anteriores tienen `NULL` en las columnas nuevas.
- Un cambio de esquema que no sea aditivo no cabe en este mecanismo: si
  alguna vez hace falta, será una versión mayor con instrucciones de
  migración.
