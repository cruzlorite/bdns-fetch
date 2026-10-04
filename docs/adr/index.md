# Decisiones de diseño

Cada una de estas páginas recoge **una decisión tal y como se tomó**, junto con el contexto que la justificaba (lo que en inglés se conoce como ADR, *architecture decision record*). A diferencia de las páginas de conceptos, que describen cómo funcionan las cosas hoy, una decisión no se modifica después: si se revierte, se escribe otra que la sustituye y la original se marca como *sustituida*, pero su texto se queda como estaba. Mientras una decisión es una *propuesta*, todavía puede cambiar.

Están todas aquí, numeradas por orden de fecha, y la columna *Ámbito* dice a qué parte del proyecto afecta cada una.

| Nº | Decisión | Ámbito | Estado |
| --- | --- | --- | --- |
| [0001](0001-store-whole-record-version-by-hash.md) | Guardar el registro entero y detectar los cambios por hash | bdns-sync | Aceptada |
| [0002](0002-staging-and-bulk-diff.md) | Staging y comparación en bloque, nunca fila a fila | bdns-sync | Aceptada |
| [0003](0003-run-event-log.md) | `_sync_runs` como registro de eventos, no como columna de estado | bdns-sync | Aceptada |
| [0004](0004-beneficiario-out-of-hash.md) | Sacar `beneficiario` del hash | bdns-sync | Aceptada |
| [0005](0005-per-run-reject-tolerance.md) | Los límites de rechazo se fijan en cada ejecución | bdns-sync | Aceptada |
| [0006](0006-api-parameter-names-keyword-only.md) | Los parámetros se llaman como en la API y se pasan por nombre | bdns-fetch | Aceptada |
| [0007](0007-retry-only-transient-failures.md) | Solo se reintentan los fallos pasajeros | bdns-fetch | Aceptada |
| [0008](0008-spaced-requests-no-bursts.md) | Peticiones espaciadas, sin ráfagas | bdns-fetch | Aceptada |
| [0009](0009-records-as-plain-dicts.md) | Los registros se devuelven como `dict`, sin modelos tipados | bdns-fetch | Aceptada |
| [0010](0010-ordered-bounded-pagination.md) | Paginación en orden y sin acumular memoria | bdns-fetch | Aceptada |
| [0011](0011-cli-generated-from-client.md) | La línea de comandos se genera a partir del cliente | bdns-fetch | Aceptada |
| [0012](0012-api-knowledge-lives-in-fetch.md) | Lo que se sabe de la API vive en bdns-fetch | bdns-fetch | Aceptada |
| [0013](0013-entity-registry.md) | Un único registro de entidades | bdns-sync | Aceptada |
| [0014](0014-cadence-in-the-cli.md) | La periodicidad se decide en la línea de comandos, con código probado | bdns-sync | Aceptada |
| [0015](0015-run-linked-versions-additive-migrations.md) | Cada versión sabe qué ejecución la creó, y el esquema solo crece | bdns-sync | Aceptada |
| [0016](0016-natural-key-conflicts-fail-the-run.md) | Si dos registros comparten clave natural, la ejecución falla | bdns-sync | Aceptada |
| [0017](0017-api-semantics-from-bdns-fetch.md) | Lo que hace falta saber de la API lo aporta bdns-fetch | bdns-sync | Aceptada |
| [0018](0018-one-package.md) | Un solo paquete con varias herramientas | proyecto | Aceptada |
| [0019](0019-one-call-at-a-time.md) | Una llamada cada vez por defecto | bdns-fetch | Aceptada |
| [0020](0020-anonymised-dataset.md) | Un dataset anonimizado y agregado | dataset | Propuesta |
