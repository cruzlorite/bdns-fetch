# -*- coding: utf-8 -*-
"""
Custom exceptions for BDNS API client.
"""


class BDNSAPIError(Exception):
    """Base exception for BDNS API related errors."""

    pass


class BDNSAPIConnectionError(BDNSAPIError):
    """Raised when connection to BDNS API fails."""

    pass


class BDNSAPIResponseError(BDNSAPIError):
    """Raised when BDNS API returns an error response."""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class BDNSAPITimeoutError(BDNSAPIError):
    """Raised when BDNS API request times out."""

    pass


class BDNSAPIRateLimitError(BDNSAPIError):
    """Raised when BDNS API rate limit is exceeded."""

    pass


class BDNSDataValidationError(BDNSAPIError):
    """Raised when data validation fails."""

    pass
