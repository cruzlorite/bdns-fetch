# 0003. `_sync_runs` como log de eventos, no columna de estado

**Estado:** aceptada · **Fecha:** 2026-07-08 (anterior al historial registrado)

## Contexto

Hace falta saber, mirando el destino, si una ejecución terminó bien.

Lo habitual es una fila por ejecución con una columna `status` que pasa de
`running` a `success` o `failed`.

Eso no puede registrar el caso que más importa: **un proceso que muere a
mitad**. Un proceso muerto no actualiza su propia fila, así que la
ejecución se queda en `running` para siempre, indistinguible de una que
sigue corriendo.

## Decisión

`_sync_runs` es un log de **eventos** que solo crece. Nunca se actualiza
una fila ya escrita.

- Un evento `started` al arrancar, confirmado de inmediato y **fuera de la
  transacción de los datos**.
- Un evento final `success` o `failed` al terminar.

El estado de una ejecución es su último evento. Un `started` sin evento
final significa que el proceso murió a mitad.

Los eventos van en transacciones cortas propias. Dentro de la transacción
de datos heredarían su suerte: en un motor transaccional, una ejecución
fallida haría rollback de sus propios eventos y borraría del log todas las
ejecuciones fallidas.

## Consecuencias

- El log siempre dice la verdad, incluso cuando los datos hicieron
  rollback.
- Dos filas por ejecución en lugar de una.
- Queda una ventana teórica en la que los datos se confirman y el evento
  `success` no llega a escribirse. Se asume: las tablas `_sync_*` son
  informativas y la lógica de sincronización nunca las lee.
- La regla de operación es la misma en todos los motores: **si no hay
  evento `success`, se vuelve a lanzar.**
