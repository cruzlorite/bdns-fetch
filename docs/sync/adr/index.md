# Decisiones de diseño

Cada una de estas páginas recoge **una decisión tal y como se tomó**, junto con el contexto que la justificaba (lo que en inglés se conoce como ADR, *architecture decision record*). A diferencia de las páginas de [conceptos](../explanation/payload-policy.md), que describen cómo funcionan las cosas hoy, una decisión no se modifica después: si se revierte, se escribe otra que la sustituye y la original se marca como *sustituida*, pero su texto se queda como estaba.

Esto importa aquí porque casi todas estas decisiones salen de mediciones hechas en una fecha concreta contra la API. Que algo se midiera el 1 de septiembre de 2026 es un hecho de ese día, no una verdad para siempre.

| Nº | Decisión | Estado |
| --- | --- | --- |
| [0001](0001-store-whole-record-version-by-hash.md) | Guardar el registro entero y detectar los cambios por hash | Aceptada |
| [0002](0002-staging-and-bulk-diff.md) | Staging y comparación en bloque, nunca fila a fila | Aceptada |
| [0003](0003-run-event-log.md) | `_sync_runs` como registro de eventos, no como columna de estado | Aceptada |
| [0004](0004-beneficiario-out-of-hash.md) | Sacar `beneficiario` del hash | Aceptada |
| [0005](0005-per-run-reject-tolerance.md) | Los límites de rechazo se fijan en cada ejecución | Aceptada |
| [0006](0006-entity-registry.md) | Un único registro de entidades | Aceptada |
| [0007](0007-cadence-in-the-cli.md) | La periodicidad se decide en la línea de comandos, con código probado | Aceptada |
| [0008](0008-run-linked-versions-additive-migrations.md) | Cada versión sabe qué ejecución la creó, y el esquema solo crece | Aceptada |
| [0009](0009-natural-key-conflicts-fail-the-run.md) | Si dos registros comparten clave natural, la ejecución falla | Aceptada |
| [0010](0010-api-semantics-from-bdns-fetch.md) | Lo que hace falta saber de la API lo aporta bdns-fetch | Aceptada |

Las decisiones anteriores al 8 de julio de 2026 no tienen fecha exacta, porque el historial del repositorio empieza ese día con un primer commit que ya lo incluía todo.
