# 0007. Knowledge of the API lives in bdns-fetch

**Status:** accepted · **Date:** 2026-10-03

## Context

Nearly everything known about the API's real behaviour (the opposite
semantics of `fechaRegFin` and `fechaHasta`, failures on long ranges,
burst rejection, per-endpoint retention, spurious changes) was measured
while building `bdns-sync`, and lived there: in its documentation, in its
`api_contract.py` and in its date helpers.

But these are facts about the API, not about storage. Users of
`bdns-fetch` alone hit them without warning, and `bdns-sync` compensated
for client defects (request spacing) instead of fixing them where they
belonged.

## Decision

What is about the API lives in `bdns-fetch`:

- the documentation of its [behaviour](../explanation/api-behavior.md);
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
