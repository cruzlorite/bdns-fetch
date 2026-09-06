"""BDNS Sync - keeps target databases in SCD2 form from the BDNS API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bdns-sync")
except PackageNotFoundError:
    # Running straight from a source tree that was never installed. Only
    # happens in development; an installed package always has metadata.
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
