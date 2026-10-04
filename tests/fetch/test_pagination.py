import logging
import time

from bdns.fetch import BDNSClient
from tests.fetch.conftest import endpoint, page, paginated, query_of

SEARCH = endpoint("concesiones/busqueda")


def ids(records):
    return [record["id"] for record in records]


def test_all_pages_by_default(mocked, client):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=5))
    assert ids(client.fetch_concesiones_busqueda()) == list(range(10))


def test_pages_are_yielded_in_order_even_when_they_complete_out_of_order(mocked):
    # Earlier pages answer slower, so they finish last.
    mocked.add_callback(
        "GET", SEARCH, callback=paginated(total_pages=8, delay=lambda n: time.sleep((8 - n) / 200))
    )
    client = BDNSClient(max_workers=4, progress=False)
    assert ids(client.fetch_concesiones_busqueda()) == list(range(16))


def test_num_pages_limits_and_warns(mocked, client, caplog):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=5))
    with caplog.at_level(logging.WARNING, logger="bdns.fetch"):
        records = list(client.fetch_concesiones_busqueda(num_pages=2))
    assert ids(records) == [0, 1, 2, 3]
    assert "Returning pages 0 to 1 of 5" in caplog.text


def test_from_page_offsets_the_range(mocked, client):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=5))
    assert ids(client.fetch_concesiones_busqueda(from_page=3)) == [6, 7, 8, 9]


def test_no_warning_when_every_page_is_returned(mocked, client, caplog):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=2))
    with caplog.at_level(logging.WARNING, logger="bdns.fetch"):
        list(client.fetch_concesiones_busqueda(num_pages=5))
    assert caplog.text == ""


def test_pages_yields_whole_page_documents(mocked, client):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=3))
    pages = list(client.pages("/concesiones/busqueda", {"pageSize": 2}))
    assert pages == [page(0, 3), page(1, 3), page(2, 3)]


def test_stopping_early_does_not_download_every_page(mocked):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=1000))
    client = BDNSClient(max_workers=2, progress=False)
    records = client.fetch_concesiones_busqueda()
    for record in records:
        if record["id"] == 3:  # second page
            break
    records.close()
    # First page, plus at most the in-flight window (2 * workers) and one refill.
    assert len(mocked.calls) <= 1 + 2 * 2 + 1


def test_empty_answer_is_an_empty_result(mocked, client):
    mocked.get(SEARCH, status=204)
    assert list(client.fetch_concesiones_busqueda()) == []


def test_page_size_and_page_are_sent(mocked, client):
    mocked.add_callback("GET", SEARCH, callback=paginated(total_pages=2))
    list(client.fetch_concesiones_busqueda(pageSize=50))
    assert [query_of(call)["page"] for call in mocked.calls] == [["0"], ["1"]]
    assert query_of(mocked.calls[0])["pageSize"] == ["50"]
