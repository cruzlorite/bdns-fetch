# Compatibility

`bdns-sync` follows [semantic versioning](https://semver.org/). While it
is at `0.x`, a minor release (`0.7.0`) may break and a patch (`0.6.1`)
only fixes; from `1.0.0` on, only a major release may break. Every change
is recorded in the
[CHANGELOG](https://github.com/cruzlorite/bdns-sync/blob/main/CHANGELOG.md),
with incompatible ones marked.

## What the public API is

- **The CLI**: the commands (`sync`, `delta`, `backfill`, `list`,
  `check-api`), their options and environment variables, and exit codes.
- **The target schema**: the columns of the entity tables and of the
  `_sync_*` tables described in the [data model](reference/data-model.md).
- **The Python API**: what each module declares in its `__all__`; in
  particular [`ENTITIES`][bdns.sync.entities.ENTITIES],
  [`sync_entity`][bdns.sync.entities.sync_entity], the
  [`Sink`][bdns.sync.sinks.Sink] interface and
  [`SyncStats`][bdns.sync.sinks.SyncStats].

Underscore names, messages and logs may change in any release.

## The schema only grows

The target schema changes only by **adding nullable columns**, and each
run adds on its own the columns a target created by an earlier version
lacks ([ADR 0008](adr/0008-run-linked-versions-additive-migrations.md)).
No column is ever renamed, retyped or dropped: upgrading `bdns-sync`
needs no manual migration. A non-additive change would be a major release
with migration instructions.

Changing an entity's natural key or hash rules does not change the
schema, but it does change the hashes: the next run re-versions the
affected rows. Such changes are announced in the CHANGELOG.

## Python versions

The Python versions CI tests are supported (today, 3.11 to 3.14).
Dropping one, only once it reaches end of life, is announced in the
CHANGELOG.

## With bdns-fetch

`bdns-sync` declares the `bdns-fetch` range it accepts. Its CI tests
against that version and, in a separate job, against `bdns-fetch`'s main
branch, to catch a break before it is released.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## How releases happen

A `vX.Y.Z` tag on the main branch publishes to PyPI and the image to
`ghcr.io`, provided it matches the version in `pyproject.toml`. There is
no other way to publish.
