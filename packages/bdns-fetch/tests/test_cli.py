import inspect
import json
from datetime import date

import click
import pytest
from typer.testing import CliRunner

from bdns.fetch import BDNSClient
from bdns.fetch.cli import app
from bdns.fetch.options import CLI_DEFAULTS, DATE, PARAMETERS
from tests.conftest import endpoint, paginated, query_of


@pytest.fixture
def runner():
    try:
        return CliRunner(mix_stderr=False)
    except TypeError:  # Click >= 8.2 always keeps stderr apart
        return CliRunner()


def run(runner, *args):
    return runner.invoke(app, ["--no-progress", *args])


def endpoint_methods():
    return [name for name in dir(BDNSClient) if name.startswith("fetch_")]


def test_help_lists_every_endpoint(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in endpoint_methods():
        assert name.removeprefix("fetch_").replace("_", "-") in result.stdout


def test_every_client_parameter_has_a_flag():
    for name in endpoint_methods():
        params = list(inspect.signature(getattr(BDNSClient, name)).parameters)[1:]
        missing = [param for param in params if param not in PARAMETERS]
        assert not missing, f"{name}: no CLI spec for {missing}"


def test_version(runner):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.startswith("bdns-fetch ")


def test_records_are_written_as_json_lines(mocked, runner):
    mocked.get(endpoint("sectores"), json=[{"id": 1, "descripcion": "Agricultura"}, {"id": 2}])
    result = run(runner, "sectores")
    assert result.exit_code == 0, result.output
    lines = result.stdout.strip().split("\n")
    assert [json.loads(line) for line in lines] == [
        {"id": 1, "descripcion": "Agricultura"},
        {"id": 2},
    ]


def test_output_file(mocked, runner, tmp_path):
    mocked.get(endpoint("sectores"), json=[{"id": 1}])
    out = tmp_path / "sectores.jsonl"
    result = run(runner, "-o", str(out), "sectores")
    assert result.exit_code == 0, result.output
    assert out.read_text(encoding="utf-8") == '{"id": 1}\n'


def test_documents_are_written_as_bytes(mocked, runner, tmp_path):
    mocked.get(endpoint("convocatorias/pdf"), body=b"%PDF-1.5 binary")
    out = tmp_path / "c.pdf"
    result = run(runner, "-o", str(out), "convocatorias-pdf", "--id", "1", "--vpd", "GE")
    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"%PDF-1.5 binary"


def test_underscore_alias(mocked, runner):
    mocked.add_callback("GET", endpoint("concesiones/busqueda"), callback=paginated(1))
    assert run(runner, "concesiones_busqueda").exit_code == 0
    assert "concesiones_busqueda" not in runner.invoke(app, ["--help"]).stdout


def test_cli_fetches_one_page_by_default(mocked, runner):
    assert CLI_DEFAULTS["num_pages"] == 1
    mocked.add_callback("GET", endpoint("concesiones/busqueda"), callback=paginated(5))
    result = run(runner, "concesiones-busqueda")
    assert len(result.stdout.strip().split("\n")) == 2
    assert len(mocked.calls) == 1


def test_options_reach_the_query(mocked, runner):
    mocked.add_callback("GET", endpoint("concesiones/busqueda"), callback=paginated(1))
    result = run(
        runner,
        "concesiones-busqueda",
        "--fechaDesde",
        "2024-01-31",
        "--organos",
        "1",
        "--organos",
        "2",
        "--tipoAdministracion",
        "A",
    )
    assert result.exit_code == 0, result.output
    query = query_of(mocked.calls[0])
    assert query["fechaDesde"] == ["31/01/2024"]
    assert query["organos"] == ["1", "2"]
    assert query["tipoAdministracion"] == ["A"]


def test_missing_required_option_is_a_usage_error(runner):
    result = run(runner, "organos")
    assert result.exit_code == 2


def test_api_error_is_reported_without_traceback(mocked, runner):
    mocked.get(endpoint("sectores"), status=400, json={"codigo": "ERR_VALIDACION", "error": "bad"})
    result = run(runner, "sectores")
    assert result.exit_code == 1
    assert "Error: Error (ERR_VALIDACION): bad" in result.stderr
    assert "Traceback" not in result.output


def test_verbose_error_shows_response_details(mocked, runner):
    mocked.get(endpoint("sectores"), status=400, json={"codigo": "ERR_VALIDACION", "error": "bad"})
    result = run(runner, "--verbose", "sectores")
    assert "HTTP 400 from" in result.stderr


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-02-01", date(2024, 2, 1)),
        ("01/02/2024", date(2024, 2, 1)),  # day first, as written in Spain
        ("1-2-2024", date(2024, 2, 1)),
    ],
)
def test_date_parsing(text, expected):
    assert DATE.convert(text, None, None) == expected


@pytest.mark.parametrize("text", ["not a date", "two weeks ago", "31/02/2024", "2024/01/31"])
def test_anything_else_is_a_usage_error(text):
    with pytest.raises(click.BadParameter):
        DATE.convert(text, None, None)


def test_rate_limited_error_suggests_lowering_the_rate(mocked, runner):
    mocked.get(endpoint("sectores"), status=429)
    result = run(runner, "--max-retries", "0", "sectores")
    assert result.exit_code == 1
    assert "--rate-limit" in result.stderr


def test_get_command_requests_any_path(mocked, runner):
    mocked.get(endpoint("vpd/GE/configuracion"), json={"titulo": "Portal"})
    result = run(runner, "get", "/vpd/GE/configuracion", "-p", "a=1", "-p", "a=2")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"titulo": "Portal"}
    assert query_of(mocked.calls[0]) == {"a": ["1", "2"]}


def test_get_command_rejects_a_malformed_param(runner):
    assert run(runner, "get", "/x", "-p", "novalue").exit_code == 2


@pytest.mark.parametrize(("status", "code"), [("ok", 0), ("inconclusive", 0), ("changed", 1)])
def test_check_api_exit_code(monkeypatch, runner, status, code):
    from bdns.fetch.contract import ContractReport

    monkeypatch.setattr(
        "bdns.fetch.cli.check_api_contract", lambda client, day: ContractReport(status, ["msg"])
    )
    result = run(runner, "check-api", "--day", "2024-01-31")
    assert result.exit_code == code
    assert "msg" in result.stdout
