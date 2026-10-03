# SPDX-License-Identifier: GPL-3.0-or-later

"""BDNS Fetch: Python client and CLI for the BDNS API.

The public API is what this module exports. Names elsewhere in the package
may change in any release.
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
from bdns.fetch.utils import format_date_for_api_request, format_url, smart_open

try:
    __version__ = version("bdns-fetch")
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
    "TipoAdministracion",
    "__version__",
    "format_date_for_api_request",
    "format_url",
    "smart_open",
]
