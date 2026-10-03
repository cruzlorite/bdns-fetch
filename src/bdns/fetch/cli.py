# SPDX-License-Identifier: GPL-3.0-or-later

"""The `bdns-fetch` command line.

One command per `fetch_*` method of [`BDNSClient`][bdns.fetch.client.BDNSClient],
generated from the method's signature: its parameters become the command's
options, with flags and help from [`options`][bdns.fetch.options]. Adding an
endpoint to the client adds the command; there is no second list to keep in
sync.

Command names are the method name without `fetch_`, with hyphens
(`concesiones-busqueda`). The underscore spelling (`concesiones_busqueda`),
which is how bdns-sync names the same endpoint, is accepted as a hidden
alias.

Records are written as JSON Lines; document endpoints write the raw bytes.
Two commands are not endpoints: `get` requests any path, and `check-api`
verifies the documented date semantics against the live service.
"""

import inspect
import json
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import click
import typer

from bdns.fetch.client import BDNSClient
from bdns.fetch.contract import check_api_contract
from bdns.fetch.exceptions import BDNSError, BDNSTransientError
from bdns.fetch.options import CLI_DEFAULTS, DATE, PARAMETERS
from bdns.fetch.utils import RateLimiter, smart_open

__all__ = ["app"]

try:
    __version__ = version("bdns-fetch")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

app = typer.Typer(
    name="bdns-fetch",
    # Typer dumps every frame's local variables into the traceback by
    # default, which would print request parameters (NIFs, names) into
    # whatever log captures stderr. The traceback itself is kept.
    pretty_exceptions_show_locals=False,
)


@dataclass
class _State:
    """What the global options configure, handed to every command."""

    client: BDNSClient
    output_file: Path
    verbose: bool


def _version_callback(value: bool) -> None:
    """Print the version and exit, when `--version` was passed."""
    if value:
        typer.echo(f"bdns-fetch {__version__}")
        raise typer.Exit()


def _configure_logging(verbose: bool) -> None:
    """Send log records to stderr: warnings always, HTTP detail with `--verbose`.

    Done in the callback rather than under `__main__`, because the installed
    `bdns-fetch` script calls `app` directly and never runs that guard.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    if verbose:
        logging.getLogger("bdns.fetch").setLevel(logging.DEBUG)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    output_file: Path = typer.Option(
        "-", "--output-file", "-o", help="File to write to. '-' is standard output."
    ),
    max_retries: int = typer.Option(
        3, "--max-retries", min=0, help="Retries for transient failures. 0 disables them."
    ),
    wait_time: float = typer.Option(
        2,
        "--wait-time",
        min=0,
        help="Initial seconds between retries. Doubles on each retry, up to 60.",
    ),
    max_workers: int = typer.Option(
        5, "--max-workers", min=1, max=20, help="Threads fetching pages concurrently."
    ),
    rate_limit: float = typer.Option(
        10,
        "--rate-limit",
        min=0.1,
        max=10,
        help="Requests per second. The API allows 10 per IP; lower it when several processes share one.",
    ),
    progress: bool | None = typer.Option(
        None,
        "--progress/--no-progress",
        help="Show a progress bar. By default, only when stderr is a terminal.",
        show_default=False,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Log every HTTP request and response."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    r"""Fetch data from the Base de Datos Nacional de Subvenciones (BDNS).

    \b
    Examples:
      bdns-fetch -o organos.jsonl organos --idAdmon C
      bdns-fetch convocatorias-busqueda --fechaDesde 2024-01-01 --num-pages 0
      bdns-fetch --max-retries 5 ayudasestado-busqueda --descripcion innovación

    \b
    Official API: https://www.infosubvenciones.es/bdnstrans/api
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

    _configure_logging(verbose)
    ctx.obj = _State(
        client=BDNSClient(
            max_retries=max_retries,
            wait_time=wait_time,
            max_workers=max_workers,
            progress=progress,
            rate_limiter=RateLimiter(rate=rate_limit) if rate_limit < 10 else None,
        ),
        output_file=output_file,
        verbose=verbose,
    )


def _write_records(records: Iterable[Any], output_file: Path) -> None:
    """Write `records` as JSON Lines, one per line, flushing as they arrive."""
    with smart_open(output_file, "w", encoding="utf-8", buffering=1) as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_bytes(content: bytes, output_file: Path) -> None:
    """Write a downloaded document as is."""
    with smart_open(output_file, "wb") as f:
        f.write(content)


def _hint(error: BDNSError) -> str | None:
    """Advice for the person at the prompt, from what kind of error it was."""
    if isinstance(error, BDNSTransientError):
        if error.status_code == 429:
            return "The API is rate limiting this IP. Lower --rate-limit or try later."
        return "The API is having trouble; the retries ran out. Try again later, or raise --max-retries."
    if error.status_code == 404:
        return "The resource does not exist. Check the identifier."
    if error.status_code in (400, 200):
        return "Check the parameter values and formats; see the command's --help."
    return None


