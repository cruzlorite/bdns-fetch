# 0008. Versions linked to their run, and additive-only migrations

**Status:** accepted · **Date:** 2026-10-03

## Context

Whoever queries an SCD2 history asks questions the schema must answer
without guessing:

- What changed in yesterday's run? With only `_valid_from` it is
  approximated by date, and two runs on the same day blur together.
- Was this record withdrawn, or did it change? A version closed by a
  change and one closed because the record disappeared look the same; the
  difference can only be inferred by looking for a later version.
- Which range did each windowed run cover? Without the range in the run
  log, there is no auditing whether a slice of history is missing.

Adding columns to targets already in production, some with tens of
millions of rows in BigQuery, requires a migration. A full migration tool
(versions, up and down scripts) is a lot for a schema that rarely
changes, and renaming or retyping columns in BigQuery is costly and
risky.

## Decision

Every version records the run that created it (`_created_run_id`) and,
once closed, the run that closed it and why (`_closed_run_id`,
`_closed_reason`: `superseded` when a different payload replaces it,
`removed` when the source stopped serving the key). `_sync_runs` also
records changed and unchanged keys (`rows_changed`, `rows_unchanged`) and
a windowed run's range (`window_start`, `window_end`).

The schema **only grows, and only with nullable columns**. At the start
of each run,
[`add_missing_columns`][bdns.sync.sinks.sql.migrate.add_missing_columns]
adds to existing tables the columns they lack. No column is ever renamed,
retyped or dropped.

## Consequences

- "What changed in run X" and "what was withdrawn" are direct queries.
- A target written by an earlier version upgrades itself; earlier rows
  have `NULL` in the new columns.
- A non-additive schema change does not fit this mechanism: if one is
  ever needed, it will be a major release with migration instructions.
