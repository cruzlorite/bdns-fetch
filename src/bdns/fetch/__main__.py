# SPDX-License-Identifier: GPL-3.0-or-later

"""
@file __main__.py
@brief Main entry point for the BDNS API command line interface.
@details
This script provides a command line interface to interact with the BDNS API.
It allows users to fetch data from the API and save it to a file or print it to stdout.
@author: José María Cruz Lorite <josemariacruzlorite@gmail.com>
"""

import logging

from bdns.fetch.cli import app

if __name__ == "__main__":
    # Configure logging only when run as CLI, not when imported
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Ensure configuration is applied even if basicConfig was called before
    )
    app()
