# Decisiones de arquitectura

Un ADR registra **una decisión, en el momento en que se tomó**, con el
contexto que la justificaba. A diferencia de las páginas de
[Explicación](../explanation/policies.md), que describen cómo son las
cosas hoy, un ADR no se actualiza: si una decisión se revierte, se escribe
otro que la sustituye y el original se marca como *sustituido*, pero su
texto se queda como estaba.

| ADR | Decisión | Estado |
| --- | --- | --- |
| [0001](0001-api-parameter-names-keyword-only.md) | Parámetros con el nombre de la API, solo por nombre | Aceptada |
| [0002](0002-retry-only-transient-failures.md) | Reintentar solo los fallos transitorios | Aceptada |
| [0003](0003-spaced-requests-no-bursts.md) | Peticiones espaciadas, sin ráfagas | Aceptada |
| [0004](0004-records-as-plain-dicts.md) | Registros como `dict`, sin modelos tipados | Aceptada |
| [0005](0005-ordered-bounded-pagination.md) | Paginación concurrente, en orden y con memoria acotada | Aceptada |
| [0006](0006-cli-generated-from-client.md) | El CLI se genera a partir del cliente | Aceptada |
| [0007](0007-api-knowledge-lives-in-fetch.md) | El conocimiento de la API vive en bdns-fetch | Aceptada |
