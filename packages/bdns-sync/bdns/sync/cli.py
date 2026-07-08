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

import bdns.fetch.client as _bdns_fetch_client
from bdns.fetch import BDNSClient
from bdns.sync import __version__
from bdns.sync.generic import WINDOWS
from bdns.sync.sinks import get_sink
from bdns.sync.syncers import FULL_SYNCERS, SEARCH_SYNCERS

app = typer.Typer(
    name="bdns-sync",
    help="Sync one BDNS API endpoint into a target database in SCD2 form.",
    add_completion=False,
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
) -> None:
    """Sync one endpoint.

    Incremental endpoints (the big search endpoints plus convocatorias) need
    a reg-date range: either a cascade `--window` (daily/weekly/monthly/annual)
    or an explicit `--since [--until]` backfill range. Full-replace endpoints
    ignore all of these.
    """
    sink = get_sink(target_url)
    # Defaults (3 retries, 2s fixed wait) give up after ~1 minute of server
    # trouble; a real multi-hour backfill died live to one request timing
    # out 3 times in a row. 8 x 15s rides out a ~2-minute server rough patch;
    # the only cost is extra delay before a genuinely permanent failure.
    client = BDNSClient(max_retries=8, wait_time=15)

    since_date = _parse_iso_date(since, "--since")
    until_date = _parse_iso_date(until, "--until")

    # Outcome (row counts, duration) is logged by bookkeeping.run_with_bookkeeping;
    # no separate echo here to avoid printing the same summary twice.
    if endpoint in SEARCH_SYNCERS:
        sync_fn = SEARCH_SYNCERS[endpoint]
        if since_date is not None:
            if window is not None:
                raise typer.BadParameter("use either --window or --since, not both")
            if until_date is not None and until_date < since_date:
                raise typer.BadParameter("--until must not be before --since")
            sync_fn(sink, client, since=since_date, until=until_date)
        elif window is not None:
            if window not in WINDOWS:
                raise typer.BadParameter(f"window must be one of {', '.join(WINDOWS)}")
            sync_fn(sink, client, window)
        else:
            raise typer.BadParameter(f"{endpoint} requires --window or --since")
    elif endpoint in FULL_SYNCERS:
        FULL_SYNCERS[endpoint](sink, client)
    else:
        raise typer.BadParameter(f"unknown endpoint: {endpoint}")


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
