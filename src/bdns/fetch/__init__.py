# SPDX-License-Identifier: MIT

"""BDNS Fetch: Python client and CLI for the BDNS API.

The public API is what this module exports, plus the modules
[`dates`][bdns.fetch.dates] and [`contract`][bdns.fetch.contract]. Names
elsewhere in the package may change in any release.
"""

from importlib.metadata import PackageNotFoundError, version

from bdns.fetch.client import BDNSClient
from bdns.fetch.exceptions import BDNSError, BDNSTransientError
from bdns.fetch.types import (
    Ambito,
    DescripcionTipoBusqueda,
    Direccion,
    Order,
    TipoAdministracion,
)
from bdns.fetch.utils import RateLimiter

try:
    __version__ = version("bdns-tools")
except PackageNotFoundError:
    # Running from a source tree that was never installed.
    __version__ = "0.0.0+unknown"

__all__ = [
    "Ambito",
    "BDNSClient",
    "BDNSError",
    "BDNSTransientError",
    "DescripcionTipoBusqueda",
    "Direccion",
    "Order",
    "RateLimiter",
    "TipoAdministracion",
    "__version__",
]
