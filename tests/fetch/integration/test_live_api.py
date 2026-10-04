"""Live tests against the real BDNS API.

Excluded from the default run (`-m "not integration"` in pytest.ini) so CI
does not depend on a third-party service. They run nightly, and on demand
with `make test-integration`.

Identifiers are discovered from the API itself rather than hard-coded:
documents and calls get withdrawn, and a fixed ID turns a passing suite
into a failing one without any change on our side.
"""

from datetime import date, timedelta

import pytest
from typer.testing import CliRunner

from bdns.fetch import Ambito, BDNSClient, TipoAdministracion
from bdns.fetch.cli import app

pytestmark = pytest.mark.integration

PAGE = {"pageSize": 10, "num_pages": 1}
RECENT = {"fechaDesde": date.today() - timedelta(days=30), "fechaHasta": date.today()}


@pytest.fixture(scope="module")
def client():
    return BDNSClient(progress=False)


@pytest.fixture(scope="module")
def convocatoria(client):
    """Detail of a recent call that has at least one attached document."""
    for item in client.fetch_convocatorias_busqueda(pageSize=50, num_pages=1):
        detail = next(client.fetch_convocatorias(numConv=item["numeroConvocatoria"]))
        if detail.get("documentos"):
            return {**detail, "id": item["id"]}
    pytest.skip("no recent call with documents")


@pytest.fixture(scope="module")
def plan(client):
    """Detail of a strategic plan that has at least one attached document."""
    for item in client.fetch_planesestrategicos_busqueda(pageSize=50, num_pages=1):
        detail = next(client.fetch_planesestrategicos(idPES=item["id"]), {})
        if detail.get("documentos"):
            return {**detail, "id": item["id"]}
    pytest.skip("no strategic plan with documents")


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("fetch_actividades", {}),
        ("fetch_sectores", {}),
        ("fetch_regiones", {}),
        ("fetch_finalidades", {}),
        ("fetch_beneficiarios", {}),
        ("fetch_instrumentos", {}),
        ("fetch_objetivos", {}),
        ("fetch_reglamentos", {"ambito": Ambito.C}),
        ("fetch_grandesbeneficiarios_anios", {}),
        ("fetch_organos", {"idAdmon": TipoAdministracion.C}),
        ("fetch_organos_agrupacion", {"idAdmon": TipoAdministracion.L}),
        ("fetch_organos_codigo", {"codigo": "L02000034"}),
        ("fetch_organos_codigoadmin", {"codigoAdmin": "C31"}),
        ("fetch_convocatorias_ultimas", {}),
        ("fetch_terceros", {"vpd": "A02", "ambito": Ambito.C, "busqueda": "asociacion"}),
        ("fetch_convocatorias_busqueda", {**PAGE, **RECENT}),
        ("fetch_concesiones_busqueda", {**PAGE, **RECENT}),
        ("fetch_ayudasestado_busqueda", {**PAGE, "fechaDesde": date(2024, 1, 1)}),
        ("fetch_minimis_busqueda", {**PAGE, "fechaDesde": date(2024, 1, 1)}),
        ("fetch_partidospoliticos_busqueda", {**PAGE, "fechaDesde": date(2020, 1, 1)}),
        ("fetch_sanciones_busqueda", PAGE),
        ("fetch_planesestrategicos_busqueda", PAGE),
        ("fetch_grandesbeneficiarios_busqueda", {**PAGE, "anios": [2023]}),
    ],
)
def test_endpoint_returns_records(client, method, kwargs):
    records = list(getattr(client, method)(**kwargs))
    assert records, f"{method} returned nothing"
    assert all(isinstance(record, dict) for record in records)


def test_pages_are_consecutive(client):
    """Two pages of 5 are the first 10 records of one page of 10, in order."""
    params = {
        "fechaDesde": date(2024, 1, 1),
        "fechaHasta": date(2024, 1, 31),
        "order": "codConcesion",
    }
    paged = list(client.fetch_concesiones_busqueda(pageSize=5, num_pages=2, **params))
    single = list(client.fetch_concesiones_busqueda(pageSize=10, num_pages=1, **params))
    assert [r["id"] for r in paged] == [r["id"] for r in single]


def test_convocatorias_documentos(client, convocatoria):
    document_id = convocatoria["documentos"][0]["id"]
    assert client.fetch_convocatorias_documentos(idDocumento=document_id)


def test_convocatorias_pdf(client, convocatoria):
    assert client.fetch_convocatorias_pdf(id=convocatoria["id"], vpd="GE").startswith(b"%PDF")


def test_planesestrategicos_vigencia(client, plan):
    assert list(client.fetch_planesestrategicos_vigencia(idPES=plan["id"]))


def test_planesestrategicos_documentos(client, plan):
    document_id = plan["documentos"][0]["id"]
    assert client.fetch_planesestrategicos_documentos(idDocumento=document_id)


def test_cli_end_to_end():
    result = CliRunner().invoke(app, ["--no-progress", "sectores"])
    assert result.exit_code == 0, result.output
    assert result.stdout.strip()


def test_documented_date_semantics_still_hold(client):
    from bdns.fetch.contract import check_api_contract

    report = check_api_contract(client)
    assert report.status != "changed", report.messages
