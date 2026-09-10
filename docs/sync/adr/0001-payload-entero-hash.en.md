# 0001. Store the whole record and version by hash

**Status:** accepted · **Date:** 2026-07-08 (predates the recorded history)

## Context

The BDNS API exposes twenty-odd entities with different shapes, and their
fields change without notice. A schema with one column per field would
need a migration every time the source adds or drops something, and
twenty-odd schemas maintained by hand.

Changes also have to be detected between runs without comparing field by
field, which does not scale to tens of millions of rows.

## Decision

One table per endpoint, all sharing **the same generic schema**. The
record is stored whole in a `payload` column, as JSON in text. Every other
column is SCD2 versioning metadata.

Changes are detected through `_row_hash`, a SHA-256 of the canonicalized
payload.

## Consequences

- A new or vanished field needs no migration: the hash picks it up and it
  is versioned like any other change.
- Closed versions are never deleted. History only grows.
- The payload cannot be queried with native SQL JSON functions on every
  engine, because it is stored as text for portability. This code never
  queries it in SQL, only reads it back as a dict in Python.
- Canonicalization has to be stable, or the hash reports changes that do
  not exist. That is where [0004](0004-beneficiario-fuera-del-hash.md)
  and the payload policy rules come from.
