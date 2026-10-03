# SPDX-License-Identifier: MIT

"""The `bdns-sync` command line.

`sync` runs one entity. `delta` and `backfill` run a plan of many, built
from the entity registry ([`orchestration`][bdns.sync.orchestration]):
the daily incremental run and the historical load. Every command that
writes takes `--dry-run`, which prints what it would do without touching
the API or the target, through the same code path as a real run.

Configuration is flags, each with an environment variable for unattended
use; there is no configuration file.
"""

import logging
from datetime import date

import typer
from sqlalchemy.engine import make_url

from bdns.fetch import BDNSClient, RateLimiter
from bdns.fetch.contract import check_api_contract
from bdns.fetch.dates import MAX_RANGE_DAYS, split_range
from bdns.sync import __version__
from bdns.sync.entities import ENTITIES, Entity, get_entity, sync_entity
from bdns.sync.orchestration import Step, StepResult, backfill_plan, delta_plan, run_plan
from bdns.sync.sinks import DEFAULT_LIMITS, RejectLimits, SyncStats, get_sink
from bdns.sync.windows import WINDOWS, resolve_when

__all__ = ["app"]

app = typer.Typer(
    name="bdns-sync",
    help="Keep a target database in SCD2 form from the BDNS API.",
    add_completion=False,
    # Typer dumps every frame's local variables into the traceback by
    # default. This tool runs unattended and its locals hold payload
    # fragments (beneficiary names, identifiers) and the target URL,
    # password included. The traceback itself is kept.
    pretty_exceptions_show_locals=False,
)


def _version_callback(value: bool) -> None:
    """Print the version and exit, when `--version` was passed."""
    if value:
        typer.echo(f"bdns-sync {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """BDNS Sync command line interface.

    Configures logging here rather than in `__main__.py`: the installed
    console script calls the Typer app directly, so this callback is the
    one place guaranteed to run.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )


# --- options shared by several commands -------------------------------------

TARGET_URL = typer.Option(
    ...,
    "--target-url",
    envvar="BDNS_SYNC_TARGET_URL",
    help="SQLAlchemy URL of the target database (e.g. bigquery://project/dataset).",
)
MAX_RETRIES = typer.Option(
    5,
    "--max-retries",
    envvar="BDNS_SYNC_MAX_RETRIES",
    min=0,
    help="Retries per request for transient API failures.",
)
WAIT_TIME = typer.Option(
    10.0,
    "--wait-time",
    envvar="BDNS_SYNC_WAIT_TIME",
    min=0,
    help="Initial seconds between retries; doubles on each, up to 60. "
    "With the defaults a request rides out about 3-4 minutes of trouble.",
)
RATE_LIMIT = typer.Option(
    9.5,
    "--rate-limit",
    envvar="BDNS_SYNC_RATE_LIMIT",
    min=0.1,
    max=10,
    help="API requests per second. The limit is per IP: lower it if other processes share yours.",
)
MAX_REJECT_RATIO = typer.Option(
    DEFAULT_LIMITS.max_ratio,
    "--max-reject-ratio",
    min=0.0,
    max=1.0,
    help="Share of a batch that may be unusable before the run refuses it (0.10 = 10%).",
)
MAX_REJECTS = typer.Option(
    None,
    "--max-rejects",
    min=0,
    help="Absolute cap on unusable records per batch, whatever the share. Unset by default.",
)
DRY_RUN = typer.Option(
    False,
    "--dry-run",
    help="Print what would be done, then stop. Touches neither the API nor the target.",
)


def _client(max_retries: int, wait_time: float, rate_limit: float) -> BDNSClient:
    """Build the API client a run uses."""
    return BDNSClient(
        max_retries=max_retries, wait_time=wait_time, rate_limiter=RateLimiter(rate=rate_limit)
    )


def _parse_iso_date(value: str | None, flag: str) -> date | None:
    """Parse an ISO date option, reporting a bad one as a usage error.

    Raises:
        typer.BadParameter: If `value` is not an ISO date.
    """
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(
            f"{flag} must be an ISO date (YYYY-MM-DD), got {value!r}"
        ) from None


def _entity_option(value: str) -> Entity:
    """Resolve an entity name, accepting hyphens, as a usage error if unknown."""
    try:
        return get_entity(value)
    except KeyError:
        raise typer.BadParameter(
            f"unknown entity {value!r}; `bdns-sync list` shows them all"
        ) from None


