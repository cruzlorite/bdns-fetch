# SPDX-License-Identifier: GPL-3.0-or-later

"""bdns-sync is a pure parameterized tool: one endpoint per invocation, no
config file, no cadence knowledge. Which endpoints to sync and when is an
orchestration concern that lives outside this package (see scripts/).
"""

import logging
import sys
from datetime import date
from typing import Optional

import typer
from sqlalchemy.engine import make_url

import bdns.fetch.client as _bdns_fetch_client
from bdns.fetch import BDNSClient
from bdns.sync import __version__
from bdns.sync.api_contract import check_api_contract
from bdns.sync.generic import CHUNK_DAYS, WINDOWS, iter_date_chunks, resolve_when
from bdns.sync.sinks import DEFAULT_LIMITS, RejectLimits, get_sink
from bdns.sync.syncers import FULL_SYNCERS, SEARCH_SYNCERS, policy_for

app = typer.Typer(
    name="bdns-sync",
    help="Sync one BDNS API endpoint into a target database in SCD2 form.",
    add_completion=False,
    # Typer dumps every frame's local variables into the traceback by
    # default. This tool runs unattended from cron and its locals hold
    # payload fragments (beneficiary names, identifiers) and the target
    # URL, password included for a Postgres target. That would land in
    # whatever log the job writes to, readable by anyone with access to
    # it. The traceback itself is kept; only the locals are dropped.
    pretty_exceptions_show_locals=False,
)


