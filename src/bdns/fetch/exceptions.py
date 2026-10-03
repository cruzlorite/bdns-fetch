# SPDX-License-Identifier: GPL-3.0-or-later

"""Exceptions raised by the BDNS client, and the mapping from HTTP errors to them.

Every failure the client reports is a [`BDNSError`][bdns.fetch.exceptions.BDNSError].
The ones worth retrying (rate limiting, server errors, database maintenance)
are the subclass [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError],
which is what the client's retry policy keys on. Callers that only want to
know whether a request failed can keep catching `BDNSError`.

Nothing here prints: presenting an error is the CLI's job.
"""

import json

__all__ = [
    "BDNSError",
    "BDNSTransientError",
    "BDNSWarning",
    "handle_api_response",
]


class BDNSError(Exception):
    """A request to the BDNS API failed.

    Attributes:
        message: What went wrong, in the API's own words when it gave any.
        suggestion: What the caller could change, if anything.
        technical_details: Status, URL, and a preview of the response body.
    """

    def __init__(
        self,
        message: str,
        suggestion: str | None = None,
        technical_details: str | None = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.technical_details = technical_details
        super().__init__(self.message)


class BDNSTransientError(BDNSError):
    """A request failed in a way that may succeed if repeated.

    Raised for HTTP 429 and 5xx responses, and for API error codes that
    signal a temporary condition such as `ERR_MANTENIMIENTO_BBDD`. The
    client retries these; one reaches the caller only after the retries
    are exhausted.

    Attributes:
        retry_after: Seconds the server asked to wait (`Retry-After`), if
            it said.
    """

    def __init__(
        self,
        message: str,
        suggestion: str | None = None,
        technical_details: str | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, suggestion, technical_details)
        self.retry_after = retry_after


class BDNSWarning(BDNSError):
    """The API answered successfully but with no data.

    Kept for backward compatibility. The client no longer raises it: an
    empty answer is an empty result.
    """


def parse_bdns_error_response(response_text: str) -> tuple[str, list[str]]:
    """Extract the error code and messages from a BDNS error body.

    Args:
        response_text: The raw response body.

    Returns:
        The `codigo` field (or `"PARSE_ERROR"` when the body is not a BDNS
        error document) and the list of messages it carries.
    """
    try:
        error_data = json.loads(response_text)
    except (TypeError, ValueError):
        error_data = None

    if isinstance(error_data, dict):
        error_code = error_data.get("codigo", "UNKNOWN_ERROR")
        if isinstance(error_data.get("errores"), list):
            return error_code, error_data["errores"]
        for key in ("error", "message", "detail"):
            if key in error_data:
                return error_code, [str(error_data[key])]
        return error_code, []

    return "PARSE_ERROR", [response_text[:200] if response_text else "No error details available"]


def format_bdns_error_message(error_code: str, error_messages: list[str]) -> str:
    """Render an error code and its messages as one human-readable string.

    The messages stay in the language the API wrote them in (Spanish).
    """
    if not error_messages:
        return "Server returned an error (no details provided)"

    error_type = f"Error ({error_code})" if error_code != "PARSE_ERROR" else "Server Error"
    if len(error_messages) == 1:
        return f"{error_type}: {error_messages[0]}"
    numbered = "\n".join(f"  {i}. {msg}" for i, msg in enumerate(error_messages, 1))
    return f"{error_type}:\n{numbered}"


# Fallback message and advice for each status, used when the body says nothing.
_STATUS_HINTS: dict[int, tuple[str, str]] = {
    400: (
        "Bad Request",
        "Check your parameter values and formats. Use --help to see valid parameter examples.",
    ),
    401: ("Unauthorized", "This endpoint may require authentication."),
    403: ("Forbidden", "You don't have permission to access this resource."),
    404: (
        "Not Found",
        "Check if the endpoint URL is correct or if the requested resource exists.",
    ),
    429: ("Too Many Requests", "Wait a moment and try again, or reduce --max-workers."),
}


def handle_api_response(
    status_code: int,
    url: str,
    response_text: str = "",
    response_headers: dict | None = None,
) -> BDNSError:
    """Build the exception that describes an unsuccessful response.

    Args:
        status_code: HTTP status of the response.
        url: The requested URL.
        response_text: The response body.
        response_headers: The response headers, included in the details.

    Returns:
        The exception to raise. It is returned rather than raised so the
        caller can decide whether it is transient.
    """
    tech_details = f"HTTP {status_code} from {url}"
    if response_text:
        preview = response_text[:100] + ("..." if len(response_text) > 100 else "")
        tech_details += f"\nResponse content (first 100 chars): {preview}"
    if response_headers:
        tech_details += "\nResponse headers:"
        for key, value in response_headers.items():
            tech_details += f"\n  {key}: {value}"

    if status_code in (200, 204):
        return BDNSWarning(
            message="No data available for the specified parameters.",
            suggestion="This might be expected if no records match your criteria. Try different parameters.",
            technical_details=tech_details,
        )

    error_code, error_messages = parse_bdns_error_response(response_text)
    if status_code in _STATUS_HINTS:
        fallback, suggestion = _STATUS_HINTS[status_code]
    elif status_code >= 500:
        fallback, suggestion = (
            "Internal Server Error",
            "The API server is experiencing issues. Try again later.",
        )
    else:
        fallback, suggestion = None, "Check your internet connection and try again."

    message = format_bdns_error_message(error_code, error_messages)
    if fallback and not error_messages:
        message = fallback
    return BDNSError(message=message, suggestion=suggestion, technical_details=tech_details)
