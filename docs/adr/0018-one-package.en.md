# 0018. One package with several tools

**Status:** accepted · **Date:** 2026-10-04

## Context

The project is made of several tools that depend on one another: `bdns-fetch` talks to the API, `bdns-sync` builds on it to keep the history, and a generator of an anonymised dataset built from `bdns-sync`'s tables is planned ([roadmap](../roadmap.md#dataset)).

They change together. `bdns-sync` is `bdns-fetch`'s main user, and many improvements to one come from what the other needs: an API quirk is found while syncing, solved in the client and used by the sync. If each tool is versioned and released on its own, such a change means releasing one before the other can be tested, temporary dependencies, and a table of which versions work together.

They also share almost everything that is not code: the `ruff` configuration, the scripts that check the documentation, CI and the documentation conventions. Several copies of the same thing drift apart without anyone noticing. And one tool's documentation keeps citing the other's, links that can only be checked when they are on the same site.

Besides, what people programming with these tools actually use are the import paths ([`bdns.fetch`](../fetch/reference/api/index.md), [`bdns.sync`](../sync/reference/api/index.md)) and the commands; how they are split into PyPI packages is a packaging detail. The tools' dependencies differ little, except BigQuery's, which is optional. And the project has a single maintainer, for whom every extra version, CHANGELOG and configuration is repeated work.

## Decision

Every tool lives in one repository and is released in one package, `bdns-tools`, with one version and one CHANGELOG. Each tool is a module ([`bdns.fetch`](../fetch/reference/api/index.md), [`bdns.sync`](../sync/reference/api/index.md)) with its own command and its own section of the site, and heavy optional dependencies go in extras, such as `bdns-tools[bigquery]`.

The package is called `bdns-tools`, not plain `bdns`: BDNS is the official database's name, and a package or site called exactly that would suggest it is the official tool, which is what the IGAE's reuse conditions ask to avoid. The name keeps the word people search for and makes clear these are third-party tools.

Imports hang from `bdns`, a namespace with no `__init__.py` of its own, so each module stands on its own. The boundary between them is kept: [`bdns.fetch`](../fetch/reference/api/index.md) never imports [`bdns.sync`](../sync/reference/api/index.md), and a test checks it.

Numbering continues `bdns-fetch`'s, whose `v1.x` tags already exist, so the first `bdns-tools` release is 2.0.0. Generated data is not kept in the repository: it is published separately, under its own license.

## Consequences

- A change touching several tools is made, tested and released at once, with no temporary dependencies and no compatibility table between versions.
- An incompatible change in any module means a major release for the whole package, even for someone who only needs another module.
- Not every module is equally mature, so the [compatibility policy](../compatibility.md) details what is public in each.
- Someone using only [`bdns.fetch`](../fetch/reference/api/index.md) also installs SQLAlchemy, a few megabytes.
- If one day a module has an audience of its own, it can ship as a separate package without changing a single import, thanks to the namespace.
- Whoever installed `bdns-fetch` or `bdns-sync` has to install `bdns-tools` instead; the releases already published under those names stay on PyPI.
