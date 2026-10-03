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