def _safe_url(target_url: str) -> str:
    """The target URL with its password hidden, for terminals and logs."""
    return make_url(target_url).render_as_string(hide_password=True)


def _summary(stats: SyncStats) -> str:
    """One-line rendering of a run's counters."""
    return (
        f"fetched={stats.fetched} new={stats.new} changed={stats.changed} "
        f"unchanged={stats.unchanged} removed={stats.removed} skipped={stats.skipped}"
    )


def _report(results: list[StepResult]) -> None:
    """Print one line per step and exit 1 if any failed."""
    failed = [r for r in results if not r.ok]
    for result in results:
        if result.ok:
            typer.echo(f"ok      {result.step.entity.name:<32} {_summary(result.stats)}")
        else:
            typer.echo(f"FAILED  {result.step.entity.name:<32} {result.error}", err=True)
    if failed:
        typer.echo(f"{len(failed)} of {len(results)} sync(s) failed", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"all {len(results)} sync(s) succeeded")


def _echo_steps(target_url: str, steps: list[Step], limits: RejectLimits) -> None:
    """Print a plan without running it."""
    typer.echo(f"target      {_safe_url(target_url)}")
    typer.echo(f"limits      {limits.describe()}")
    for step in steps:
        typer.echo(f"  {step.describe()}")
    typer.echo(f"dry run     {len(steps)} sync(s) planned; nothing fetched, nothing written")


# --- commands ------------------------------------------------------------------


@app.command()
def sync(
    entity_name: str = typer.Argument(
        ...,
        metavar="ENTITY",
        help="Entity to sync, as `bdns-sync list` names it. Hyphens and underscores are interchangeable.",
    ),
    target_url: str = TARGET_URL,
    window: str | None = typer.Option(
        None, "--window", help=f"Window for a windowed entity: {', '.join(WINDOWS)}."
    ),
    since: str | None = typer.Option(
        None, "--since", help="First day (YYYY-MM-DD) of an explicit range. Overrides --window."
    ),
    until: str | None = typer.Option(
        None, "--until", help="Last day (YYYY-MM-DD) of that range. Defaults to yesterday."
    ),
    max_retries: int = MAX_RETRIES,
    wait_time: float = WAIT_TIME,
    rate_limit: float = RATE_LIMIT,
    max_reject_ratio: float = MAX_REJECT_RATIO,
    max_rejects: int | None = MAX_REJECTS,
    dry_run: bool = DRY_RUN,
) -> None:
    """Sync one entity.

    A windowed entity needs a range: a named --window, or --since [--until]
    for a historical load. A full entity takes neither.
    """
    entity = _entity_option(entity_name)
    since_date = _parse_iso_date(since, "--since")
    until_date = _parse_iso_date(until, "--until")
    if entity.kind == "windowed":
        if since_date is not None:
            if window is not None:
                raise typer.BadParameter("use either --window or --since, not both")
            if until_date is not None and until_date < since_date:
                raise typer.BadParameter("--until must not be before --since")
        elif window is None:
            raise typer.BadParameter(f"{entity.name} needs --window or --since")
        elif window not in WINDOWS:
            raise typer.BadParameter(f"window must be one of {', '.join(WINDOWS)}")
    elif window or since_date or until_date:
        raise typer.BadParameter(f"{entity.name} is synced whole; it takes no range")
    limits = RejectLimits(max_ratio=max_reject_ratio, max_count=max_rejects)

    if dry_run:
        typer.echo(f"target      {_safe_url(target_url)}  ->  table {entity.name}")
        if entity.kind == "full":
            typer.echo("run type    full  (complete state, no date range)")
        else:
            start, end, run_type = resolve_when(window, since_date, until_date)
            chunks = sum(1 for _ in split_range(start, end))
            typer.echo(f"run type    {run_type}")
            typer.echo(
                f"range       {start} .. {end}  ({(end - start).days + 1} day(s), "
                f"{chunks} chunk(s) of at most {MAX_RANGE_DAYS})"
            )
        typer.echo(f"policy      {entity.policy.describe()}")
        typer.echo(f"limits      {limits.describe()}")
        typer.echo("dry run     nothing fetched, nothing written")
        return

    stats = sync_entity(
        entity,
        get_sink(target_url, limits),
        _client(max_retries, wait_time, rate_limit),
        window,
        since=since_date,
        until=until_date,
    )
    typer.echo(f"ok      {entity.name:<32} {_summary(stats)}")


