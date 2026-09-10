# 0002. Staging plus bulk diff, never a per-row loop

**Status:** accepted · **Date:** 2026-07-08 (predates the recorded history)

## Context

Applying SCD2 to a batch needs four operations: insert new keys, close
versions whose hash changed, refresh the unchanged ones, and close the
missing ones.

The direct way is a loop: for each record, look up its current version
and decide. `concesiones_busqueda` is over 20 million rows.

On BigQuery every DML statement pays per-statement latency and cost,
however many rows it touches. A loop of thousands of single-row UPDATEs
does not scale there at all.

## Decision

Load the batch into a staging table and apply the diff with a **fixed
number of bulk statements**, whether the batch is 20 rows or 2 million.

Portable SQL only: correlated `EXISTS`/`NOT EXISTS` subqueries, no
engine-specific `UPDATE...FROM` or `MERGE`. The same code path runs
unchanged on SQLite, PostgreSQL and BigQuery.

## Consequences

- The cost in statements is constant with respect to batch size.
- The counters have to be computed **before** writing: each statement
  changes what the next one would have counted.
- Each endpoint needs a staging table, emptied at the start and end of
  every run.
- Engine differences are confined to adapters (`sinks.sql.dialects`);
  nothing outside them branches on dialect name.
- A target with no connection, no UPDATE and no transaction (Parquet,
  Delta) does not fit this design. It would be another `Sink`
  implementation, not an adapter.
