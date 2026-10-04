# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
What counts as public, module by module, is in the
[compatibility policy](https://cruzlorite.github.io/bdns-tools/compatibility/).

## [Unreleased]

Planned as 2.0.0. `bdns-tools` brings bdns-fetch and bdns-sync together in one package
([ADR 0001](https://cruzlorite.github.io/bdns-tools/adr/0001-one-package/)): the imports (`bdns.fetch`,
`bdns.sync`) and the commands (`bdns-fetch`, `bdns-sync`) stay the same, but the package to install is
now `bdns-tools` (`pip install bdns-tools`, or `pip install "bdns-tools[bigquery]"`). Numbering continues bdns-fetch's.

### Changed

- **Breaking.** One package, `bdns-tools`, replaces `bdns-fetch` and `bdns-sync` on PyPI. The repository is now
  [cruzlorite/bdns-tools](https://github.com/cruzlorite/bdns-tools), and both tools share one documentation site,
  <https://cruzlorite.github.io/bdns-tools/>.
- The Docker image (`ghcr.io/cruzlorite/bdns-sync`) is built with uv from the project's lock file.

### Added

- Each release gets a GitHub release, with its changelog section as notes and the same files published to PyPI.

### The dataset (experimental)

The start of the anonymised, aggregated dataset ([ADR 0002](https://cruzlorite.github.io/bdns-tools/adr/0002-anonymised-dataset/),
still a proposal). It is DuckDB SQL in `dataset/`, not part of the Python package, and may change until its first
version is published. `dataset/build.sql` runs the steps with the DuckDB command line against a bdns-sync database
attached as `sync`:

- `01_beneficiaries.sql`: classifies a BDNS beneficiary as a natural person, an entity made of persons, a legal
  person, a public body or unknown, from its tax ID alone, and treats anything unrecognised as a natural person.
- `02_privacy.sql`: the building blocks of the checks that stop the build if a table about to be published holds
  something shaped like a natural person's tax ID or a column that identifies people.
- `10_concesiones.sql`: each award's last known version, read straight from bdns-sync (withdrawn ones included),
  with typed columns and the beneficiary's kind.
- `11_ayudas_estado.sql`, `12_minimis.sql`: state and de minimis aid, likewise.
- `20_entidades.sql`: awards, state aid and de minimis aid to legal persons and public bodies, record by record, in
  the `publicar` schema that holds everything to be published; without `url_br` (the bulletin usually lists natural
  persons too) or `id_persona`.
- `90_checks.sql`: stops the build if a record-level table holds a protected beneficiary or anything shaped like a
  natural person's tax ID.
- `95_export.sql`: writes each table in `publicar`, and nothing else, as a Parquet file (the dataset's only format)
  in the folder named by the `salida` variable, once the checks have passed.

### bdns.fetch

Changes since bdns-fetch 1.3.0.

#### Fixed

- API errors no longer read "Error: Error (ERR_VALIDACION): …" on the command line: an error's message now starts
  with the API's code (`ERR_VALIDACION: …`), or with `HTTP 404` when there is none.
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

#### Added

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

#### Changed

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

#### Removed

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

### bdns.sync

Changes since bdns-sync 0.5.0.

#### Added

- `bdns-sync delta`: the daily run as one command. It checks the API's date semantics (and syncs nothing if they
  changed), syncs every full entity, then every windowed one with the window the cadence picks: annual on 1 January,
  1 May and 1 September, monthly on Mondays, weekly otherwise. One entity failing does not stop the others; the exit
  code is 1 if any failed. `--window` forces a window, `--dry-run` prints the plan with its dates.
- `bdns-sync backfill`: the historical load as one command, each windowed entity loaded year by year from the start
  of its history, each year a run of its own. `--entity` limits it.
- Every version records the run that created it and, once closed, the run that closed it and why: `_created_run_id`,
  `_closed_run_id`, `_closed_reason` (`superseded` or `removed`). "What did run X change" and "what was withdrawn"
  become plain queries.
- `_sync_runs` records `rows_changed`, `rows_unchanged` and, for windowed runs, `window_start` and `window_end`, so the
  coverage of the history can be audited from the log.
- Targets written by earlier versions are upgraded in place: each run adds the nullable columns a table lacks. The
  schema only ever grows that way.
- `--max-retries`, `--wait-time`, `--rate-limit` and `--max-workers`, each with an environment variable
  (`BDNS_SYNC_MAX_RETRIES`...).
  The defaults (5 retries from 10 s) ride out about 3-4 minutes of server trouble per request.
- A CI job runs the suite against bdns-fetch's main branch, to catch a break before it is released.
- `--max-reject-ratio` and `--max-rejects` set how much of a batch may be unusable before the run refuses it. The
  first was a constant; the second is new, and covers what a share cannot see: 20,000 broken records out of 20
  million is 0.1%, below any sane ratio, and still means the shape of what the source returns changed. Both are
  operational tolerances rather than statements about the data, so they are per run and carry no per-entity
  defaults. `--dry-run` prints them alongside the payload policy.
- Documented that a rejected record on a full-replace entity closes its stored version as a withdrawal. A record with
  no usable natural key cannot be matched to the row it belongs to, so "returned malformed" and "no longer served"
  are indistinguishable. The reject ceiling is what bounds how many rows this can close.
- `sync` accepts hyphenated endpoint names (`concesiones-busqueda`), the spelling bdns-fetch uses for its
  commands.
- The package ships `py.typed`.

#### Fixed

- DuckDB targets failed on a fresh install: pip picked SQLAlchemy 2.1, under which duckdb-engine 0.17 cannot
  reflect the schema. SQLAlchemy is capped below 2.1 until the DuckDB and BigQuery dialects support it.
- Building the tables no longer warns "Can't validate argument 'bigquery_clustering_fields'" on every run
  when the `bigquery` extra is not installed: the BigQuery clustering option is only passed when its
  dialect is.
- A batch in which one natural key carries two different payloads fails the run, naming the keys. It used to write
  two current versions for one key, which every later run closed and rewrote, reporting changes the source never
  made. Byte-identical duplicates are still tolerated.
- Retries now cover server errors. With bdns-fetch 1.x the configured 8 retries only applied to network errors; HTTP
  429, 5xx and `ERR_MANTENIMIENTO_BBDD` failed the run at the first attempt.
- Rejected records reach `_sync_errors` on a failed run too. They were only written on the success path, so a run
  that failed *because* too much of the batch was rejected told the operator to go and read a table that had nothing
  in it, which is exactly the case where the reasons matter.

#### Changed

- **License.** bdns-sync is now distributed under the MIT license, instead of GPL-3.0-or-later, so it can be
  used in software under any license. Releases up to 0.5.0 remain under the GPL.
- **Breaking.** Entities are declared once, in `bdns.sync.entities.ENTITIES`, and run with `sync_entity`. The 22
  `sync_*` functions, `FULL_SYNCERS`, `SEARCH_SYNCERS`, `POLICIES`, `policy_for` and the `generic`, `syncers` and
  `api_contract` modules are gone.
- **Breaking.** Sinks return a `SyncStats` (`fetched`, `new`, `changed`, `unchanged`, `removed`, `skipped`) instead of
  a dict with `inserted`, `updated`, `touched` and `soft_deleted`. Run logs print the new names.
- `list --kind windowed` replaces `search`, which is still accepted.
- One API call at a time by default, pages and detail calls alike, as the official good-practice guide asks. The
  detail step of `convocatorias` and `planesestrategicos` used 8 threads; `--max-workers` (`BDNS_SYNC_MAX_WORKERS`)
  raises it again. Paginated searches take about twice as long with one (a week of `concesiones_busqueda` into
  SQLite: 63 s instead of 27 s); detail calls barely change while the server is fast, since the rate limit caps them.
- `bdns.fetch` now owns the API's date semantics (`bdns.fetch.dates`), the contract check
  (`bdns.fetch.contract`) and request spacing. The tqdm patch, the all-pages wrapper and the per-call spacing are gone.
- The scripts are one-line wrappers around `delta` and `backfill`, kept for existing crontabs, and the image runs
  `bdns-sync delta`.
- The docs site is deployed on release tags instead of on every push, so it documents the latest release. The API
  behaviour notes moved to bdns-fetch's site; this site keeps what the engine decides because of them.
- ruff targets Python 3.11 and CI checks formatting, with the same configuration as bdns-fetch.
- The Docker image installs the locked dependency versions instead of resolving them at build time.

## Before bdns

bdns-fetch and bdns-sync were published as separate packages. bdns-sync's full changelog is kept at its last
tag, [bdns-sync 0.5.0](https://github.com/cruzlorite/bdns-tools/blob/bdns-sync-v0.5.0/packages/bdns-sync/CHANGELOG.md).
bdns-fetch had no changelog; this summary is reconstructed from its tags and commit messages:

- **1.3.0** (2026-07-04): `fechaRegInicio` / `fechaRegFin` on the search endpoints that support
  them; client-side limit of 10 requests per second.
- **1.2.1** (2026-07-04): fixes to URL encoding, list parameters, binary retries and type mismatches.
- **1.2.0** (2026-01-05): `max_workers`; records instead of pages by default, with `--return-raw`.
- **1.1.0** (2026-01-03): removed concurrency to fix memory growth (restored in 1.2.0).
- **1.0.1** (2025-09-21), **1.0.0** (2025-09-20): first stable releases.
