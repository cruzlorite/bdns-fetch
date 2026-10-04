# 0012. Knowledge of the API lives in bdns-fetch

**Status:** accepted · **Date:** 2026-10-03

## Context

The family has two projects: `bdns-fetch` talks to the API and
`bdns-sync` stores what it returns. What is known about the API's real
behaviour (the opposite semantics of `fechaRegFin` and `fechaHasta`,
failures on long ranges, burst rejection, per-endpoint retention,
spurious changes) is useful to anyone using it, not only to whoever
stores it.

If that knowledge lives in the storage layer, users of the client alone
hit all of it without warning, and the storage layer ends up
compensating for the client's limitations instead of fixing them where
they belong.

## Decision

What is about the API lives in `bdns-fetch`:

- the documentation of its [behaviour](../fetch/explanation/api-behavior.md);
- [`dates`][bdns.fetch.dates], which turns an inclusive range into each
  date family's arguments and splits long ranges;
- [`contract`][bdns.fetch.contract] and `bdns-fetch check-api`, which
  check those semantics against the live service.

`bdns-sync` uses them and documents only what it decides on top of them.

## Consequences

- Any `bdns-fetch` user downloads correctly by date without knowing the
  history.
- A fact about the API has one home; `bdns-sync`'s documentation links
  here.
- Changing those semantics is a `bdns-fetch` change, which `bdns-sync`
  picks up when it upgrades.
