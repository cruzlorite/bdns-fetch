# 0002. Staging más diff en bloque, nunca bucle por fila

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al historial registrado)

## Contexto

Aplicar SCD2 a un lote necesita cuatro operaciones: insertar claves
nuevas, cerrar versiones cuyo hash cambió, refrescar las que no cambiaron
y cerrar las ausentes.

La forma directa es un bucle: por cada registro, consultar su versión
vigente y decidir. `concesiones_busqueda` pasa de 20 millones de filas.

En BigQuery cada sentencia DML paga latencia y coste por sentencia,
independientemente de cuántas filas toque. Un bucle de miles de UPDATE de
una fila no escala ahí de ninguna manera.

## Decisión

Cargar el lote en una tabla de staging y aplicar el diff con un **número
fijo de sentencias en bloque**, sea el lote de 20 filas o de 2 millones.

Solo SQL portable: subconsultas `EXISTS`/`NOT EXISTS` correlacionadas, sin
`UPDATE...FROM` ni `MERGE` específicos de motor. El mismo camino de código
corre sin cambios en SQLite, PostgreSQL y BigQuery.

## Consecuencias

- El coste en sentencias es constante respecto al tamaño del lote.
- Los contadores hay que calcularlos **antes** de escribir: cada
  sentencia cambia lo que la siguiente habría contado.
- Hace falta una tabla de staging por endpoint, que se vacía al principio
  y al final de cada ejecución.
- Las diferencias entre motores se concentran en adaptadores
  (`sinks.sql.dialects`); nada fuera de ahí ramifica por nombre de
  dialecto.
- Un destino sin conexión ni UPDATE ni transacción (Parquet, Delta) no
  encaja en este diseño. Sería otra implementación de `Sink`, no un
  adaptador.
