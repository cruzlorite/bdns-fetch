"""The boundary between modules: bdns.fetch stands on its own.

bdns.sync builds on bdns.fetch, never the other way round, so the client
keeps working, and could ship on its own, without anything sync needs. See
docs/adr/0001-one-package.md.
"""

import ast
import pathlib

FETCH = pathlib.Path(__file__).resolve().parent.parent / "src" / "bdns" / "fetch"


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
