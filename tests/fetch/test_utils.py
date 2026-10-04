import time
from datetime import date
from urllib.parse import parse_qs, urlsplit

import pytest

from bdns.fetch import BDNSError, BDNSTransientError, TipoAdministracion
from bdns.fetch.exceptions import error_from_response
from bdns.fetch.utils import RateLimiter, format_date_for_api_request, format_url


def test_format_date():
    assert format_date_for_api_request(date(2024, 1, 31)) == "31/01/2024"
    assert format_date_for_api_request(None) is None
    with pytest.raises(ValueError):
        format_date_for_api_request("2024-01-31")


def test_format_url_drops_none_unwraps_enums_and_repeats_lists():
    url = format_url("https://x/api", {"a": None, "b": TipoAdministracion.L, "c": [1, 2], "d": "é"})
    query = parse_qs(urlsplit(url).query)
    assert query == {"b": ["L"], "c": ["1", "2"], "d": ["é"]}


def test_rate_limiter_spaces_calls_evenly_by_default():
    limiter = RateLimiter(rate=20)
    start = time.monotonic()
    for _ in range(5):  # first at once, then one every 50 ms
        limiter.acquire()
    assert 0.19 <= time.monotonic() - start < 0.5


def test_rate_limiter_allows_a_burst_when_asked():
    limiter = RateLimiter(rate=1, burst=5)
    start = time.monotonic()
    for _ in range(5):
        limiter.acquire()
    assert time.monotonic() - start < 0.1


@pytest.mark.parametrize("kwargs", [{"rate": 0}, {"rate": 1, "per": 0}, {"rate": 1, "burst": 0}])
def test_rate_limiter_rejects_nonsense(kwargs):
    with pytest.raises(ValueError):
        RateLimiter(**kwargs)


def _error(status, body, headers=None):
    return error_from_response(
        status_code=status,
        url="https://x/api",
        body=body,
        headers=headers or {},
        transient_statuses={503},
        transient_codes={"ERR_MANTENIMIENTO_BBDD"},
    )


def test_error_carries_status_code_and_url():
    error = _error(400, '{"codigo": "ERR_VALIDACION", "error": "bad"}')
    assert type(error) is BDNSError
    assert (error.status_code, error.code, error.url) == (400, "ERR_VALIDACION", "https://x/api")
    assert str(error) == "ERR_VALIDACION: bad"
    assert "HTTP 400 from https://x/api" in error.details


def test_several_messages_are_numbered():
    error = _error(400, '{"codigo": "E", "errores": ["a", "b"]}')
    assert error.message == "E:\n  1. a\n  2. b"


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (404, "", "HTTP 404: Not Found"),
        (500, "<html>", "HTTP 500: Server error"),
        (418, "teapot", "HTTP 418: teapot"),
    ],
)
def test_message_without_an_error_document(status, body, expected):
    assert _error(status, body).message == expected


def test_transient_by_status_or_by_code():
    assert isinstance(_error(503, ""), BDNSTransientError)
    assert isinstance(
        _error(200, '{"codigo": "ERR_MANTENIMIENTO_BBDD", "error": "x"}'), BDNSTransientError
    )
    assert _error(503, "", {"Retry-After": "3"}).retry_after == 3.0
