# SPDX-License-Identifier: MIT

"""BDNS Dataset - builds the anonymised, aggregated dataset from bdns-sync's tables.

Experimental: nothing here is covered by the compatibility policy until the
first version of the dataset is published. What may be published, and why,
is in docs/adr/0002-anonymised-dataset.md.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bdns-tools")
except PackageNotFoundError:
    # Running straight from a source tree that was never installed. Only
    # happens in development; an installed package always has metadata.
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
