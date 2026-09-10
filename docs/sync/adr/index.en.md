# Architecture decisions

An ADR records **one decision, at the moment it was made**, with the
context that justified it. Unlike the
[Explanation](../explanation/payload-policy.md) pages, which describe how
things are today, an ADR is never updated: if a decision is reversed, a
new ADR supersedes it and the original is marked *superseded*, but its
text stays as it was.

That matters here because almost every one of these decisions comes from
dated measurements against the source API. "Measured on 1 September
2026" is a fact about that date, not a permanent truth.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-payload-entero-hash.md) | Store the whole record and version by hash | Accepted |
| [0002](0002-staging-diff-en-bloque.md) | Staging plus bulk diff, never a per-row loop | Accepted |
| [0003](0003-log-de-eventos.md) | `_sync_runs` as an event log, not a status column | Accepted |
| [0004](0004-beneficiario-fuera-del-hash.md) | Exclude `beneficiario` from the content hash | Accepted |
| [0005](0005-tolerancia-de-rechazo.md) | Reject tolerance set per run | Accepted |

Dates before 8 July 2026 are not on record: the repository history starts
there, with an already-consolidated initial commit.
