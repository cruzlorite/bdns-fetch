#!/usr/bin/env python3
"""Verify that every docs/ reference in the code points somewhere real.

Docstrings, tests, scripts, the dataset's SQL, the Dockerfile and the Makefile link to the
documents instead of copying them, which is what stops the two from
drifting. That only works while the links do: a renamed file or a
reworded heading silently turns a reference into a dead end that nothing
else would catch.

Run from the repository root, or via `make check-docs`.
"""

import pathlib
import re
import sys

from modules import ROOT, SRC, modules

REF = re.compile(r"docs/[\w./-]+\.md(?:#([\w-]+))?")
# A docstring links relative to the page it renders on, and every module's
# page is in docs/<module>/reference/api/. mkdocs does not validate these:
# they come out of mkdocstrings after its own link checks have run.
REL = re.compile(r"\]\((\.\./[\w./-]+\.md)(?:#([\w-]+))?\)")
ANCHOR = re.compile(r'<a id="([\w-]+)"></a>')
SOURCES = (
    "src/**/*.py",
    "tests/**/*.py",
    "scripts/*.sh",
    "dataset/**/*.sql",
    "Dockerfile",
    "Makefile",
)


def anchors_in(path: pathlib.Path) -> set[str]:
    """Return the explicit anchor ids declared in a Markdown file."""
    return set(ANCHOR.findall(path.read_text(encoding="utf-8")))


def main() -> int:
    """Check every reference, reporting each failure. Returns an exit code."""
    problems: list[str] = []
    checked = 0

    # Each source with the directory its docstrings' relative links resolve
    # against: the API pages of its module. Only Python under src/ renders.
    api_pages = {module.path: module.docs / "reference" / "api" for module in modules()}
    sources: list[tuple[pathlib.Path, pathlib.Path | None]] = []
    for pattern in SOURCES:
        for path in sorted(ROOT.glob(pattern)):
            module = SRC / "bdns" / path.relative_to(SRC).parts[1] if SRC in path.parents else None
            sources.append((path, api_pages.get(module)))

    for source, api_pages in sources:
        text = source.read_text(encoding="utf-8")
        for match in REF.finditer(text):
            checked += 1
            ref, anchor = match.group(0), match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            target = ROOT / ref.split("#")[0]
            where = f"{source.relative_to(ROOT)}:{line}"

            if not target.exists():
                problems.append(f"{where}: {ref} -> no such file")
            elif anchor and anchor not in anchors_in(target):
                problems.append(f"{where}: {ref} -> no anchor '{anchor}' in that file")

        if api_pages is None:
            continue
        for match in REL.finditer(text):
            checked += 1
            rel, anchor = match.group(1), match.group(2)
            line = text.count("\n", 0, match.start()) + 1
            target = (api_pages / rel).resolve()
            where = f"{source.relative_to(ROOT)}:{line}"
            if not target.exists():
                relative_to = api_pages.relative_to(ROOT)
                problems.append(f"{where}: {rel} -> no such file (relative to {relative_to})")
            elif anchor and anchor not in anchors_in(target):
                problems.append(f"{where}: {rel}#{anchor} -> no anchor '{anchor}' in that file")

    for problem in problems:
        print(problem, file=sys.stderr)

    print(f"checked {checked} references, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
