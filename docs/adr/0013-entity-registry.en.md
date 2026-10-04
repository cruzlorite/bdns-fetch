# 0013. A single entity registry

**Status:** accepted · **Date:** 2026-10-03

## Context

There are 22 entities. For each one the same things must be known: how
its rows are fetched, which fields form the natural key, whether each run
covers the whole entity or a date window, which payload rules apply, and
how far back its history is worth loading.

If that knowledge is spread out (one function per entity, one dictionary
of policies, another of full entities, another of windowed ones, lists
written by hand in the scripts and the documentation), every new entity
must be added in five places, and a typo in one of them does not fail: a
misspelt policy name is silently ignored and the entity starts
versioning noise.

## Decision

Each entity is declared **once**, as an
[`Entity`][bdns.sync.entities.Entity] in
[`ENTITIES`][bdns.sync.entities.ENTITIES]: name, kind (`full` or
`windowed`), natural key, row source, registration-date field, policy and
history start. Row sources are few and reusable (catalog, parameter
sweep, registration-date window, period window, discover then detail).

Everything else reads that registry:
[`sync_entity`][bdns.sync.entities.sync_entity], the `delta` and
`backfill` plans, `bdns-sync list`, `--dry-run` and the tests.

## Consequences

- A new entity is one entry in a table.
- There are no lists that can diverge: the policy `--dry-run` prints is
  the one the run applies, and the entities `delta` syncs are the ones
  `list` shows.
- The measurements justifying each rule sit next to the entry they apply
  to.
- An entity with genuinely its own logic is still possible: its row
  source is one more function.
