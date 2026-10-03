import time
from datetime import date
from urllib.parse import parse_qs, urlsplit

import pytest

from bdns.fetch import TipoAdministracion, format_date_for_api_request, format_url
from bdns.fetch.exceptions import (
    BDNSError,
    handle_api_response,
    parse_bdns_error_response,
)
from bdns.fetch.utils import RateLimiter


def test_format_date():
    assert format_date_for_api_request(date(2024, 1, 31)) == "31/01/2024"
    assert format_date_for_api_request(None) is None
    with pytest.raises(ValueError):
        format_date_for_api_request("2024-01-31")


def test_format_url_drops_none_unwraps_enums_and_repeats_lists():
    url = format_url("https://x/api", {"a": None, "b": TipoAdministracion.L, "c": [1, 2], "d": "é"})
    query = parse_qs(urlsplit(url).query)
    assert query == {"b": ["L"], "c": ["1", "2"], "d": ["é"]}


def test_rate_limiter_spaces_out_calls_beyond_the_burst():
    limiter = RateLimiter(rate=5, per=0.5)
    start = time.monotonic()
    for _ in range(10):  # 5 from the full bucket, then 5 more at 10/s
        limiter.acquire()
    assert time.monotonic() - start >= 0.45


def test_parse_error_body():
    assert parse_bdns_error_response('{"codigo": "E1", "errores": ["a", "b"]}') == (
        "E1",
        ["a", "b"],
    )
    assert parse_bdns_error_response("<html>")[0] == "PARSE_ERROR"


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 418])
def test_handle_api_response_builds_an_error(status):
    error = handle_api_response(status, "https://x", '{"codigo": "E", "error": "boom"}')
    assert isinstance(error, BDNSError)
    assert "boom" in error.message
    assert f"HTTP {status}" in error.technical_details
