# Design decisions

An ADR (*architecture decision record*) records **one decision, at the time it was made**, with the context that justified it. Unlike the explanation pages, which describe how things are today, an ADR is never updated: if a decision is reversed, a new one supersedes it and the original is marked *superseded*, but its text stays as it was. While a decision is *proposed*, it may still change.

They are all here, numbered by date, and the *Scope* column says which part of the project each one affects.

| No. | Decision | Scope | Status |
| --- | --- | --- | --- |
| [0001](0001-store-whole-record-version-by-hash.md) | Store the whole record and version by hash | bdns-sync | Accepted |
| [0002](0002-staging-and-bulk-diff.md) | Staging plus bulk diff, never a per-row loop | bdns-sync | Accepted |
| [0003](0003-run-event-log.md) | `_sync_runs` as an event log, not a status column | bdns-sync | Accepted |
| [0004](0004-beneficiario-out-of-hash.md) | Exclude `beneficiario` from the content hash | bdns-sync | Accepted |
| [0005](0005-per-run-reject-tolerance.md) | Reject tolerance set per run | bdns-sync | Accepted |
| [0006](0006-api-parameter-names-keyword-only.md) | Parameters named as the API names them, keyword-only | bdns-fetch | Accepted |
| [0007](0007-retry-only-transient-failures.md) | Retry transient failures only | bdns-fetch | Accepted |
| [0008](0008-spaced-requests-no-bursts.md) | Spaced requests, no bursts | bdns-fetch | Accepted |
| [0009](0009-records-as-plain-dicts.md) | Records as `dict`, no typed models | bdns-fetch | Accepted |
| [0010](0010-ordered-bounded-pagination.md) | Concurrent pagination, in order, with bounded memory | bdns-fetch | Accepted |
| [0011](0011-cli-generated-from-client.md) | The CLI is generated from the client | bdns-fetch | Accepted |
| [0012](0012-api-knowledge-lives-in-fetch.md) | Knowledge of the API lives in bdns-fetch | bdns-fetch | Accepted |
| [0013](0013-entity-registry.md) | A single entity registry | bdns-sync | Accepted |
| [0014](0014-cadence-in-the-cli.md) | The cadence lives in the CLI, as tested code | bdns-sync | Accepted |
| [0015](0015-run-linked-versions-additive-migrations.md) | Versions linked to their run, and additive-only migrations | bdns-sync | Accepted |
| [0016](0016-natural-key-conflicts-fail-the-run.md) | A natural-key conflict fails the run | bdns-sync | Accepted |
| [0017](0017-api-semantics-from-bdns-fetch.md) | bdns-fetch provides the API's semantics | bdns-sync | Accepted |
| [0018](0018-one-package.md) | One package with several tools | project | Accepted |
| [0019](0019-one-call-at-a-time.md) | One call at a time by default | bdns-fetch | Accepted |
| [0020](0020-anonymised-dataset.md) | An anonymised, aggregated dataset | dataset | Proposed |
