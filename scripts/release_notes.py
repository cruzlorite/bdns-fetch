#!/usr/bin/env python3
"""Print one version's section of CHANGELOG.md, for its GitHub release.

The release workflow runs it twice: before publishing, so a tag whose
version has no changelog entry stops before anything reaches PyPI, and
after, to fill in the release notes.

Usage: python scripts/release_notes.py X.Y.Z
"""

import re
import sys

from modules import ROOT

CHANGELOG = ROOT / "CHANGELOG.md"


def section(changelog: str, version: str) -> str | None:
    """Return the body under ``## [version]``, or None if there is none.

    Args:
        changelog: The whole changelog text.
        version: The version, without the leading ``v``.

    Returns:
        The text between that heading and the next ``## `` heading, with
        surrounding blank lines removed, or None when the heading is missing
        or the section is empty.
    """
    heading = re.search(rf"^## \[{re.escape(version)}\].*$", changelog, re.MULTILINE)
    if heading is None:
        return None
    following = re.search(r"^## ", changelog[heading.end() :], re.MULTILINE)
    end = heading.end() + following.start() if following else len(changelog)
    return changelog[heading.end() : end].strip() or None


def main() -> int:
    """Print the section of the version given on the command line."""
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    version = sys.argv[1]
    notes = section(CHANGELOG.read_text(encoding="utf-8"), version)
    if notes is None:
        print(f"CHANGELOG.md has no section for {version}", file=sys.stderr)
        return 1
    print(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
