__version__ = "2.1.0"

from bdns.fetch.utils import smart_open, format_date_for_api_request, format_url
from bdns.fetch.types import (
    Order,
    Direccion,
    TipoAdministracion,
    DescripcionTipoBusqueda,
)
from bdns.fetch.exceptions import BDNSError, BDNSWarning


# Import BDNSClient only when needed to avoid runpy conflicts
def __getattr__(name):
    if name == "BDNSClient":
        from bdns.fetch.client import BDNSClient

        return BDNSClient
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "__version__",
    "format_date_for_api_request",
    "format_url",
    "smart_open",
    "Order",
    "Direccion",
    "TipoAdministracion",
    "DescripcionTipoBusqueda",
    "BDNSError",
    "BDNSWarning",
    "BDNSClient",
]
