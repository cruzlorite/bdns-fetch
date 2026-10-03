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
    result = runner.invoke(
        app, ["sync", "not_a_real_endpoint", "--target-url", "sqlite:///:memory:"]
    )
    assert result.exit_code != 0


def test_sync_incremental_endpoint_requires_window_or_since():
    result = runner.invoke(
        app, ["sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:"]
    )
    assert result.exit_code != 0
    assert "needs --window or --since" in plain(result)


def test_sync_rejects_window_and_since_together():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--target-url",
            "sqlite:///:memory:",
            "--window",
            "daily",
            "--since",
            "2020-01-01",
        ],
    )
    assert result.exit_code != 0
    assert "not both" in plain(result)


def test_sync_rejects_non_iso_since():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--target-url",
            "sqlite:///:memory:",
            "--since",
            "01/01/2020",
        ],
    )
    assert result.exit_code != 0
    assert "ISO date" in plain(result)


def test_sync_rejects_until_before_since():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--target-url",
            "sqlite:///:memory:",
            "--since",
            "2020-06-01",
            "--until",
            "2020-01-01",
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


# --- dry run ---------------------------------------------------------------
#
# Its whole value is that it previews the invocation you are about to run,
# so it resolves through the same validation and the same date arithmetic
# and then stops before touching the API or the target.


def test_dry_run_resolves_a_window_to_concrete_dates_and_chunks():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--window",
            "monthly",
            "--target-url",
            "sqlite:///:memory:",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    output = plain(result)
    assert "run type monthly" in output
    assert "30 day(s), 5 chunk(s) of at most 7" in output


def test_dry_run_shows_the_policy_that_would_apply():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones_busqueda",
            "--window",
            "daily",
            "--target-url",
            "sqlite:///:memory:",
            "--dry-run",
        ],
    )
    assert "hash_exclude=['beneficiario']" in plain(result)


def test_dry_run_of_a_full_catalog_reports_no_date_range():
    result = runner.invoke(
        app, ["sync", "sectores", "--target-url", "sqlite:///:memory:", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "complete state, no date range" in plain(result)


def test_dry_run_hides_the_target_password():
    """This output goes to a terminal and, from a script, into a log."""
    result = runner.invoke(
        app,
        ["sync", "sectores", "--target-url", "postgresql://user:hunter2@host/db", "--dry-run"],
    )
    assert "hunter2" not in plain(result)
    assert "***" in plain(result)


def test_dry_run_touches_neither_the_api_nor_the_target(tmp_path):
    db = tmp_path / "should-not-exist.db"
    result = runner.invoke(
        app, ["sync", "sectores", "--target-url", f"sqlite:///{db}", "--dry-run"]
    )
    assert result.exit_code == 0
    assert not db.exists()


def test_dry_run_still_rejects_an_invalid_invocation():
    """A preview that accepted what the real run rejects would be worse than
    no preview at all.
    """
    result = runner.invoke(
        app, ["sync", "concesiones_busqueda", "--target-url", "sqlite:///:memory:", "--dry-run"]
    )
    assert result.exit_code != 0
    assert "needs --window or --since" in plain(result)


def test_dry_run_rejects_an_unknown_endpoint():
    result = runner.invoke(
        app, ["sync", "not_a_real_endpoint", "--target-url", "sqlite:///:memory:", "--dry-run"]
    )
    assert result.exit_code != 0


def test_endpoint_accepts_the_hyphenated_name_bdns_fetch_uses():
    result = runner.invoke(
        app,
        [
            "sync",
            "concesiones-busqueda",
            "--window",
            "daily",
            "--dry-run",
            "--target-url",
            "sqlite://",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "concesiones_busqueda" in plain(result)


# --- delta / backfill ---------------------------------------------------------

TARGET = ["--target-url", "sqlite:///:memory:"]


def test_delta_dry_run_lists_every_entity():
    result = runner.invoke(app, ["delta", "--dry-run", *TARGET])
    assert result.exit_code == 0, result.output
    assert "22 sync(s) planned" in plain(result)
    assert "sectores: complete state" in plain(result)


def test_delta_refuses_an_unknown_window():
    assert runner.invoke(app, ["delta", "--window", "hourly", "--dry-run", *TARGET]).exit_code == 2


def test_delta_syncs_nothing_when_the_api_changed(monkeypatch):
    from bdns.fetch.contract import ContractReport

    ran = []
    monkeypatch.setattr(
        "bdns.sync.cli.check_api_contract", lambda client: ContractReport("changed", ["moved"])
    )
    monkeypatch.setattr("bdns.sync.cli.run_plan", lambda *a: ran.append(a) or [])
    result = runner.invoke(app, ["delta", *TARGET])
    assert result.exit_code == 1
    assert ran == []


def test_delta_runs_the_plan_and_fails_if_any_step_failed(monkeypatch):
    from bdns.fetch.contract import ContractReport
    from bdns.sync.orchestration import StepResult

    def fake_run(steps, sink, client):
        return [StepResult(steps[0], error="boom")] + [
            StepResult(s, stats=__import__("bdns.sync.sinks", fromlist=["SyncStats"]).SyncStats())
            for s in steps[1:]
        ]

    monkeypatch.setattr(
        "bdns.sync.cli.check_api_contract", lambda client: ContractReport("ok", ["fine"])
    )
    monkeypatch.setattr("bdns.sync.cli.run_plan", fake_run)
    result = runner.invoke(app, ["delta", *TARGET])
    assert result.exit_code == 1
    assert "1 of 22 sync(s) failed" in plain(result)


def test_delta_end_to_end_with_the_fake_api(monkeypatch, tmp_path):
    from tests.fake_client import FakeBDNSClient

    monkeypatch.setattr("bdns.sync.cli._client", lambda *a: FakeBDNSClient())
    url = f"sqlite:///{tmp_path / 'bdns.db'}"
    result = runner.invoke(
        app, ["delta", "--skip-api-check", "--window", "daily", "--target-url", url]
    )
    assert result.exit_code == 0, result.output
    assert "all 22 sync(s) succeeded" in plain(result)


def test_backfill_dry_run_for_one_entity():
    result = runner.invoke(app, ["backfill", "--entity", "convocatorias", "--dry-run", *TARGET])
    assert result.exit_code == 0, result.output
    assert "convocatorias: backfill [2013-01-01 .. 2013-12-31]" in plain(result)


def test_backfill_rejects_an_unknown_entity():
    assert runner.invoke(app, ["backfill", "--entity", "nope", "--dry-run", *TARGET]).exit_code == 2


def test_sync_full_entity_rejects_a_range():
    result = runner.invoke(app, ["sync", "sectores", "--window", "daily", "--dry-run", *TARGET])
    assert result.exit_code == 2
    assert "takes no range" in plain(result)


def test_list_without_kind_lists_all_and_rejects_bad_kind():
    assert len(runner.invoke(app, ["list"]).output.split()) == 22
    assert runner.invoke(app, ["list", "--kind", "bogus"]).exit_code == 2


def test_check_api_exit_code(monkeypatch):
    from bdns.fetch.contract import ContractReport

    for status, code in (("ok", 0), ("inconclusive", 0), ("changed", 1)):
        monkeypatch.setattr(
            "bdns.sync.cli.check_api_contract",
            lambda client, day, s=status: ContractReport(s, ["m"]),
        )
        assert runner.invoke(app, ["check-api", "--day", "2024-01-31"]).exit_code == code
