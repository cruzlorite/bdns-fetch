import pytest
import requests

from bdns.fetch import BDNSClient, BDNSError, BDNSTransientError
from tests.conftest import endpoint

SECTORES = endpoint("sectores")
DOC = endpoint("convocatorias/documentos")
OK = [{"id": 1}]


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_retryable_status_is_retried(mocked, client, status):
    mocked.get(SECTORES, status=status)
    mocked.get(SECTORES, json=OK)
    assert list(client.fetch_sectores()) == OK
    assert len(mocked.calls) == 2


def test_maintenance_error_code_is_retried_whatever_the_status(mocked, client):
    mocked.get(SECTORES, status=200, json={"codigo": "ERR_MANTENIMIENTO_BBDD", "error": "x"})
    mocked.get(SECTORES, json=OK)
    assert list(client.fetch_sectores()) == OK


def test_connection_error_is_retried(mocked, client):
    mocked.get(SECTORES, body=requests.ConnectionError("reset"))
    mocked.get(SECTORES, json=OK)
    assert list(client.fetch_sectores()) == OK


def test_client_error_is_not_retried(mocked, client):
    mocked.get(SECTORES, status=400, json={"codigo": "ERR_VALIDACION", "error": "bad"})
    with pytest.raises(BDNSError) as excinfo:
        list(client.fetch_sectores())
    assert not isinstance(excinfo.value, BDNSTransientError)
    assert "ERR_VALIDACION" in excinfo.value.message
    assert len(mocked.calls) == 1


def test_error_payload_in_a_200_is_raised(mocked, client):
    mocked.get(SECTORES, status=200, json={"codigo": "ERR_VALIDACION", "error": "bad"})
    with pytest.raises(BDNSError, match="API returned error"):
        list(client.fetch_sectores())


def test_max_retries_counts_retries_after_the_first_attempt(mocked):
    mocked.get(SECTORES, status=503)
    with pytest.raises(BDNSTransientError):
        list(BDNSClient(max_retries=2, wait_time=0).fetch_sectores())
    assert len(mocked.calls) == 3


def test_zero_retries_means_one_attempt(mocked):
    mocked.get(SECTORES, status=503)
    with pytest.raises(BDNSTransientError):
        list(BDNSClient(max_retries=0).fetch_sectores())
    assert len(mocked.calls) == 1


def test_exhausted_retries_raise_the_last_error_not_a_tenacity_wrapper(mocked):
    mocked.get(SECTORES, body=requests.ConnectionError("down"))
    with pytest.raises(requests.ConnectionError):
        list(BDNSClient(max_retries=1, wait_time=0).fetch_sectores())


def test_backoff_grows_exponentially(mocked, no_retry_sleep):
    mocked.get(SECTORES, status=503)
    with pytest.raises(BDNSTransientError):
        list(BDNSClient(max_retries=3, wait_time=1).fetch_sectores())
    # initial * 2^n plus up to `wait_time` of jitter: [1, 2), [2, 3), [4, 5)
    assert [int(w) for w in no_retry_sleep] == [1, 2, 4]


def test_retry_after_header_is_honoured(mocked, client, no_retry_sleep):
    mocked.get(SECTORES, status=429, headers={"Retry-After": "7"})
    mocked.get(SECTORES, json=OK)
    list(client.fetch_sectores())
    assert no_retry_sleep == [7.0]


def test_binary_endpoints_retry_too(mocked, client):
    mocked.get(DOC, status=503)
    mocked.get(DOC, body=b"%PDF-1.5")
    assert client.fetch_convocatorias_documentos(idDocumento=1) == b"%PDF-1.5"


def test_binary_not_found_is_an_error(mocked, client):
    mocked.get(DOC, status=404)
    with pytest.raises(BDNSError):
        client.fetch_convocatorias_documentos(idDocumento=1)
    assert len(mocked.calls) == 1


@pytest.mark.parametrize("kwargs", [{"max_retries": -1}, {"max_workers": 0}])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        BDNSClient(**kwargs)
