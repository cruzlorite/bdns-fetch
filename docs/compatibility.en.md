# Compatibility

`bdns-fetch` follows [semantic versioning](https://semver.org/): a major
release (`3.0.0`) may break; a minor one (`2.1.0`) adds without breaking;
a patch (`2.0.1`) only fixes. Every change is recorded in the
[CHANGELOG](https://github.com/cruzlorite/bdns-fetch/blob/main/CHANGELOG.md).

## What the public API is

What does not change incompatibly without a major release:

- what the package exports in its `__all__`;
- the `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] and [`pages`][bdns.fetch.client.BDNSClient.pages] methods of
  [`BDNSClient`][bdns.fetch.client.BDNSClient], and its constructor
  arguments;
- the attributes of [`BDNSError`][bdns.fetch.exceptions.BDNSError] and
  [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
- the [`dates`][bdns.fetch.dates] and [`contract`][bdns.fetch.contract]
  modules;
- on the CLI: command names and their options, exit codes, and the output
  format (JSON Lines, or the document's bytes).

Everything else (underscore names, the [`cli`][bdns.fetch.cli],
[`options`][bdns.fetch.options], [`endpoints`][bdns.fetch.endpoints] and
[`utils`][bdns.fetch.utils] modules except [`RateLimiter`][bdns.fetch.utils.RateLimiter], message texts
and logs) may change in any release.

**Records** are the API's, as is ([ADR 0004](adr/0004-records-as-plain-dicts.md)):
if the API changes a field, it changes without any `bdns-fetch` release
involved.

## Python versions

The Python versions CI tests are supported (today, 3.11 to 3.14). Dropping
one, only once it reaches end of life, is a minor change announced in the
CHANGELOG.

## With bdns-sync

`bdns-sync` declares the `bdns-fetch` range it accepts, and its CI also
tests against `bdns-fetch`'s main branch, to catch a break before it is
released.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## How releases happen

A `vX.Y.Z` tag on the main branch releases that version, provided it
matches the version in `pyproject.toml`, the CHANGELOG has its section
and the tests pass. PyPI goes first. Only if that succeeds is the GitHub
release created, with the CHANGELOG notes and the same files PyPI
received, and this site updated. There is no other way to publish.
