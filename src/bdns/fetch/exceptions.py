# SPDX-License-Identifier: GPL-3.0-or-later

"""Exceptions raised by the BDNS client.

Every failure the API reports is a [`BDNSError`][bdns.fetch.exceptions.BDNSError],
carrying what a program needs to react to it: the HTTP status, the API's
own error code and the URL. The ones worth retrying (rate limiting, server
errors, database maintenance) are the subclass
[`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError], which is
what the client's retry policy keys on.

Nothing here prints or gives advice: presenting an error is the CLI's job.
"""

import json
from collections.abc import Collection, Mapping

__all__ = ["BDNSError", "BDNSTransientError", "error_from_response"]


class BDNSError(Exception):
    """The BDNS API reported an error.

    `str(error)` is `message`.

    Attributes:
        message: What went wrong, in the API's own words when it gave any
            (usually Spanish).
        status_code: HTTP status of the response.
        code: The API's error code (`codigo`), such as `ERR_VALIDACION`,
            when the body carried one.
        url: The requested URL.
        details: Status, URL, response headers and a preview of the body,
            for logs and bug reports.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        url: str | None = None,
        details: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.url = url
        self.details = details


class BDNSTransientError(BDNSError):
    """A request failed in a way that may succeed if repeated.

    Raised for HTTP 429 and 5xx responses, and for error codes that signal
    a temporary condition such as `ERR_MANTENIMIENTO_BBDD`. The client
    retries these; one reaches the caller only after the retries run out.

    Attributes:
        retry_after: Seconds the server asked to wait (`Retry-After`), if
            it said.
    """

    def __init__(self, message: str, *, retry_after: float | None = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


def _parse_body(body: str) -> tuple[str | None, list[str]]:
    """Extract the error code and messages from a BDNS error body."""
    try:
        document = json.loads(body)
    except (TypeError, ValueError):
        document = None
    if not isinstance(document, dict):
        return None, []
    code = document.get("codigo")
    if isinstance(document.get("errores"), list):
        return code, [str(m) for m in document["errores"]]
    for key in ("error", "message", "detail"):
        if key in document:
            return code, [str(document[key])]
    return code, []


_STATUS_TEXT = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    429: "Too Many Requests",
}


def _message(status_code: int, code: str | None, messages: list[str], body: str) -> str:
    """Compose the one-line (or numbered) message an error is known by."""
    prefix = f"Error ({code})" if code else f"HTTP {status_code}"
    if len(messages) == 1:
        return f"{prefix}: {messages[0]}"
    if messages:
        return f"{prefix}:\n" + "\n".join(f"  {i}. {m}" for i, m in enumerate(messages, 1))
    fallback = _STATUS_TEXT.get(status_code)
    if fallback is None:
        fallback = "Server error" if status_code >= 500 else (body[:200] or "No details")
    return f"{prefix}: {fallback}"


def _parse_retry_after(headers: Mapping[str, str]) -> float | None:
    """Read `Retry-After` as seconds. HTTP-date values are ignored."""
    value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
    try:
        return max(0.0, float(value)) if value is not None else None
    except ValueError:
        return None


def error_from_response(
    *,
    status_code: int,
    url: str,
    body: str,
    headers: Mapping[str, str],
    transient_statuses: Collection[int],
    transient_codes: Collection[str],
) -> BDNSError:
    """Build the exception that describes an error response.

    The API sometimes reports an error inside a 200 response; that is an
    error too.

    Args:
        status_code: HTTP status of the response.
        url: The requested URL.
        body: The response body.
        headers: The response headers.
        transient_statuses: Statuses that make the error transient.
        transient_codes: API error codes that make it transient, whatever
            the status.

    Returns:
        A [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError] if either rule matches, else a [`BDNSError`][bdns.fetch.exceptions.BDNSError].
        Returned rather than raised, so the caller raises it in context.
    """
    code, messages = _parse_body(body)
    preview = body[:500] + ("..." if len(body) > 500 else "")
    details = "\n".join(
        [f"HTTP {status_code} from {url}", "Response headers:"]
        + [f"  {key}: {value}" for key, value in headers.items()]
        + [f"Response body: {preview}"]
    )
    fields = {"status_code": status_code, "code": code, "url": url, "details": details}
    message = _message(status_code, code, messages, body)
    if status_code in transient_statuses or code in transient_codes:
        return BDNSTransientError(message, retry_after=_parse_retry_after(headers), **fields)
    return BDNSError(message, **fields)
