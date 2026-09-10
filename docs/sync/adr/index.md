# Decisiones de arquitectura

Un ADR registra **una decisión, en el momento en que se tomó**, con el
contexto que la justificaba. A diferencia de las páginas de
[Explicación](../explanation/payload-policy.md), que describen cómo son
las cosas hoy, un ADR no se actualiza: si una decisión se revierte, se
escribe otro ADR que sustituye al anterior y el original se marca como
*sustituido*, pero su texto se queda como estaba.

Eso importa aquí porque casi todas estas decisiones nacen de mediciones
fechadas contra la API de origen. "Medido el 1 de septiembre de 2026" es
un hecho de esa fecha, no una verdad permanente.

| ADR | Decisión | Estado |
| --- | --- | --- |
| [0001](0001-payload-entero-hash.md) | Guardar el registro entero y versionar por hash | Aceptada |
| [0002](0002-staging-diff-en-bloque.md) | Staging más diff en bloque, nunca bucle por fila | Aceptada |
| [0003](0003-log-de-eventos.md) | `_sync_runs` como log de eventos, no columna de estado | Aceptada |
| [0004](0004-beneficiario-fuera-del-hash.md) | Excluir `beneficiario` del hash de contenido | Aceptada |
| [0005](0005-tolerancia-de-rechazo.md) | Tolerancia de rechazo fijada por ejecución | Aceptada |

Las fechas anteriores al 8 de julio de 2026 no constan: el historial del
repositorio arranca ahí con un commit inicial ya consolidado.
