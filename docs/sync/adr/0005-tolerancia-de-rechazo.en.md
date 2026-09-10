# 0005. Reject tolerance set per run

**Status:** accepted · **Date:** 2026-09-06

## Context

Some records arrive malformed: the backend sometimes returns an HTML
error page instead of JSON for one specific record. A record with no
usable natural key cannot be versioned.

Dropping the odd one is right: they are a documented, permanent trait of
the source, and losing a multi-hour backfill to one of them helps nobody.

Dropping most of a batch is not the same event. It means the shape of
what the source returns changed, and applying what survived is actively
destructive: staging ends up nearly empty, and to a full reconciliation —
or to window-scoped deletion detection — an empty batch is
indistinguishable from "everything here was withdrawn".

## Decision

A run refuses the whole batch when the rejects cross a limit. Three
parameters, all three set **per run**, not per entity:

- `max_ratio`, the share of the batch that may be unusable (10% by
  default).
- `max_count`, an absolute cap. It catches a shape change in a batch
  large enough to hide it under the ratio: 200,000 bad records out of 20
  million is 1%, below any sane ratio, and still means something broke.
- `min_to_enforce_ratio`, below this many rejects the ratio does not
  apply. A narrow window can hold three records, where one bad one is
  already a third of the batch.

They are **operational tolerances, not statements about the data**. That
is why, unlike the payload policy, they carry no per-entity values.

## Consequences

- A refused batch leaves the run `failed`, with the reason recorded, and
  the data untouched.
- The dropped records go to `_sync_errors` with their context.
- Whoever orchestrates can raise the limit for a source having a bad day,
  or lower it to be told sooner.
