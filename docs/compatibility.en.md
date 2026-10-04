# Compatibility

`bdns-tools` follows [semantic versioning](https://semver.org/): a major release (`3.0.0`) may break; a minor one (`2.1.0`) adds without breaking; a patch (`2.0.1`) only fixes. The version is shared by the whole package, so an incompatible change in any of its modules means a major release. Every change is recorded in the [CHANGELOG](https://github.com/cruzlorite/bdns-tools/blob/main/CHANGELOG.md), with incompatible ones marked.

## What is public in bdns.fetch

What does not change incompatibly without a major release:

- what the module exports in its `__all__`;
- the `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] and [`pages`][bdns.fetch.client.BDNSClient.pages] methods of [`BDNSClient`][bdns.fetch.client.BDNSClient], and its constructor arguments;
- the attributes of [`BDNSError`][bdns.fetch.exceptions.BDNSError] and [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
- the [`dates`][bdns.fetch.dates] and [`contract`][bdns.fetch.contract] modules;
- on the CLI: command names and their options, exit codes, and the output format (JSON Lines, or the document's bytes).

Everything else may change in any release: underscore names; the [`cli`][bdns.fetch.cli], [`options`][bdns.fetch.options], [`endpoints`][bdns.fetch.endpoints] and [`utils`][bdns.fetch.utils] modules (except [`RateLimiter`][bdns.fetch.utils.RateLimiter]); message texts and logs.

**Records** are the API's own ([ADR 0004](fetch/adr/0004-records-as-plain-dicts.md)), so a field the API changes arrives changed without a new `bdns-tools` release in between.

## What is public in bdns.sync

- **The CLI**: the commands (`sync`, `delta`, `backfill`, `list`, `check-api`), their options and environment variables, and exit codes.
- **The target schema**: the columns of the entity tables and of the `_sync_*` tables described in the [data model](sync/reference/data-model.md).
- **The Python API**: what each module declares in its `__all__`; in particular [`ENTITIES`][bdns.sync.entities.ENTITIES], [`sync_entity`][bdns.sync.entities.sync_entity], the [`Sink`][bdns.sync.sinks.Sink] interface and [`SyncStats`][bdns.sync.sinks.SyncStats].

Underscore names, messages and logs may change in any release.

<a id="schema"></a>
### The schema only grows

The target schema changes only by **adding nullable columns**, and each run adds on its own the columns a target created by an earlier version lacks ([ADR 0008](sync/adr/0008-run-linked-versions-additive-migrations.md)). No column is ever renamed, retyped or dropped: upgrading `bdns-tools` needs no manual migration. A non-additive change would be a major release with migration instructions.

Changing an entity's natural key or hash rules does not change the schema, but it does change the hashes: the next run re-versions the affected rows. Such changes are announced in the CHANGELOG.

## Python versions

The Python versions CI tests are supported (today, 3.11 to 3.14). Dropping one, only once it reaches end of life, is announced in the CHANGELOG.

<a id="previous-names"></a>
## Previous names

Up to `bdns-fetch` 1.3.0 and `bdns-sync` 0.5.0, the two tools were published on PyPI as separate packages. They now come together in `bdns-tools`, with the same modules ([`bdns.fetch`](fetch/reference/api/index.md) and [`bdns.sync`](sync/reference/api/index.md)) and the same commands (`bdns-fetch` and `bdns-sync`), so upgrading only means installing `bdns-tools` instead of the previous packages. Numbering continues `bdns-fetch`'s, so the first `bdns-tools` release is 2.0.0.

## How releases happen

A `vX.Y.Z` tag on the main branch releases that version, provided it matches the version in `pyproject.toml`, the CHANGELOG has its section and the tests pass, both on the code and on the built package. PyPI goes first. Only if that succeeds are the image pushed to `ghcr.io`, the GitHub release created, with the CHANGELOG notes and the same files PyPI received, and this site updated. There is no other way to publish.

Tags of earlier releases are kept: `bdns-fetch`'s up to 1.3.0 are called `v1.3.0`, and `bdns-sync`'s up to 0.5.0, `bdns-sync-v0.5.0`.
