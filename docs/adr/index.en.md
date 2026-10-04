# Architecture decisions

An ADR records **one decision, at the time it was made**, with the context
that justified it. Unlike the [Explanation](../explanation/policies.md)
pages, which describe how things are today, an ADR is never updated: if a
decision is reversed, a new ADR supersedes it and the original is marked
*superseded*, but its text stays as it was.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-api-parameter-names-keyword-only.md) | Parameters named as the API names them, keyword-only | Accepted |
| [0002](0002-retry-only-transient-failures.md) | Retry transient failures only | Accepted |
| [0003](0003-spaced-requests-no-bursts.md) | Spaced requests, no bursts | Accepted |
| [0004](0004-records-as-plain-dicts.md) | Records as `dict`, no typed models | Accepted |
| [0005](0005-ordered-bounded-pagination.md) | Concurrent pagination, in order, with bounded memory | Accepted |
| [0006](0006-cli-generated-from-client.md) | The CLI is generated from the client | Accepted |
| [0007](0007-api-knowledge-lives-in-fetch.md) | Knowledge of the API lives in bdns-fetch | Accepted |
| [0008](0008-one-call-at-a-time.md) | One call at a time by default | Accepted |
