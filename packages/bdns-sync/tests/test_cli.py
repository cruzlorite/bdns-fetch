import re

from typer.testing import CliRunner

from bdns.sync.cli import app

runner = CliRunner()


def plain(result) -> str:
    """`result.output` without ANSI escapes and with whitespace collapsed.

    On CI, rich colors the error box and wraps it to the terminal width,
    which splits the message with escape codes and newlines. Asserting on
    the raw output makes tests pass locally and fail there.
    """
    text = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    return " ".join(text.split())


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "bdns-sync" in plain(result)


def test_list_full_includes_known_endpoints():
    result = runner.invoke(app, ["list", "--kind", "full"])
    assert result.exit_code == 0
    assert "sectores" in plain(result)
    assert "organos" in plain(result)


def test_list_search_includes_known_endpoints():
    result = runner.invoke(app, ["list", "--kind", "search"])
    assert result.exit_code == 0
    assert "concesiones_busqueda" in plain(result)
    assert "convocatorias" in plain(result)


def test_list_rejects_unknown_kind():
    result = runner.invoke(app, ["list", "--kind", "bogus"])
    assert result.exit_code != 0


def test_sync_rejects_unknown_endpoint():
    result = runner.invoke(app, ["sync", "not_a_real_endpoint", "--target-url", "sqlite:///:memory:"])
    assert result.exit_code != 0


def test_sync_incremental_endpoint_requires_window_or_since():
    result = runner.invoke(
        app, ["sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:"]
    )
    assert result.exit_code != 0
    assert "requires --window or --since" in plain(result)


def test_sync_rejects_window_and_since_together():
    result = runner.invoke(
        app,
        [
            "sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:",
            "--window", "daily", "--since", "2020-01-01",
        ],
    )
    assert result.exit_code != 0
    assert "not both" in plain(result)


def test_sync_rejects_non_iso_since():
    result = runner.invoke(
        app,
        ["sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:", "--since", "01/01/2020"],
    )
    assert result.exit_code != 0
    assert "ISO date" in plain(result)


def test_sync_rejects_until_before_since():
    result = runner.invoke(
        app,
        [
            "sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:",
            "--since", "2020-06-01", "--until", "2020-01-01",
        ],
    )
    assert result.exit_code != 0
    assert "must not be before" in plain(result)


def test_sync_convocatorias_requires_window():
    result = runner.invoke(app, ["sync", "convocatorias", "--target-url", "sqlite:///:memory:"])
    assert result.exit_code != 0


def test_sync_rejects_unknown_window():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--target-url",
            "sqlite:///:memory:",
            "--window",
            "bogus",
        ],
    )
    assert result.exit_code != 0
