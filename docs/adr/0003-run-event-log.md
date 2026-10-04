# 0003. `_sync_runs` como registro de eventos, no como columna de estado

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al primer commit del repositorio)

## Contexto

Hay que poder saber, mirando la base de datos, si una ejecución terminó bien.

Lo habitual es tener una fila por ejecución con una columna `status` que pasa de `running` a `success` o a `failed`.

Pero así no se puede registrar el caso que más importa: **un proceso que se muere a mitad**. Un proceso muerto no puede actualizar su propia fila, así que la ejecución se queda en `running` para siempre y no se distingue de una que sigue en marcha.

## Decisión

`_sync_runs` es un registro de **eventos** que solo crece, y ninguna fila se modifica una vez escrita:

- al empezar se anota un evento `started`, que se confirma en el momento y **fuera de la transacción de los datos**;
- al terminar se anota un evento `success` o `failed`.

El estado de una ejecución es su último evento, y un `started` sin evento final significa que el proceso se murió a mitad.

Los eventos se escriben en transacciones cortas propias. Si fueran dentro de la transacción de los datos correrían su misma suerte: en una base de datos con transacciones, una ejecución fallida desharía también sus propios eventos y desaparecerían del registro todas las ejecuciones fallidas.

## Consecuencias

- El registro siempre dice la verdad, incluso cuando los cambios en los datos se han deshecho.
- Cada ejecución deja dos filas en lugar de una.
- En teoría puede pasar que los datos se confirmen y el evento `success` no llegue a escribirse. Se asume ese riesgo porque las tablas `_sync_*` son solo informativas y la sincronización nunca las lee.
- La regla es la misma con cualquier base de datos: **si no hay evento `success`, se vuelve a lanzar.**
