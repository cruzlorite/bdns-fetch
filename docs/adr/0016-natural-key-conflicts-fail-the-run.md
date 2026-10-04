# 0016. Si dos registros comparten clave natural, la ejecución falla

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Si dos registros de un mismo lote tienen la misma clave natural pero distinto contenido, la comparación SCD2 escribe dos versiones vigentes para una sola clave. A partir de ahí, cada ejecución las cierra y las vuelve a escribir, y da cambios que en la API no existen. No falla nada: el histórico se va llenando de ruido y la ejecución termina bien.

Esto pasa cuando los campos de la clave no identifican de verdad a los registros. Es un riesgo real en `sanciones_busqueda`, cuya clave es una combinación de tres campos que se eligió porque la API no da un identificador.

No hay que confundirlo con las copias idénticas byte a byte que deja la paginación por posición cuando entran registros mientras se recorre un periodo: esas no hacen daño y ya se eliminan al insertar.

## Decisión

Después de cargar el staging, y antes de comparar, se buscan las claves que tengan más de un hash distinto. Si aparece alguna, la ejecución falla con [`NaturalKeyConflict`][bdns.sync.sinks.sql.scd2.NaturalKeyConflict], indicando hasta cinco de esas claves, y no se aplica nada. Las copias idénticas se siguen admitiendo.

## Consecuencias

- Un error al definir una clave se ve el primer día, con las claves que lo provocan, en lugar de ir estropeando el histórico sin que nadie se entere.
- Una ejecución `failed` en `_sync_runs` con el motivo anotado dice exactamente qué hay que corregir: la clave de esa entidad en el registro de entidades.
- Antes de activarlo se comprobó contra la base de datos real que no había ninguna clave repetida en las 23 tablas (unos 45 millones de filas vigentes).