def _version_callback(value: bool) -> None:
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

    Configures logging here, not in `__main__.py`'s `if __name__ ==
    "__main__":` guard. The installed `bdns-sync` console script
    (`pyproject.toml`) imports and calls this Typer `app` directly, so that
    guard never runs. Typer always runs this callback before any
    subcommand regardless of entry point, so this is the one place
    guaranteed to run every time.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    if not sys.stderr.isatty():
        # bdns-fetch's pagination progress bar writes bare `\r` updates with
        # no trailing newline, meant for an interactive terminal. Piped to a
        # log file (cron, background runs) that leaves a stale progress
        # fragment glued to the front of the next log line. No public knob
        # on BDNSClient to disable it, so silence it here instead. Only
        # applies when output isn't a real terminal; interactive use keeps it.
        _bdns_fetch_client.tqdm = lambda iterable, *args, **kwargs: iterable


TARGET_URL_OPTION = typer.Option(
    ...,
    "--target-url",
    envvar="BDNS_SYNC_TARGET_URL",
    help="SQLAlchemy target DB URL (e.g. bigquery://project/dataset).",
)


def _parse_iso_date(value: Optional[str], flag: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(f"{flag} must be an ISO date (YYYY-MM-DD), got {value!r}") from None


def _resolve_plan(
    endpoint: str, window: Optional[str], since: Optional[date], until: Optional[date]
) -> tuple[Optional[date], Optional[date], str]:
    """Validate the invocation and work out what it would do.

    Shared by the real run and `--dry-run`, so a preview cannot disagree
    with the run it previews: the same rejections happen, in the same
    order, before either path goes anywhere.
    """
    if endpoint in SEARCH_SYNCERS:
        if since is not None:
            if window is not None:
                raise typer.BadParameter("use either --window or --since, not both")
            if until is not None and until < since:
                raise typer.BadParameter("--until must not be before --since")
        elif window is not None:
            if window not in WINDOWS:
                raise typer.BadParameter(f"window must be one of {', '.join(WINDOWS)}")
        else:
            raise typer.BadParameter(f"{endpoint} requires --window or --since")
        return resolve_when(window, since, until)
    if endpoint in FULL_SYNCERS:
        return None, None, "full"
    raise typer.BadParameter(f"unknown endpoint: {endpoint}")


def _echo_plan(
    endpoint: str,
    target_url: str,
    start: Optional[date],
    end: Optional[date],
    run_type: str,
    limits: RejectLimits,
) -> None:
    """Print the resolved invocation without touching anything.

    The URL is rendered with its password hidden: this output goes to a
    terminal and, from a script, to a log.
    """
    safe_url = make_url(target_url).render_as_string(hide_password=True)
    typer.echo(f"target      {safe_url}  ->  table {endpoint}")
    if start is None:
        typer.echo(f"run type    {run_type}  (complete replace, no date range)")
    else:
        chunks = sum(1 for _ in iter_date_chunks(start, end))
        days = (end - start).days + 1
        typer.echo(f"run type    {run_type}")
        typer.echo(
            f"range       {start} .. {end}  "
            f"({days} day(s), {chunks} chunk(s) of at most {CHUNK_DAYS})"
        )
    typer.echo(f"policy      {policy_for(endpoint).describe()}")
    typer.echo(f"limits      {limits.describe()}")
    typer.echo("dry run     nothing fetched, nothing written")


@app.command()
def sync(
    endpoint: str = typer.Argument(..., help="Endpoint/entity name to sync."),
    target_url: str = TARGET_URL_OPTION,
    window: str = typer.Option(
        None,
        "--window",
        help=f"Cascade window for incremental endpoints: one of {', '.join(WINDOWS)}.",
    ),
    since: str = typer.Option(
        None,
        "--since",
        help="Backfill start date (YYYY-MM-DD) for incremental endpoints. "
        "Overrides --window; syncs [since, until]. See scripts/full_load.sh.",
    ),
    until: str = typer.Option(
        None,
        "--until",
        help="Backfill end date (YYYY-MM-DD). Defaults to yesterday. Only with --since.",
    ),
    max_reject_ratio: float = typer.Option(
        DEFAULT_LIMITS.max_ratio,
        "--max-reject-ratio",
        min=0.0,
        max=1.0,
        help="Share of the batch that may be unusable before the run refuses it "
        "(0.10 = 10%). Raise it for a source having a bad day; lower it to be told sooner.",
    ),
    max_rejects: int = typer.Option(
        None,
        "--max-rejects",
        min=0,
        help="Absolute cap on unusable records, whatever the share. Catches a shape "
        "change in a batch large enough to hide it under the ratio. Unset by default.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Resolve and print what this invocation would do, then stop. "
        "Touches neither the API nor the target.",
    ),
) -> None:
    """Sync one endpoint.

    Incremental endpoints (the big search endpoints plus convocatorias) need
    a reg-date range: either a cascade `--window` (daily/weekly/monthly/annual)
    or an explicit `--since [--until]` backfill range. Full-replace endpoints
    ignore all of these.
    """
    since_date = _parse_iso_date(since, "--since")
    until_date = _parse_iso_date(until, "--until")
    start, end, run_type = _resolve_plan(endpoint, window, since_date, until_date)
    limits = RejectLimits(max_ratio=max_reject_ratio, max_count=max_rejects)

    if dry_run:
        _echo_plan(endpoint, target_url, start, end, run_type, limits)
        return

    sink = get_sink(target_url, limits)
    # Defaults (3 retries, 2s fixed wait) give up after ~1 minute of server
    # trouble; a real multi-hour backfill died live to one request timing
    # out 3 times in a row. 8 x 15s rides out a ~2-minute server rough patch;
    # the only cost is extra delay before a genuinely permanent failure.
    client = BDNSClient(max_retries=8, wait_time=15)

    # Outcome (row counts, duration) is logged by bookkeeping.run_with_bookkeeping;
    # no separate echo here to avoid printing the same summary twice.
    if endpoint in SEARCH_SYNCERS:
        sync_fn = SEARCH_SYNCERS[endpoint]
        if since_date is not None:
            sync_fn(sink, client, since=since_date, until=until_date)
        else:
            sync_fn(sink, client, window)
    else:
        FULL_SYNCERS[endpoint](sink, client)


@app.command(name="list")
def list_endpoints(
    kind: str = typer.Option("full", "--kind", help="one of: full, search"),
) -> None:
    """List known endpoint names, one per line, for scripting (no hardcoded lists)."""
    if kind == "full":
        for name in FULL_SYNCERS:
            typer.echo(name)
    elif kind == "search":
        for name in SEARCH_SYNCERS:
            typer.echo(name)
    else:
        raise typer.BadParameter("kind must be one of: full, search")


@app.command(name="check-api")
def check_api(
    day: str = typer.Option(
        None, "--day", help="Probe this day (YYYY-MM-DD) instead of one 30 days back."
    ),
) -> None:
    """Check that the live API still behaves the way this engine assumes.

    The date-window semantics this tool relies on were measured once and
    frozen into tests, but the tests pin the assumption, not the API: the
    fake client models the same semantics, so a change upstream would leave
    CI green while production silently lost a day per chunk boundary. This
    is the one command that asks the real service.

    Exits non-zero ONLY when the API returned valid data contradicting an
    invariant, which is the case worth stopping a sync for. Transient
    trouble (an error page, a maintenance window, an empty probe day) is
    reported and exits zero: blocking a whole day's cadence over a blip
    would cost far more than it saves, and a genuinely unreachable API
    makes the syncs themselves fail anyway.
    """
    client = BDNSClient(max_retries=8, wait_time=15)
    status, messages = check_api_contract(client, day=_parse_iso_date(day, "--day"))
    for message in messages:
        typer.echo(message)
    if status == "changed":
        typer.echo(
            "The API no longer behaves as this engine assumes. Syncing through a changed "
            "date boundary loses or duplicates records silently, so nothing was synced.",
            err=True,
        )
        raise typer.Exit(code=1)
