# 0004. Records as `dict`, no typed models

**Status:** accepted · **Date:** 2026-10-03

## Context

A "modern" client usually returns typed models (dataclasses, Pydantic):
autocompletion, validation, documentation for each field.

The BDNS API changes shape without notice: fields that appear, that
arrive `null` when they are normally filled, or that change format
([API behaviour](../explanation/api-behavior.md#intermittent-fields)). A
strict model would break downloads as soon as the API changed; a lax one
would add nothing. And the main consumer, `bdns-sync`, stores the whole
record precisely so as to lose nothing that arrives.

## Decision

Methods return records as `dict`, **exactly** as the API returns them:
no renaming, no type conversion, no dropped fields.

## Consequences

- A new field reaches the consumer without waiting for a `bdns-fetch`
  release.
- Nothing is lost or transformed on the way: what is stored is what the
  administration published.
- No field autocompletion or validation. Whoever needs it adds it in
  their own layer, where they know which fields matter to them.