def _report_error(error: BDNSError, verbose: bool) -> None:
    """Print a failed request as a short message on stderr."""
    typer.secho(f"Error: {error.message}", fg=typer.colors.RED, err=True)
    hint = _hint(error)
    if hint:
        typer.secho(f"Hint: {hint}", fg=typer.colors.YELLOW, err=True)
    if error.details:
        if verbose:
            typer.secho(error.details, dim=True, err=True)
        else:
            typer.secho("Run with --verbose for the response details.", dim=True, err=True)


def _run(action: Callable[[], None]) -> None:
    """Run a command body, turning an API error into a message and exit code 1."""
    state: _State = click.get_current_context().obj
    try:
        action()
    except BDNSError as error:
        _report_error(error, state.verbose)
        raise typer.Exit(code=1) from None


def _summary(method: Callable) -> str:
    """First paragraph of a docstring: the command's help."""
    return inspect.cleandoc(method.__doc__ or "").split("\n\n")[0]


def _build_command(method_name: str) -> Callable[..., None]:
    """Make a Typer command that calls `BDNSClient.<method_name>`.

    The command's signature is the method's, with each default replaced by
    a `typer.Option` built from the parameter's spec. A parameter with no
    default becomes a required option.
    """
    method = getattr(BDNSClient, method_name)
    signature = inspect.signature(method)
    parameters = []
    for param in list(signature.parameters.values())[1:]:  # skip self
        spec = PARAMETERS[param.name]
        default = CLI_DEFAULTS.get(param.name, param.default)
        if default is inspect.Parameter.empty:
            default = ...
        option = typer.Option(
            default,
            spec.flag,
            help=spec.help,
            show_default=default not in (None, ...),
            **spec.extra,
        )
        parameters.append(param.replace(default=option, kind=inspect.Parameter.KEYWORD_ONLY))

    def command(**kwargs: Any) -> None:
        state: _State = click.get_current_context().obj

        def action() -> None:
            result = getattr(state.client, method_name)(**kwargs)
            if isinstance(result, bytes):
                _write_bytes(result, state.output_file)
            else:
                _write_records(result, state.output_file)

        _run(action)

    command.__name__ = method_name
    command.__doc__ = _summary(method)
    command.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=parameters, return_annotation=inspect.Signature.empty
    )
    return command


def _register_endpoint_commands() -> None:
    """Add one command per `fetch_*` method, plus its underscore alias."""
    method_names = sorted(name for name in dir(BDNSClient) if name.startswith("fetch_"))
    for method_name in method_names:
        command = _build_command(method_name)
        endpoint = method_name.removeprefix("fetch_")
        app.command(endpoint.replace("_", "-"), rich_help_panel="Endpoints")(command)
        if "_" in endpoint:
            app.command(endpoint, hidden=True)(command)


def _parse_param(value: str) -> tuple[str, str]:
    key, sep, val = value.partition("=")
    if not sep or not key:
        raise typer.BadParameter(f"expected KEY=VALUE, got {value!r}")
    return key, val


@app.command(rich_help_panel="Tools")
def get(
    path: str = typer.Argument(..., help="Endpoint path, such as /vpd/GE/configuracion."),
    param: list[str] = typer.Option(
        [], "--param", "-p", help="Query parameter as KEY=VALUE. Repeatable."
    ),
    binary: bool = typer.Option(False, "--binary", help="Write the body as bytes, not JSON."),
) -> None:
    """Request any endpoint by path, with the same retries and rate limit.

    For endpoints that have no command of their own. The JSON document is
    written as one line.
    """
    state: _State = click.get_current_context().obj
    params: dict[str, Any] = {}
    for key, val in map(_parse_param, param):
        params.setdefault(key, []).append(val)
    query = {key: vals[0] if len(vals) == 1 else vals for key, vals in params.items()}

    def action() -> None:
        if binary:
            _write_bytes(state.client.get_bytes(path, query), state.output_file)
        else:
            _write_records([state.client.get(path, query)], state.output_file)

    _run(action)


@app.command("check-api", rich_help_panel="Tools")
def check_api(
    day: str | None = typer.Option(
        None, "--day", help="Probe this day (YYYY-MM-DD) instead of one 30 days back."
    ),
) -> None:
    """Check that the live API still has the documented date semantics.

    Exits 1 only when the API returned valid data that contradicts them.
    Transient trouble or empty probe days are reported and exit 0.
    """
    state: _State = click.get_current_context().obj
    probe_day: date | None = DATE.convert(day, None, None) if day else None
    report = check_api_contract(state.client, day=probe_day)
    for message in report.messages:
        typer.echo(message)
    if report.status == "changed":
        typer.secho(
            "The API no longer behaves as documented: date ranges would lose or duplicate records.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


_register_endpoint_commands()
