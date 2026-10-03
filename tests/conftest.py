"""Shared fixtures. Unit tests never touch the network: HTTP goes through `responses`."""

import json
import re
from urllib.parse import parse_qs, urlsplit

import pytest
import responses as responses_lib

from bdns.fetch import BDNSClient
from bdns.fetch.endpoints import BDNS_API_BASE_URL


class _NoRateLimit:
    def acquire(self) -> None:
        pass


@pytest.fixture(autouse=True)
def no_rate_limit(monkeypatch):
    """Lift the 10 req/s limit, which would only slow the suite down."""
    monkeypatch.setattr("bdns.fetch.client.DEFAULT_RATE_LIMITER", _NoRateLimit())


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    """Record retry waits instead of sleeping through them."""
    waits: list[float] = []
    monkeypatch.setattr("tenacity.nap.time.sleep", waits.append)
    return waits


@pytest.fixture
def mocked():
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def client():
    return BDNSClient(wait_time=1, progress=False)


def endpoint(path: str) -> re.Pattern:
    """Match an endpoint URL with any query string."""
    return re.compile(re.escape(f"{BDNS_API_BASE_URL}/{path}") + r"(\?.*)?$")


def query_of(call) -> dict[str, list[str]]:
    return parse_qs(urlsplit(call.request.url).query)


def page(number: int, total_pages: int, size: int = 2) -> dict:
    """A page document in the API's shape, with records numbered by position."""
    start = number * size
    return {
        "content": [{"id": start + i} for i in range(size)],
        "number": number,
        "totalPages": total_pages,
    }


def paginated(total_pages: int, size: int = 2, delay=None):
    """A `responses` callback serving `total_pages` pages, optionally delayed per page."""

    def callback(request):
        number = int(parse_qs(urlsplit(request.url).query)["page"][0])
        if delay:
            delay(number)
        return 200, {}, json.dumps(page(number, total_pages, size))

    return callback
