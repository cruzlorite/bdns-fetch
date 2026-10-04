# 0002. Staging y comparación en bloque, nunca fila a fila

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al primer commit del repositorio)

## Contexto

Aplicar SCD2 a un lote requiere cuatro operaciones: insertar las claves nuevas, cerrar las versiones cuyo hash ha cambiado, actualizar las que no han cambiado y cerrar las que han desaparecido.

Lo más directo sería un bucle que, para cada registro, consultara su versión vigente y decidiera qué hacer. Pero `concesiones_busqueda` tiene más de 20 millones de filas.

Y en BigQuery cada sentencia DML tiene una latencia y un coste fijos, toque las filas que toque, así que un bucle de miles de `UPDATE` de una sola fila no es viable de ninguna manera.

## Decisión

El lote se carga en una tabla de staging y la comparación se hace con un **número fijo de sentencias en bloque**, tenga el lote 20 filas o 2 millones.

Solo se usa SQL portable (subconsultas `EXISTS` y `NOT EXISTS` correlacionadas, sin `UPDATE ... FROM` ni `MERGE`, que dependen de cada motor), así que el mismo código funciona sin cambios en SQLite, PostgreSQL y BigQuery.

## Consecuencias

- El número de sentencias no depende del tamaño del lote.
- Los contadores hay que calcularlos **antes** de escribir, porque cada sentencia cambia lo que contaría la siguiente.
- Hace falta una tabla de staging por entidad, que se vacía al principio y al final de cada ejecución.
- Las diferencias entre motores están aisladas en sus adaptadores ([`sinks.sql.dialects`][bdns.sync.sinks.sql.dialects]); fuera de ahí, nada depende del nombre del motor.
- Un destino sin conexión, sin `UPDATE` y sin transacciones (Parquet o Delta, por ejemplo) no encaja en este diseño. Sería otra implementación de [`Sink`][bdns.sync.sinks.Sink], no un adaptador más.
