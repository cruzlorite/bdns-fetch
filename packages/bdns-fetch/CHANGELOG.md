# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The public API is what `bdns.fetch` exports in `__all__`, plus the `fetch_*`
methods of `BDNSClient` and the `bdns-fetch` command line.

## [Unreleased]

Planned as 2.0.0: the client's signatures change (see *Changed*).

### Fixed

- Transient failures are retried. Only network errors were: HTTP 429 and 5xx, and the API's
  `ERR_MANTENIMIENTO_BBDD`, raised at the first attempt whatever `max_retries` said. Long-running
  callers configured retries that never happened.
- `max_retries` counts retries. It counted attempts, so `max_retries=3` meant two retries, and
  `max_retries=1` none.
- An exhausted retry raises the last error (`BDNSTransientError`, `requests.ConnectionError`...)
  instead of `tenacity.RetryError`.
- Pages are yielded in page order. They came in completion order, so a paginated result was
  shuffled whenever `max_workers > 1`.
- Paginated downloads keep at most `2 * max_workers` pages in memory. All page requests used to be
  submitted at once, so the whole result could pile up behind a slow consumer, and stopping
  iteration early still downloaded every page.
- Document endpoints on the CLI (`convocatorias-pdf`, `convocatorias-documentos`,
  `planesestrategicos-documentos`) write the document. They wrote each byte as a JSON number on its
  own line.
- Logging works from the installed `bdns-fetch` script. It was configured under
  `if __name__ == "__main__"`, which the console script never runs, so warnings and `--verbose`
  output were lost.
- An HTTP 204 on a JSON endpoint is an empty result instead of an exception.
- The CLI reports API errors as a message and exit code 1 instead of a traceback, and no longer
  prints local variables (request parameters) in tracebacks.

### Added

- Each release gets a GitHub release, with its changelog section as notes and the same files published to PyPI.
- `BDNSTransientError`, the `BDNSError` subclass for failures worth retrying, with `retry_after`.
- Exponential backoff with jitter between retries, capped at 60 seconds, honouring `Retry-After`.
- Connection reuse: one `requests.Session` per thread.
- A `User-Agent` header identifying the client and its version.
- `progress` on `BDNSClient` and `--progress/--no-progress` on the CLI. By default the progress bar
  shows only when stderr is a terminal, so it no longer litters log files.
- A warning when a paginated call returns fewer pages than exist.
- `timeout` on `BDNSClient`.
- Underscore aliases for CLI commands (`concesiones_busqueda`), the spelling bdns-sync uses.
- Structured errors: `BDNSError` carries `status_code`, `code` (the API's `codigo`), `url` and
  `details`, so a program can react without parsing text.
- `get()`, `get_bytes()` and `pages()` request any path under the same retries, rate limit and
  parameter encoding, covering endpoints without a method of their own; `bdns-fetch get` does the
  same from the CLI.
- `bdns.fetch.dates`: `registration_range` and `period_range` turn an inclusive range into each
  date family's arguments (`fechaRegFin` is exclusive, `fechaHasta` inclusive), and `split_range`
  cuts long ranges into the 7-day pieces the API serves reliably. Moved here from bdns-sync.
- `bdns.fetch.contract` and `bdns-fetch check-api`: check those date semantics against the live
  API. Moved here from bdns-sync.
- `rate_limiter` and `base_url` on `BDNSClient`; `--rate-limit` on the CLI.
- A documentation site, with the measured behaviour of the API, architecture decision records and a
  compatibility policy.
- `Ambito` and `RateLimiter` are exported from `bdns.fetch`.
- Type information (`py.typed`), and support for Python 3.13 and 3.14.

### Changed

- **Breaking.** Endpoint parameters are keyword-only: `client.fetch_organos(idAdmon="C")`, not
  `client.fetch_organos("GE", "C")`.
- **Breaking.** Required parameters have no default. Omitting one raises `TypeError`; it used to send
  the literal `Ellipsis` to the API.
- **Breaking.** In the library, paginated methods fetch all pages by default (`num_pages=0`). One
  page silently truncated any larger result. The CLI keeps one page by default, and warns.
- **Breaking.** A document that does not exist raises `BDNSError`. It returned `b""`, the same as an
  empty document.
- The client no longer depends on the CLI. Method defaults are plain Python values instead of Typer
  `OptionInfo` objects, so signatures, type hints and editor help are accurate. The CLI builds its
  commands from the client's signatures.
- `wait_time` is the initial backoff rather than a fixed wait.
- Paginated downloads make one call at a time by default (`max_workers=1`), as the official good-practice guide
  asks ("no realizar llamadas de forma concurrente"). `max_workers` and `--max-workers` raise it. Splitting by date,
  not concurrency, is what makes large downloads reliable.
- Requests are spaced evenly, 9.5 per second, instead of allowing bursts of ten: the API answers 429
  to bursts even when the average is under its limit.
- **Breaking.** `BDNSError` takes its fields as keywords; `suggestion` is gone (advice is the CLI's
  job) and `technical_details` is now `details`.
- **Breaking.** `BDNSClient`'s constructor is keyword-only.
- **Breaking.** `bdns.fetch.endpoints` holds paths relative to `BDNS_API_BASE_URL`, with shorter
  names (`CONCESIONES_BUSQUEDA`).
- **Breaking.** CLI flags have no multi-letter short forms (`-mr`, `-np`, `-iddoc`...); `-o` and `-v`
  remain. CLI dates accept `YYYY-MM-DD` or `DD/MM/YYYY` only.
- The package moved to a `src/` layout.
- **License.** bdns-fetch is now distributed under the MIT license, instead of GPL-3.0-or-later,
  so it can be used in software under any license. Releases up to 1.3.0 remain under the GPL.

### Removed

- **Breaking.** `BDNSWarning`, no longer raised by anything.
- **Breaking.** `return_raw` and `--return-raw`, a client-wide flag that changed the return type of
  every method. Use `pages()` for whole page documents.
- **Breaking.** `format_url`, `format_date_for_api_request` and `smart_open` are no longer exported
  from `bdns.fetch`.
- **Breaking.** The `anio` alias of `fetch_grandesbeneficiarios_busqueda`. Use `anios=[...]`.
- Internal helpers that were never part of the public API: `utils.api_request`,
  `utils.extract_option_values`, `utils.write_to_file`, `exceptions.show_error`,
  `exceptions.handle_api_error`.
- Dependencies: `aiohttp` and `pytest-asyncio` (unused), Typer's `all` extra, and `dateparser`.

## Earlier releases

Reconstructed from tags and commit messages; there was no changelog before 2.0.0.

- **1.3.0** (2026-07-04): `fechaRegInicio` / `fechaRegFin` on the search endpoints that support
  them; client-side limit of 10 requests per second.
- **1.2.1** (2026-07-04): fixes to URL encoding, list parameters, binary retries and type mismatches.
- **1.2.0** (2026-01-05): `max_workers`; records instead of pages by default, with `--return-raw`.
- **1.1.0** (2026-01-03): removed concurrency to fix memory growth (restored in 1.2.0).
- **1.0.1** (2025-09-21), **1.0.0** (2025-09-20): first stable releases.
