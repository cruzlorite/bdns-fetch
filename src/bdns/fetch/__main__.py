# SPDX-License-Identifier: GPL-3.0-or-later

"""Entry point for `python -m bdns.fetch` and the `bdns-fetch` console script."""

from bdns.fetch.cli import app

if __name__ == "__main__":
    app()
