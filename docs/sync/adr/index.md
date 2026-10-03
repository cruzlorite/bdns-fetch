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
| [0001](0001-store-whole-record-version-by-hash.md) | Guardar el registro entero y versionar por hash | Aceptada |
| [0002](0002-staging-and-bulk-diff.md) | Staging más diff en bloque, nunca bucle por fila | Aceptada |
| [0003](0003-run-event-log.md) | `_sync_runs` como log de eventos, no columna de estado | Aceptada |
| [0004](0004-beneficiario-out-of-hash.md) | Excluir `beneficiario` del hash de contenido | Aceptada |
| [0005](0005-per-run-reject-tolerance.md) | Tolerancia de rechazo fijada por ejecución | Aceptada |
| [0006](0006-entity-registry.md) | Un registro único de entidades | Aceptada |
| [0007](0007-cadence-in-the-cli.md) | La cadencia vive en el CLI, como código probado | Aceptada |
| [0008](0008-run-linked-versions-additive-migrations.md) | Versiones enlazadas a su ejecución; migraciones solo aditivas | Aceptada |
| [0009](0009-natural-key-conflicts-fail-the-run.md) | Un conflicto de clave natural hace fallar la ejecución | Aceptada |
| [0010](0010-api-semantics-from-bdns-fetch.md) | La semántica de la API la aporta bdns-fetch | Aceptada |

Las fechas anteriores al 8 de julio de 2026 no constan: el historial del
repositorio arranca ahí con un commit inicial ya consolidado.
