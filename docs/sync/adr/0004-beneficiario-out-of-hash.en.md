# 0004. Exclude `beneficiario` from the content hash

**Status:** accepted · **Date:** 2026-09-03, narrowed on 2026-09-04

## Context

The payload hash decides whether a new version opens. If the source
rewrites a field without the data changing, every run opens a version
that corresponds to nothing that happened.

Measured against the live service:

- In `concesiones_busqueda`, of the keys whose name changed more than
  once, **67% return to a spelling they already had** (`ASOCIACIÓN` →
  `ASOCIACION` → `ASOCIACIÓN`), with `idPersona` unchanged. Hashing it
  re-versioned **58% of the table**.
- In `grandesbeneficiarios_busqueda`, worse: six variants for one
  `idPersona` in eleven days, with the amount identical.

## Decision

`beneficiario` leaves the hash for those two entities. **It is still
stored whole**; it simply stops counting as a change.

Identity is untouched: it is still `idPersona`.

The exclusion is declared per entity, only where the oscillation was
measured (narrowed on 2026-09-04). It is not a general rule about the
field.

## Consequences

- A difference known to be noise stops being reported. None is ever
  invented.
- The hash becomes **coarser** than what is stored: two different
  payloads may share a hash. That is safe; the opposite direction would
  not be. The full argument is in
  [what is stored, and what counts as a change](../explanation/payload-policy.md).
- If the rule turned out to be wrong, the cost is recoverable: the data
  is still stored, the rule changes, and versioning resumes from the next
  run. What is lost is history granularity over that period, not data.
- A genuine name change for the same `idPersona` opens no version. That
  is the accepted price.
