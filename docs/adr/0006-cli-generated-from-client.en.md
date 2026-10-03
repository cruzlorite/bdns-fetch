# 0006. The CLI is generated from the client

**Status:** accepted · **Date:** 2026-10-03

## Context

A CLI built on a library tempts one to put CLI details into the library:
defaults that are Typer objects, exceptions that suggest flags. Then the
client cannot be used, typed or documented without dragging the CLI
along: signatures lie, editors show framework objects, and mkdocstrings
cannot produce a useful reference.

The usual alternative, writing the commands by hand, duplicates every
endpoint and parameter, with its types and defaults, in two lists that
end up diverging.

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
