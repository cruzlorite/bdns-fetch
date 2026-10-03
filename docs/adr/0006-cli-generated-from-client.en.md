# 0006. The CLI is generated from the client

**Status:** accepted · **Date:** 2026-10-03

## Context

In 1.x the defaults of the client's methods were `typer.OptionInfo`
objects, translated on the fly by a decorator. The client could not be
used, typed or documented without dragging the CLI along: signatures
lied, editors showed Typer objects, and mkdocstrings could not have
produced a useful reference. Exceptions also suggested CLI flags to
library users.

## Decision

The client is plain Python, importing nothing from the CLI. The CLI
builds one command per `fetch_*` method by reading its signature: types,
defaults and which parameters are required come from there. From the
[`options`][bdns.fetch.options] catalog come only the flag name and help
text, one per parameter however many endpoints use it. Hints for the user
are generated in the CLI from the error's fields.

## Consequences

- Adding an endpoint to the client adds the command: there is no second
  list to maintain.
- Client and CLI cannot disagree on a default or a type.
- A test checks that every client parameter has a flag and help.
- What the CLI needs differently from the client is explicit and rare
  ([`CLI_DEFAULTS`][bdns.fetch.options.CLI_DEFAULTS]: one page by default
  instead of all).
