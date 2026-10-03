# SPDX-License-Identifier: GPL-3.0-or-later

"""Small helpers shared by the client and the CLI.

Nothing here performs HTTP requests or knows about any specific endpoint.
"""

import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from enum import Enum
from typing import IO, Any
from urllib.parse import urlencode

__all__ = [
    "RateLimiter",
    "format_date_for_api_request",
    "format_url",
    "smart_open",
]


class RateLimiter:
    """Thread-safe token bucket: `rate` acquisitions every `per` seconds, at most `burst` at once.

    With the default `burst=1` it spaces requests evenly, `per / rate`
    apart. That is deliberate: the BDNS API answers 429 to a burst even when
    the average stays under its limit, and accepts a sustained 9.8 requests
    per second when their starts are spaced
    ([measurements](../../explanation/api-behavior.md#rate-limit)).

    Args:
        rate: Acquisitions allowed per `per` seconds.
        per: Length of the period, in seconds.
        burst: Acquisitions that may happen back to back after a pause.
    """

    def __init__(self, rate: float, per: float = 1.0, burst: int = 1):
        if rate <= 0 or per <= 0 or burst < 1:
            raise ValueError("rate and per must be positive, burst 1 or greater")
        self.rate = rate
        self.per = per
        self.burst = burst
        self._tokens = float(burst)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available, then take it."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(
                    self.burst,
                    self._tokens + (now - self._last) * (self.rate / self.per),
                )
                self._last = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait = (1 - self._tokens) * (self.per / self.rate)
            time.sleep(wait)


def format_date_for_api_request(value: date | None, output_format: str = "%d/%m/%Y") -> str | None:
    """Format a date the way the BDNS API expects it in query strings.

    Args:
        value: The date to format. `None` passes through.
        output_format: A `strftime` format. The API uses `dd/mm/yyyy`.

    Returns:
        The formatted date, or `None` if `value` was `None`.

    Raises:
        ValueError: If `value` is not a `date`.
    """
    if value is None:
        return None
    if not isinstance(value, date):
        raise ValueError("The date must be a date object.")
    return value.strftime(output_format)


def format_url(url: str, query_params: dict[str, Any]) -> str:
    """Append `query_params` to `url` as a query string.

    `None` values are dropped, enums are replaced by their value, and lists
    become repeated keys (`organos=1&organos=2`).
    """
    if not url.endswith("?"):
        url += "?"
    params = {
        key: value.value if isinstance(value, Enum) else value
        for key, value in query_params.items()
        if value is not None
    }
    return url + urlencode(params, doseq=True)


@contextmanager
def smart_open(file: Any, *args: Any, **kwargs: Any) -> Iterator[IO]:
    """Open `file`, or use standard output when it is `"-"`.

    Extra arguments go to `open()`. In binary mode (`"wb"`), standard output
    is its underlying byte stream.
    """
    if str(file) == "-":
        mode = args[0] if args else kwargs.get("mode", "r")
        if "b" in mode:
            yield sys.stdout.buffer
        else:
            sys.stdout.reconfigure(encoding="utf-8")
            yield sys.stdout
    else:
        with open(file, *args, **kwargs) as f:
            yield f
