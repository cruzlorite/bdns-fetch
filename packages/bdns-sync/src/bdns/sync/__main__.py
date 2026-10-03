# SPDX-License-Identifier: MIT

"""Main entry point for the BDNS Sync command line interface.

Also what the installed `bdns-sync` console script points to
(`pyproject.toml`). It imports `app` directly rather than running this
module as `__main__`, so logging setup lives in `cli.py`'s callback
instead of here (see its docstring).
"""

from bdns.sync.cli import app

if __name__ == "__main__":
    app()
