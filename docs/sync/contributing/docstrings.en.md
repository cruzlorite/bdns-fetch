# Docstring and documentation conventions

Docstrings in this project are read twice: in the editor, by whoever is
changing the code, and on the documentation site, where `mkdocstrings`
renders them as the API reference. One text has to serve both. That is
the constraint this convention exists to satisfy.

## The one rule

**A fact has one home. Code links to it, never copies it.**

| The thing you want to write down | Where it lives |
| --- | --- |
| What a function does, and what it promises the caller | Its docstring |
| A design decision spanning several functions | The module docstring |
| A measured fact about the BDNS API | bdns-fetch's [API behaviour](https://cruzlorite.github.io/bdns-fetch/en/explanation/api-behavior/) |
| What this engine decides because of it | [How it syncs](../explanation/sync-behavior.md) |
| A warning for whoever consumes the resulting tables | [Before querying the data](../explanation/data-caveats.md) |
| How to run, deploy, or schedule the tool | The guides |

Duplication is not a style problem here, it is a correctness problem:
two copies of a measurement diverge, and nothing tells you which one is
stale.

## Function and method docstrings

Sections in this order, always:

1. **Summary line.** Imperative mood, one line, ends with a period.
2. **Why paragraph** (optional). Three to six lines. See the three-way
   test below for what belongs here.
3. **`Args` / `Returns` / `Yields` / `Raises`**, Google style.

Rules:

- Imperative mood: "Group `items` into lists", not "Groups items" and
  not "This function groups items".
- Do not restate types in prose. The type hints carry them, and
  `mkdocstrings` renders the signature above the text.
- Document every parameter, or omit `Args` entirely. Half a list reads
  as an oversight.
- `Raises` is for exceptions a caller is expected to handle, not for
  every exception that can physically escape.
- A genuinely obvious one-liner stays a one-liner. [`chunked`][bdns.sync.pipeline.chunked] needs no
  `Args` block; forcing one adds noise, not information.

## Where the "why" goes: the three-way test

Long rationale is the most valuable thing in this codebase and the
easiest to put in the wrong place. For each paragraph, ask what it is
actually about:

- **This function's own implementation choice** → it stays, trimmed to
  three to six lines.
- **A decision that spans the module** → it moves to the module
  docstring.
- **An empirical measurement of the API** → it moves to `docs/`, and the
  docstring links to it.

Nothing gets deleted. It gets filed.

### Worked example

`bdns/sync/hashing.py::sorted_delimited_list` currently carries
twenty-five lines mixing all three categories. Split:

- Which fields shuffle their order (`sectorActividad` in minimis,
  `sectores` in ayudasestado) — **measurement**, belongs in
  [the API behaviour notes](https://cruzlorite.github.io/bdns-fetch/en/explanation/api-behavior/#shuffled-lists).
- Why the separator is a regex and not a plain character (CNAE names
  contain their own semicolons) — **this function's choice**, stays.
- Why hashing may be coarser than storage but never finer — **module
  scope**, belongs in the `policy.py` module docstring, which already
  makes that argument well.

### Before

```python
def prefetch(iterable: Iterable[Any]) -> Iterator[Any]:
    """Yield the items of `iterable`, pulling them on a helper thread that
    reads ahead of the caller.

    While the caller processes one item, the helper is already producing
    the next. The queue holds at most two items: if the caller falls
    behind, the helper blocks instead of filling memory.

    The caller does its work on its own thread. That matters for SQLite
    connections, which must stay on the thread that created them.

    If the helper raises, the exception is re-raised here. If the caller
    stops iterating early, the helper is unblocked and joined before the
    generator exits.
    """
```

### After

```python
def prefetch(iterable: Iterable[Any]) -> Iterator[Any]:
    """Yield the items of `iterable`, read ahead on a helper thread.

    The queue holds at most two items, so a slow caller blocks the
    helper instead of growing memory. The caller keeps its own thread,
    which SQLite requires: a connection may only be used on the thread
    that opened it.

    Args:
        iterable: Source of items, consumed on the helper thread.

    Yields:
        The items of `iterable`, in order.

    Raises:
        Exception: Whatever `iterable` raised, re-raised on the caller's
            thread. The helper is joined before this generator exits,
            including when the caller stops iterating early.
    """
```

Same facts, three fewer lines, and the signature is no longer buried.

## Module docstrings

Every module has one. Shape:

1. A summary line naming what lives here.
2. The design argument that makes the module cohere.

This is where essays belong. `bdns/sync/policy.py` is the model: it
explains why hash-only rules are safe and stored-payload rules are not,
which is a claim no single function could carry. Leave it as it is.

## Class docstrings

Summary line, then `Attributes:` for dataclasses and value objects. Do
not write a separate `__init__` docstring — the class docstring covers
construction.

## Public surface: `__all__`

Every module declares `__all__`, and it is the contract: names in
`__all__` cannot change without a breaking-change note in the changelog.

Module-private helpers keep the underscore prefix, and they stay
documented. The reference renders them next to the public names, one
page per module; the underscore is what tells a reader a name may change
without notice. [`_order_independent`][bdns.sync.hashing._order_independent] is private, and its docstring is
still one of the more useful ones in the package.

## Links from code

Keep references to the documentation rather than copying evidence into
docstrings: copies go stale. How to write one depends on whether it gets
rendered.

**In a docstring**, write a Markdown link. It is relative to the page the
docstring renders on, and every module's page lives in
`docs/reference/api/`:

```python
"""...

Evidence that the order varies is in
[the spurious-changes measurements](../../explanation/sync-behavior.md#spurious-changes).
"""
```

In the editor the path still says which file to open; on the site it is a
link.

**To another object**, use a cross-reference. A name in the docstring's
scope needs no target, and anything else takes its full path:

```python
"""Same shape as [`registration_window`][], for the other date family.

Serialized through [`PortableJSON`][bdns.sync.sinks.sql.schema.PortableJSON].
"""
```

A name between plain backticks renders as code, not as a link.

**In a comment, a script, a test or the Dockerfile**, nothing renders, so
write the path from the repository root:

```python
# See docs/explanation/sync-behavior.md#spurious-changes.
```

In every case:

- Link an **anchor**, never a section number. Section numbers move every
  time a section is inserted.
- The anchors are the explicit `<a id="…">` ids in the evidence
  documents. They are language-independent: a Spanish page and its
  translation use the same ones.

`scripts/check_doc_refs.py` resolves every such link, rendered or not, and
fails on a missing file or anchor. `scripts/check_site_links.py` reads the
built site and fails on any mention of a documented object, a document or
a script that is not a link.

## Language

- Code, comments, and docstrings: **English**, always.
- Site: Spanish is canonical. `foo.md` is the Spanish page and
  `foo.en.md` its English translation; a page with no translation falls
  back to the Spanish one (`mkdocs.yml`, `i18n` plugin). Docstrings are
  English, so the generated API reference pages are English in both
  languages.

## Enforcement

`ruff` carries the shape so review can spend its attention on content:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "D"]
ignore = [
    "E741",  # ambiguous variable name (O is required by API)
    "E501",  # long lines: docstrings/comments carry verified-live evidence
    "D105",  # magic methods: the class docstring covers them
    "D107",  # __init__: documented on the class
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]
```

The same configuration applies in bdns-fetch, and CI runs
`ruff format --check` in both.

CI additionally runs `mkdocs build --strict`, which fails on a broken
internal link or an unresolvable reference target.
