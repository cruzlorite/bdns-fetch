# Decisiones de diseño

Cada una de estas páginas recoge **una decisión tal y como se tomó**, junto con el contexto que la justificaba (lo que en inglés se conoce como ADR, *architecture decision record*). A diferencia de las páginas de [conceptos](../explanation/policies.md), que describen cómo funcionan las cosas hoy, una decisión no se modifica después: si se revierte, se escribe otra que la sustituye y la original se marca como *sustituida*, pero su texto se queda como estaba.

| Nº | Decisión | Estado |
| --- | --- | --- |
| [0001](0001-api-parameter-names-keyword-only.md) | Los parámetros se llaman como en la API y se pasan por nombre | Aceptada |
| [0002](0002-retry-only-transient-failures.md) | Solo se reintentan los fallos pasajeros | Aceptada |
| [0003](0003-spaced-requests-no-bursts.md) | Peticiones espaciadas, sin ráfagas | Aceptada |
| [0004](0004-records-as-plain-dicts.md) | Los registros se devuelven como `dict`, sin modelos tipados | Aceptada |
| [0005](0005-ordered-bounded-pagination.md) | Paginación en orden y sin acumular memoria | Aceptada |
| [0006](0006-cli-generated-from-client.md) | La línea de comandos se genera a partir del cliente | Aceptada |
| [0007](0007-api-knowledge-lives-in-fetch.md) | Lo que se sabe de la API vive en bdns-fetch | Aceptada |
| [0008](0008-one-call-at-a-time.md) | Una llamada cada vez por defecto | Aceptada |
