# 0017. bdns-fetch provides the API's semantics

**Status:** accepted · **Date:** 2026-10-03

## Context

Syncing by date depends on facts measured on the API: that `fechaRegFin`
is exclusive and `fechaHasta` inclusive, that long ranges fail, that the
API rejects bursts, that all of this must be checked every day for
change. These are facts about the API, not about storage: anyone using
it needs them.

If the storage layer implements them on its own, the API client goes
without them, and the storage layer compensates for its limitations
(spacing requests on top of the client, patching its progress bar,
forcing it to fetch every page) instead of fixing them where they belong.

## Decision

`bdns-sync` uses what `bdns-fetch` provides: what it
[documents](../fetch/explanation/api-behavior.md#upper-bound) about each date family's last day, splitting with [`split_range`][bdns.fetch.dates.split_range],
the contract check with [`check_api_contract`][bdns.fetch.contract.check_api_contract], and request spacing in the
client. It is the other half of
[ADR 0012](0012-api-knowledge-lives-in-fetch.md), which covers the same ground from `bdns-fetch`.

## Consequences

- The API measurements have one home, in `bdns-fetch`'s documentation;
  `bdns-sync`'s links there and explains only its own decisions.
- `bdns-sync` depends on what `bdns-fetch` declares public, not on its
  internals. Since both ship in the same package
  ([ADR 0018](0018-one-package.md)), a change in one
  that breaks the other shows up in the tests of the same pull request.
