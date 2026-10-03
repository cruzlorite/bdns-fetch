# 0009. Un conflicto de clave natural hace fallar la ejecución

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Si dos registros de un mismo lote comparten clave natural pero tienen
contenido distinto, el diff SCD2 escribe dos versiones vigentes para una
sola clave. En cada ejecución siguiente las cierra y las vuelve a
escribir, e informa de cambios que en la fuente no existen. Nada falla:
el histórico se llena de ruido y la ejecución termina con éxito.

Pasa cuando los campos clave no identifican de verdad los registros. Es
un riesgo real en `sanciones_busqueda`, cuya clave es una combinación de
tres campos elegida a falta de un identificador.

No hay que confundirlo con las copias idénticas byte a byte, que produce
la paginación por offset cuando entran registros mientras se pagina: son
inofensivas y ya se deduplican al insertar.

## Decisión

Después de cargar el staging y antes del diff, se buscan claves con más
de un hash distinto. Si hay alguna, la ejecución falla con
[`NaturalKeyConflict`][bdns.sync.sinks.sql.scd2.NaturalKeyConflict],
nombrando hasta cinco claves, y no se aplica nada. Las copias idénticas
siguen tolerándose.

## Consecuencias

- Un error en la definición de una clave se ve el primer día, con las
  claves culpables, en vez de degradar el histórico en silencio.
- Una ejecución `failed` en `_sync_runs` con el motivo es información
  accionable: se corrige la clave en el registro de entidades.
- Comprobado contra el destino real antes de activarlo: ninguna clave
  duplicada en las 23 tablas (~45 millones de filas vigentes).
