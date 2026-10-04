"""Find the modules of the bdns package, for the scripts that check them all.

Each module lives in src/bdns/<name>/ and is documented in docs/<name>/, so
listing one directory is enough to find them all, and adding a module needs
no change here.
"""

import pathlib
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


@dataclass(frozen=True)
class Module:
    """One module of the package and where its parts live.

    Attributes:
        name: Its import path, such as `bdns.fetch`.
        path: Its source directory, `src/bdns/<name>`.
        docs: Its documentation directory, `docs/<name>`.
    """

    name: str
    path: pathlib.Path
    docs: pathlib.Path


def modules() -> list[Module]:
    """Return every module under src/bdns/, sorted by name."""
    return [
        Module(f"bdns.{init.parent.name}", init.parent, ROOT / "docs" / init.parent.name)
        for init in sorted(SRC.glob("bdns/*/__init__.py"))
    ]
