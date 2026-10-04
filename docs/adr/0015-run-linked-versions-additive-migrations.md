# 0015. Cada versión sabe qué ejecución la creó, y el esquema solo crece

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Quien consulta un histórico SCD2 se hace preguntas que el esquema tiene que poder responder sin adivinar:

- ¿Qué cambió en la ejecución de ayer? Con `_valid_from` solo se puede aproximar por la fecha, y dos ejecuciones del mismo día se confunden.
- ¿Este registro se dio de baja o cambió? Una versión cerrada por un cambio y otra cerrada porque el registro desapareció quedan exactamente igual, y la diferencia solo se puede deducir buscando si hay una versión posterior.
- ¿Qué periodo cubrió cada ejecución incremental? Si el periodo no queda anotado, no hay forma de comprobar si falta algún trozo del histórico.

Añadir columnas a bases de datos que ya están en producción, algunas con decenas de millones de filas en BigQuery, exige migrarlas. Una herramienta de migraciones completa (con versiones y scripts para subir y bajar) es demasiado para un esquema que cambia muy de vez en cuando, y en BigQuery renombrar columnas o cambiar su tipo es caro y arriesgado.

## Decisión

Cada versión anota qué ejecución la creó (`_created_run_id`) y, cuando se cierra, qué ejecución la cerró y por qué (`_closed_run_id` y `_closed_reason`, que vale `superseded` si la sustituye un contenido distinto y `removed` si la API ha dejado de devolver la clave). `_sync_runs` anota además cuántas claves cambiaron y cuántas no (`rows_changed`, `rows_unchanged`) y, en las ejecuciones incrementales, el periodo que cubrieron (`window_start`, `window_end`).

El esquema **solo crece, y siempre con columnas que admiten valores nulos**. Al empezar cada ejecución, [`add_missing_columns`][bdns.sync.sinks.sql.migrate.add_missing_columns] añade a las tablas existentes las columnas que les falten. Nunca se renombra una columna, se le cambia el tipo ni se borra.

## Consecuencias

- «Qué cambió en la ejecución X» y «qué se ha dado de baja» se responden con una consulta directa.
- Una base de datos creada con una versión anterior se actualiza sola, y las filas que ya había tienen `NULL` en las columnas nuevas.
- Un cambio de esquema que no consista en añadir columnas no cabe en este mecanismo. Si algún día hace falta, será en una versión mayor y con instrucciones para migrar.
