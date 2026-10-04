# 0006. Parameters named as the API names them, keyword-only

**Status:** accepted · **Date:** 2026-10-03

## Context

Each endpoint takes between zero and twenty-five parameters, named in
Spanish camelCase (`fechaRegInicio`, `tipoAdministracion`). If they can be
passed by position, nobody remembers the order of twenty parameters: an
argument in the wrong place sends a different filter with no error at
all.

Translating the names to `snake_case` or English would make the code more
"Pythonic", but would break the one-to-one match with the official
documentation, the only reference for what each parameter does.

## Decision

The parameters of the `fetch_*` methods carry **exactly the name the API
gives them** and are **keyword-only**. Required ones have no default. The
CLI follows the same rule: `--fechaDesde`, not `--fecha-desde`.

## Consequences

- The official documentation applies as is, to the client and the CLI.
- A call reads on its own: `fetch_organos(idAdmon="C")`.
- Adding or reordering parameters never breaks anyone.
- The names do not follow PEP 8. That is deliberate, and `ruff` does not
  flag it because the naming rule is not enabled.
