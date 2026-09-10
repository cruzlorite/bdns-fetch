#!/usr/bin/env python3
"""Check the parts of the docstring convention that ruff cannot see.

ruff enforces the shape of a docstring: that one exists, where the blank
lines go, that the summary is one imperative line. What it cannot check
is whether the docstring agrees with the signature it sits above, which
is where a docstring actually goes stale: a parameter gets added and the
Args block does not.

This reads the package the way mkdocstrings does, through griffe, so a
failure here is a failure the rendered reference would have shown.

Run from the repository root, or via `make check-docs`.
"""

import pathlib
import sys

import griffe

ROOT = pathlib.Path(__file__).resolve().parent.parent

# __init__ is documented on its class (ruff's D107 is off for the same
# reason), and a module with no module-level names has nothing to export.
SKIP_MEMBERS = {"__init__"}
NO_PUBLIC_SURFACE = {"bdns.sync.__main__"}


def check(pkg: griffe.Module) -> list[str]:
    """Walk the package, returning one message per convention breach."""
    problems: list[str] = []

    def walk(obj: griffe.Object) -> None:
        for name, member in obj.members.items():
            if member.is_alias:
                continue

            if member.is_module:
                if member.path not in NO_PUBLIC_SURFACE and not member.exports:
                    problems.append(f"{member.path}: module declares no __all__")
                walk(member)
                continue

            # Attributes are documented in their class's Attributes block,
            # and module-level constants in the comment above them, so
            # neither carries a docstring of its own.
            if not (member.is_class or member.is_function):
                continue

            if name in SKIP_MEMBERS:
                continue

            if not member.docstring:
                problems.append(f"{member.path}: no docstring")
                continue

            if member.is_class:
                walk(member)
                continue

            documented: set[str] = set()
            for section in member.docstring.parsed:
                if section.kind.value == "parameters":
                    documented = {p.name for p in section.value}

            # The convention allows omitting Args entirely, but a partial
            # list reads as an oversight.
            if not documented:
                continue

            signature = {
                p.name
                for p in member.parameters
                if p.name not in ("self", "cls") and not p.name.startswith("*")
            }
            for undocumented in sorted(signature - documented):
                problems.append(f"{member.path}: parameter '{undocumented}' is not in Args")
            for stale in sorted(documented - signature):
                problems.append(f"{member.path}: Args documents '{stale}', which is not a parameter")

    walk(pkg)
    return problems


def main() -> int:
    """Load the package and report. Returns an exit code."""
    pkg = griffe.load("bdns.sync", search_paths=[str(ROOT / "src")], docstring_parser="google")
    problems = check(pkg)

    for problem in problems:
        print(problem, file=sys.stderr)

    print(f"checked bdns.sync against docs/contributing/docstrings.md, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
