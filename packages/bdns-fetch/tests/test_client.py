import inspect
import re
from datetime import date

import pytest

from bdns.fetch import BDNSClient, DescripcionTipoBusqueda, Order, TipoAdministracion
from tests.conftest import endpoint, paginated, query_of


def test_query_parameters_are_encoded_the_way_the_api_expects(mocked, client):
    mocked.add_callback("GET", endpoint("concesiones/busqueda"), callback=paginated(1))
    list(
        client.fetch_concesiones_busqueda(
            fechaDesde=date(2024, 1, 31),
            order=Order.importe,
            tipoAdministracion=TipoAdministracion.A,
            descripcionTipoBusqueda=DescripcionTipoBusqueda.todas,
            organos=[1, 2],
            nifCif=None,
        )
    )
    query = query_of(mocked.calls[0])
    assert query["fechaDesde"] == ["31/01/2024"]
    assert query["order"] == ["importe"]
    assert query["tipoAdministracion"] == ["A"]
    assert query["descripcionTipoBusqueda"] == ["1"]
    assert query["organos"] == ["1", "2"]
    assert "nifCif" not in query
    assert query["vpd"] == ["GE"]


def test_list_responses_yield_their_items(mocked, client):
    mocked.get(endpoint("sectores"), json=[{"id": 1}, {"id": 2}])
    assert list(client.fetch_sectores()) == [{"id": 1}, {"id": 2}]


def test_object_responses_yield_the_object(mocked, client):
    mocked.get(endpoint("convocatorias"), json={"id": 7})
    assert list(client.fetch_convocatorias(numConv="123")) == [{"id": 7}]


def test_required_parameters_have_no_default(client):
    with pytest.raises(TypeError, match="idAdmon"):
        client.fetch_organos()


def test_endpoint_parameters_are_keyword_only(client):
    with pytest.raises(TypeError):
        client.fetch_organos("GE", TipoAdministracion.C)


def test_every_endpoint_parameter_is_keyword_only():
    for name, method in inspect.getmembers(BDNSClient, inspect.isfunction):
        if name.startswith("fetch_"):
            for param in list(inspect.signature(method).parameters.values())[1:]:
                assert param.kind is inspect.Parameter.KEYWORD_ONLY, (name, param.name)


def test_requests_identify_the_client(mocked, client):
    mocked.get(endpoint("sectores"), json=[])
    list(client.fetch_sectores())
    assert mocked.calls[0].request.headers["User-Agent"].startswith("bdns-fetch/")


def test_connections_are_reused_within_a_thread(client):
    assert client._session() is client._session()


def _dummy(annotation):
    if annotation is TipoAdministracion:
        return TipoAdministracion.C
    return 1 if annotation is int else "x"


@pytest.mark.parametrize("name", [n for n in dir(BDNSClient) if n.startswith("fetch_")])
def test_each_method_requests_the_path_its_docstring_names(mocked, client, name):
    method = getattr(client, name)
    path = re.search(r"\(`(/[^`]+)`\)", method.__doc__).group(1)
    required = {
        p.name: _dummy(p.annotation)
        for p in inspect.signature(method).parameters.values()
        if p.default is inspect.Parameter.empty
    }
    mocked.get(re.compile(r".*"), json={"content": [], "totalPages": 1})
    result = method(**required)
    if not isinstance(result, bytes):
        list(result)
    requested = mocked.calls[0].request.url.split("/bdnstrans/api", 1)[1].split("?")[0]
    assert requested == path


def test_get_requests_any_path_with_encoded_params(mocked, client):
    mocked.get(endpoint("vpd/GE/configuracion"), json={"titulo": "x"})
    assert client.get("/vpd/GE/configuracion", {"fecha": date(2024, 1, 2), "x": None}) == {
        "titulo": "x"
    }
    assert query_of(mocked.calls[0]) == {"fecha": ["02/01/2024"]}


def test_get_returns_none_on_204(mocked, client):
    mocked.get(endpoint("sectores"), status=204)
    assert client.get("/sectores") is None


def test_get_bytes(mocked, client):
    mocked.get(endpoint("convocatorias/pdf"), body=b"%PDF")
    assert client.get_bytes("convocatorias/pdf", {"id": 1}) == b"%PDF"


def test_errors_carry_status_code_and_api_code(mocked, client):
    from bdns.fetch import BDNSError

    mocked.get(endpoint("sectores"), status=400, json={"codigo": "ERR_VALIDACION", "error": "x"})
    with pytest.raises(BDNSError) as excinfo:
        client.get("/sectores")
    assert excinfo.value.status_code == 400
    assert excinfo.value.code == "ERR_VALIDACION"
    assert excinfo.value.url.endswith("/sectores?")


def test_a_given_rate_limiter_is_used(mocked):
    class Counting:
        calls = 0

        def acquire(self):
            Counting.calls += 1

    mocked.get(endpoint("sectores"), json=[])
    list(BDNSClient(rate_limiter=Counting()).fetch_sectores())
    assert Counting.calls == 1


def test_base_url_is_configurable(mocked):
    mocked.get("https://mirror.example/api/sectores", json=[{"id": 1}])
    assert list(BDNSClient(base_url="https://mirror.example/api/").fetch_sectores()) == [{"id": 1}]


def test_constructor_takes_keywords_only():
    with pytest.raises(TypeError):
        BDNSClient(3)
