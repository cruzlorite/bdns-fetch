"""The boundaries between modules: each builds only on the ones below it.

bdns.fetch stands on its own; bdns.sync builds on it; bdns.dataset builds on
both. Never the other way round, so each module keeps working, and could
ship on its own, without anything the ones above it need. See
docs/adr/0001-one-package.md.
"""

import ast
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "bdns"
FETCH = SRC / "fetch"


def _imported_modules(path: pathlib.Path) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.ImportFrom) and node.level > 1:
            # `from .. import sync` climbs out of bdns.fetch.
            modules.add("." * node.level + (node.module or ""))
    return modules


def test_fetch_never_imports_other_bdns_modules():
    offending = {
        f"{path.relative_to(FETCH)}: {module}"
        for path in FETCH.rglob("*.py")
        for module in _imported_modules(path)
        if (module.startswith("bdns.") and not module.startswith("bdns.fetch"))
        or module.startswith("..")
    }
    assert not offending


def test_sync_never_imports_the_dataset():
    offending = {
        f"{path.relative_to(SRC)}: {module}"
        for path in (SRC / "sync").rglob("*.py")
        for module in _imported_modules(path)
        if module.startswith("bdns.dataset")
    }
    assert not offending
