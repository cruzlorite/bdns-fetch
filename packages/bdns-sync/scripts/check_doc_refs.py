#!/usr/bin/env python3
"""Verify that every docs/ reference in the code points somewhere real.

Docstrings, tests, the orchestration scripts and the Dockerfile link to the
documents instead of copying them, which is what stops the two from
drifting. That only works while the links do: a renamed file or a
reworded heading silently turns a reference into a dead end that nothing
else would catch.

Run from the repository root, or via `make check-docs`.
"""

import pathlib
import re
import sys

REF = re.compile(r"docs/[\w./-]+\.md(?:#([\w-]+))?")
ANCHOR = re.compile(r'<a id="([\w-]+)"></a>')

ROOT = pathlib.Path(__file__).resolve().parent.parent


def anchors_in(path: pathlib.Path) -> set[str]:
    """Return the explicit anchor ids declared in a Markdown file."""
    return set(ANCHOR.findall(path.read_text(encoding="utf-8")))


def main() -> int:
    """Check every reference, reporting each failure. Returns an exit code."""
    problems: list[str] = []
    checked = 0

    sources = [
        path
        for pattern in ("src/**/*.py", "tests/*.py", "scripts/*.sh", "Dockerfile", "Makefile")
        for path in sorted(ROOT.glob(pattern))
    ]

    for source in sources:
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

    for problem in problems:
        print(problem, file=sys.stderr)

    print(f"checked {checked} references, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
