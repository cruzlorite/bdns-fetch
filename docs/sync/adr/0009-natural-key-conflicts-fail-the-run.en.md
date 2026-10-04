# 0009. A natural-key conflict fails the run

**Status:** accepted · **Date:** 2026-10-03

## Context

If two records in one batch share a natural key but differ in content,
the SCD2 diff writes two current versions for a single key. Every
following run closes and rewrites them, reporting changes the source
never made. Nothing fails: the history fills with noise and the run
finishes successfully.

It happens when the key fields do not really identify the records. It is
a real risk on `sanciones_busqueda`, whose key is a combination of three
fields chosen for lack of an identifier.

It must not be confused with byte-identical copies, which offset
pagination produces when records arrive while a range is being paged
through: those are harmless and already deduplicated on insert.

## Decision

After staging is loaded and before the diff, keys with more than one
distinct hash are looked for. If there is any, the run fails with
[`NaturalKeyConflict`][bdns.sync.sinks.sql.scd2.NaturalKeyConflict],
naming up to five keys, and nothing is applied. Identical copies are
still tolerated.

## Consequences

- A mistake in a key definition shows on the first day, with the
  offending keys, instead of degrading the history silently.
- A `failed` run in `_sync_runs` with the reason is actionable: the key
  is fixed in the entity registry.
- Checked against the real target before enabling it: no duplicate keys
  across the 23 tables (~45 million current rows).