@app.command()
def delta(
    target_url: str = TARGET_URL,
    window: str | None = typer.Option(
        None,
        "--window",
        help=f"Window for the windowed entities ({', '.join(WINDOWS)}). "
        "Defaults to the cadence: annual on 1 Jan, 1 May and 1 Sep, monthly on Mondays, weekly otherwise.",
    ),
    skip_api_check: bool = typer.Option(
        False, "--skip-api-check", help="Do not check the API's date semantics first."
    ),
    max_retries: int = MAX_RETRIES,
    wait_time: float = WAIT_TIME,
    rate_limit: float = RATE_LIMIT,
    max_reject_ratio: float = MAX_REJECT_RATIO,
    max_rejects: int | None = MAX_REJECTS,
    dry_run: bool = DRY_RUN,
) -> None:
    """Run the daily sync: every full entity, then every windowed one.

    Meant to run once a day from a scheduler. It first checks that the
    API's date semantics still hold, and syncs nothing if they changed.
    One entity failing does not stop the others; the exit code is 1 if any
    failed.
    """
    if window is not None and window not in WINDOWS:
        raise typer.BadParameter(f"window must be one of {', '.join(WINDOWS)}")
    limits = RejectLimits(max_ratio=max_reject_ratio, max_count=max_rejects)
    steps = delta_plan(date.today(), window)
    if dry_run:
        _echo_steps(target_url, steps, limits)
        return

    client = _client(max_retries, wait_time, rate_limit)
    if not skip_api_check:
        report = check_api_contract(client)
        for message in report.messages:
            typer.echo(message)
        if report.status == "changed":
            typer.echo(
                "The API no longer behaves as documented; syncing through a changed date "
                "boundary loses or duplicates records silently, so nothing was synced.",
                err=True,
            )
            raise typer.Exit(code=1)
    _report(run_plan(steps, get_sink(target_url, limits), client))


@app.command()
def backfill(
    target_url: str = TARGET_URL,
    entity_names: list[str] = typer.Option(
        [],
        "--entity",
        help="Load only this entity. Repeatable. Defaults to all.",
    ),
    max_retries: int = MAX_RETRIES,
    wait_time: float = WAIT_TIME,
    rate_limit: float = RATE_LIMIT,
    max_reject_ratio: float = MAX_REJECT_RATIO,
    max_rejects: int | None = MAX_REJECTS,
    dry_run: bool = DRY_RUN,
) -> None:
    """Load the history: full entities, then each windowed one year by year.

    Each windowed entity is loaded from the start of its history in
    one-year slices up to yesterday, each slice a run of its own. Safe to
    repeat: a slice already loaded is reconciled again, not duplicated.
    """
    for name in entity_names:
        _entity_option(name)
    limits = RejectLimits(max_ratio=max_reject_ratio, max_count=max_rejects)
    steps = backfill_plan(date.today(), entity_names or None)
    if dry_run:
        _echo_steps(target_url, steps, limits)
        return
    _report(
        run_plan(steps, get_sink(target_url, limits), _client(max_retries, wait_time, rate_limit))
    )


@app.command(name="list")
def list_entities(
    kind: str | None = typer.Option(
        None, "--kind", help="Only this kind: full or windowed (`search` is accepted for windowed)."
    ),
) -> None:
    """List the entities, one per line, for scripting."""
    if kind == "search":
        kind = "windowed"
    if kind not in (None, "full", "windowed"):
        raise typer.BadParameter("kind must be one of: full, windowed")
    for entity in ENTITIES.values():
        if kind is None or entity.kind == kind:
            typer.echo(entity.name)


@app.command(name="check-api")
def check_api(
    day: str | None = typer.Option(
        None, "--day", help="Probe this day (YYYY-MM-DD) instead of one 30 days back."
    ),
    max_retries: int = MAX_RETRIES,
    wait_time: float = WAIT_TIME,
    rate_limit: float = RATE_LIMIT,
) -> None:
    """Check that the live API still has the date semantics syncs rely on.

    The check itself is bdns-fetch's (`bdns-fetch check-api`); `delta` runs
    it before syncing. Exits 1 only when the API returned valid data that
    contradicts them; transient trouble or an empty probe day exits 0.
    """
    report = check_api_contract(
        _client(max_retries, wait_time, rate_limit), day=_parse_iso_date(day, "--day")
    )
    for message in report.messages:
        typer.echo(message)
    if report.status == "changed":
        typer.echo(
            "The API no longer behaves as documented. Syncing through a changed date "
            "boundary loses or duplicates records silently.",
            err=True,
        )
        raise typer.Exit(code=1)
