# Docstring and documentation conventions

These conventions are shared by the BDNS family. The full text, with
worked examples, lives in
[bdns-sync's contributing guide](https://cruzlorite.github.io/bdns-sync/contributing/docstrings/);
this page is the summary that applies here.

## The one rule

**A fact has one home. Code links to it, never copies it.** A measured
fact about the API lives in [API behaviour](../explanation/api-behavior.md);
a decision lives in its [ADR](../adr/index.md); what a function promises
lives in its docstring.

## Docstrings

- Google style: summary line in the imperative mood, ending with a
  period; an optional "why" paragraph of three to six lines; then `Args`,
  `Returns`, `Yields`, `Raises`.
- Do not restate types in prose: the signature carries them.
- Document every parameter, or omit `Args` entirely.
- Every module has a docstring and declares `__all__`, which is its
  contract.
- In a docstring, link a document relative to `docs/reference/api/`
  (`../../explanation/api-behavior.md#upper-bound`) and an object by
  cross-reference (`[`split_range`][bdns.fetch.dates.split_range]`).
  Link anchors, never section numbers.

## Language

Code, comments and docstrings are in English. The site is Spanish-first:
`foo.md` is Spanish and `foo.en.md` its English translation; the API
reference and this page are English in both languages.

## Enforcement

`make check-docs` runs what CI runs: `scripts/check_doc_refs.py` (every
link from code resolves), `scripts/check_docstrings.py` (docstrings agree
with signatures), `mkdocs build --strict`, and
`scripts/check_site_links.py` (no unlinked reference on the built site).
`ruff` enforces the docstring shape with the same configuration as
bdns-sync.
