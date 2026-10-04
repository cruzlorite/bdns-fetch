#!/usr/bin/env python3
"""Fail on references in the built site that are not links.

A page that names another page, a documented object or a script should
let the reader click through. Written as plain text, the reference is a
dead end: on the site nothing says where `split_range` is
documented, and "docs/explanation/..." is a path to a file nobody browsing
the site can open.

This reads the site the way a reader meets it, after mkdocs has built it
and mkdocstrings has rendered every docstring, and reports:

- code that names a documented object (a module, class or function with a
  docstring) without linking to it;
- a documentation path or an orchestration script left as text or code.

Names that are also parameter names are skipped: `policy` or `rows` in an
argument description means the argument, not the module. Code blocks,
headings and signatures are skipped too.

Run after `mkdocs build`, from the repository root, or via
`make check-docs`.
"""

import html
import pathlib
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser

import griffe
from modules import ROOT, SRC, modules

SITE = ROOT / "site"
PATHS = re.compile(r"docs/[\w./-]+\.md(?:#[\w-]+)?|scripts/\w+\.sh")
SCRIPT = re.compile(r"(?:scripts/)?\w+_load\.sh")
BLOCKING = {"a", "pre", "h1", "h2", "h3", "h4", "h5", "h6"}
VOID = {"br", "img", "hr", "input", "meta", "link", "wbr"}


def documented_names() -> tuple[dict[str, set[str]], set[str]]:
    """Map every way of naming a documented object to its full paths.

    Returns:
        `(names, params)`: each suffix of each documented path (so
        `generic.to_api_upper_bound` and `split_range` both count)
        mapped to the paths it can mean, and every parameter name in the
        package.
    """
    paths: set[str] = set()
    params: set[str] = set()

    def walk(obj: griffe.Object, cli: str) -> None:
        for member in obj.members.values():
            # CLI command functions share their names with the commands
            # (`delta`, `backfill`...), which pages mention as commands;
            # the CLI reference documents those, not the API reference.
            if member.is_alias or member.path.startswith(cli):
                continue
            if (member.is_module or member.is_class or member.is_function) and member.docstring:
                paths.add(member.path)
            if member.is_function:
                params.update(p.name for p in member.parameters)
            if member.is_module or member.is_class:
                walk(member, cli)

    loaded = [
        griffe.load(module.name, search_paths=[str(SRC)], docstring_parser="google")
        for module in modules()
    ]
    for module in loaded:
        paths.add(module.path)
        walk(module, f"{module.path}.cli.")
    names: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        parts = path.split(".")
        for i in range(len(parts)):
            names[".".join(parts[i:])].add(path)
    # A package's last name on its own (`sync`, `fetch`) is the tool's verb
    # in running text, not a reference to the package.
    for module in loaded:
        names.pop(module.path.split(".")[-1], None)
    return names, params


class Article(HTMLParser):
    """Collect the unlinked code and running text of a page's article."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, str]] = []
        self.code: list[str] | None = None
        self.code_linked = False
        self.unlinked_code: list[str] = []
        self.text: list[str] = []

    def blocked(self) -> bool:
        """Return whether the current position is inside a skipped element."""
        return any(tag in BLOCKING or "doc-signature" in cls for tag, cls in self.stack)

    def handle_starttag(self, tag, attrs):
        """Track nesting; note links that sit inside a code element."""
        if tag in VOID:
            return
        if tag == "a" and self.code is not None:
            self.code_linked = True
        self.stack.append((tag, dict(attrs).get("class") or ""))
        if tag == "code":
            self.code, self.code_linked = [], False

    def handle_endtag(self, tag):
        """Close elements, recording a finished code span if it was unlinked."""
        while self.stack:
            if self.stack.pop()[0] == tag:
                break
        if tag == "code" and self.code is not None:
            if not self.code_linked and not self.blocked():
                self.unlinked_code.append("".join(self.code).strip())
            self.code = None

    def handle_data(self, data):
        """Accumulate code text, or running text outside skipped elements."""
        if self.code is not None:
            self.code.append(data)
        elif not self.blocked():
            self.text.append(data)


def check(site: pathlib.Path) -> list[str]:
    """Return one message per unlinked reference, across every built page."""
    names, params = documented_names()
    problems = []
    for page in sorted(site.rglob("index.html")):
        match = re.search(r"<article[^>]*>(.*)</article>", page.read_text(encoding="utf-8"), re.S)
        if not match:
            continue
        article = Article()
        article.feed(match.group(1))
        where = "/" if page.parent == site else f"/{page.parent.relative_to(site)}/"
        found = set()
        for code in article.unlinked_code:
            name = code.rstrip("()")
            if SCRIPT.fullmatch(code) or PATHS.fullmatch(code):
                found.add(f"`{code}` is not a link")
            elif (
                name in names
                and not name.startswith("__")
                and not ("." not in name and name in params)
            ):
                found.add(f"`{code}` names {' or '.join(sorted(names[name]))} but is not a link")
        for path in PATHS.findall(html.unescape(" ".join(article.text))):
            found.add(f"'{path}' is not a link")
        problems += [f"{where}: {item}" for item in sorted(found)]
    return problems


def main() -> int:
    """Check the built site. Returns an exit code."""
    if not SITE.is_dir():
        print("no site/ directory: run `mkdocs build` first", file=sys.stderr)
        return 2
    problems = check(SITE)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"checked the built site, {len(problems)} unlinked references")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
