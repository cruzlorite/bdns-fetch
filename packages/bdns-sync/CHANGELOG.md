# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Planned as 0.6.0, on bdns-fetch 2.0.

### Added

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

### Fixed

- A batch in which one natural key carries two different payloads fails the run, naming the keys. It used to write
  two current versions for one key, which every later run closed and rewrote, reporting changes the source never
  made. Byte-identical duplicates are still tolerated.
- Retries now cover server errors. With bdns-fetch 1.x the configured 8 retries only applied to network errors; HTTP
  429, 5xx and `ERR_MANTENIMIENTO_BBDD` failed the run at the first attempt.
- Rejected records reach `_sync_errors` on a failed run too. They were only written on the success path, so a run
  that failed *because* too much of the batch was rejected told the operator to go and read a table that had nothing
  in it, which is exactly the case where the reasons matter.

### Changed

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
- Requires bdns-fetch 2.0, which now owns the API's date semantics (`bdns.fetch.dates`), the contract check
  (`bdns.fetch.contract`) and request spacing. The tqdm patch, the all-pages wrapper and the per-call spacing are gone.
- The scripts are one-line wrappers around `delta` and `backfill`, kept for existing crontabs, and the image runs
  `bdns-sync delta`.
- The docs site is deployed on release tags instead of on every push, so it documents the latest release. The API
  behaviour notes moved to bdns-fetch's site; this site keeps what the engine decides because of them.
- ruff targets Python 3.11 and CI checks formatting, with the same configuration as bdns-fetch.
- The Docker image installs the locked dependency versions instead of resolving them at build time.

## [0.5.0] - 2026-09-06

### Removed

- `convocatorias_ultimas` is no longer synced. It is a rolling feed of the most recently received calls, not a
  catalog, so reconciling it against the full current state closed about 30 rows a day that were not withdrawals,
  just calls dropping out of the latest N. Its 2,000 rows were almost all closed versions recording that churn.
  Everything it held is in `convocatorias_busqueda`, with a registration date and without the noise. Existing
  targets can drop the table and its rows in `_sync_state` and `_sync_runs`; nothing else refers to them.

### Added

- `--dry-run` on `sync`: resolves the invocation and prints what it would do, touching neither the API nor the
  target. Shows the target (password hidden), the resolved date range with its chunk count, and the payload policy
  that would apply. It runs the same validation as a real run, so a preview cannot accept what the run would reject.
- The per-entity policies become a registry the syncers read through `policy_for`, so the rules a dry run prints and
  the rules a sync applies cannot drift apart. A test pins that every key in it is a real entity: a typo there would
  not fail, it would silently fall back to the default and start re-versioning on noise the entity used to ignore.

### Changed

- The per-record rules (`exclude_from_hash`, `delimited_lists`, and array canonicalization) move into a
  `PayloadPolicy` object declared once per entity, instead of travelling as separate keyword arguments through four
  layers. `apply_incremental` drops from twelve parameters to nine, and the rules now sit next to the measurement
  that justifies each of them.
- The policy exposes a single `prepare()` returning the payload to store and its hash together. Hashing something
  other than what is stored is the one combination that produces unreadable history, so it is no longer expressible:
  a version pair whose stored payloads are byte-identical can never occur.
- Array canonicalization becomes a policy setting rather than an unconditional step. It stays on by default; turning
  it off re-versions every record with a reordered nested array on every run.
- A policy that would drop a natural-key field or the registration-date field is refused. Changing a hash rule costs
  storage and noise; changing identity severs a record's past from its future.
- No hash changes. Verified against the fixtures and, more to the point, against 24 rows read back from the live
  BigQuery target: the new policy reproduces every stored `_row_hash` exactly.

### Fixed

- PostgreSQL never worked. The version INSERT wrote `_valid_to` as a bare `NULL`, which PostgreSQL types as `text`
  and then refuses against a `timestamptz` column, so every run failed on the first insert. It is now an explicit
  `CAST(NULL AS ...)`. The full test suite runs against a real PostgreSQL in CI, alongside SQLite, so the "portable
  SQL" claim is now tested rather than asserted.
- `bdns-sync --version` reported 0.1.0 regardless of the release. The version now comes from the installed package
  metadata, so there is one source of truth and the publish workflow's tag check covers it.
- `delta_load.sh` no longer aborts the whole day when one entity fails. Failures are collected, the remaining
  entities still run, and the script exits non-zero with a summary. Seen live on 2 September 2026: `sectores` hit the
  BigQuery daily quota and took the other 22 entities down with it, leaving 1 run that day instead of 23. A run
  terminated by SIGTERM at the task timeout now exits 143 instead of reporting success.

### Changed

- Records the source sends in an unusable shape are now dropped and recorded instead of taking the run down, for
  every entity rather than only the three on the two-step detail path. A record is rejected when it is not a JSON
  object, when a natural-key field is missing or null, or when the registration date is missing, null, or not an
  ISO date. Each rejection lands in `_sync_errors` with its reason. Runs that used to fail on these now finish with
  `rows_skipped > 0`, so that counter is worth watching alongside the job-failure alert.
- A run whose batch is left empty by rejections, or where rejections exceed 10% with at least five of them, now
  fails instead of applying. An empty staging is indistinguishable from "everything in this window was withdrawn",
  so window-scoped deletion detection would close the lot.
- Staging is emptied with `TRUNCATE TABLE` on BigQuery and PostgreSQL, through a new `clear_table` adapter method.
  On BigQuery a `DELETE` is DML and is billed by the byte: 17.2 GB scanned per clear, twice per run, out of 91 GB for
  the whole annual `concesiones_busqueda` diff. `TRUNCATE` is a metadata operation and scans nothing. SQLite and
  DuckDB keep the `DELETE`, which costs them nothing.
- Typer no longer dumps frame locals into tracebacks. They held payload fragments and the target URL, password
  included for a PostgreSQL target, and landed in whatever log an unattended run writes to.

### Added

- `bdns-sync check-api`, run once by `delta_load.sh` before the cadence, asks the live service whether it still
  behaves the way the engine assumes: `fechaRegFin` exclusive, `fechaHasta` inclusive, adjacent days disjoint and
  summing to their range, records carrying their natural key and registration date. The test suite can only pin our
  model of the API, so a change upstream would otherwise leave CI green while production lost a day per chunk
  boundary. It fails open on a transient error or an empty probe day and aborts only on valid data that contradicts
  an invariant.
- DuckDB is a verified target. It needed no code change: the full suite passes against it as-is, and it runs in CI
  alongside SQLite and PostgreSQL. It is the serverless local target that suits this data better than SQLite.
- Tests for the run bookkeeping failure path and the staging lifecycle, including the guarantee that a crashed run's
  leftover staging rows cannot leak into the next run's diff.
- Direct tests for the concurrency helpers, which had none. Their failure mode is silent: a dropped row would not
  raise, it would shorten the batch, and on an entity with window-scoped deletion detection the missing rows would
  then be closed as real withdrawals under a `success` event.
- Idempotency asserted as a property: repeating a sync leaves the stored history byte-identical, with only
  `_synced_at` moving. Covers full syncs, syncs after a real edit, syncs after a deletion, and a wider cascade window
  re-running over ground a narrower one already covered.
- Tests for the BigQuery load-job payload, which bypasses SQLAlchemy and hand-builds what lands in the table. The row
  building moved to `staging_json_rows` so it can be tested without the google-cloud stack, and a fake client pins
  the blocking `.result()` call that paces submissions under BigQuery's hard rate limit.

## [0.4.0] - 2026-09-06

### Added

- `delimited_lists` on the `Sink` interface: payload fields carrying a list inside one string, mapped to the pattern
  that splits them. Their elements are sorted before hashing, so the order the source happened to use stops counting
  as a change. `sectores` in ayudasestado and `sectorActividad` in minimis, where reordering accounted for 84% and
  92% of each entity's version churn. The pattern is a regular expression rather than a plain separator because
  several CNAE names contain the ";" that joins them. Never auto-detected: a comma in free text is not a list.

### Fixed

- `concesiones_busqueda` excludes `beneficiario` from the hash: of the keys whose name changed more than once, 67%
  return to a spelling they already had, with `idPersona` unchanged throughout. It re-versioned 58% of the table.
- A field is excluded from the hash only where that oscillation is measured. The previous release excluded
  `beneficiario` in four entities by analogy; in three of them the sample was too small to conclude and the volume was
  hundreds of versions, so the exclusion is reverted there and the change is recorded instead.

### Note

- The first run of a migrated entity re-versions every row whose hash changes under the new rules, unless the stored
  hashes are migrated first. Payloads are untouched either way: these parameters only shape what the hash sees.

## [0.3.0] - 2026-08-30

### Fixed

- `grandesbeneficiarios_busqueda` no longer re-versions half the table on every run: the API returns a different
  spelling of `beneficiario` for the same `idPersona` from one hour to the next, so that field is now excluded from
  the content hash. It is still stored whole in the payload. The first run after upgrading re-versions the table once,
  because every hash changes.

### Added

- `exclude_from_hash` on the `Sink` interface: payload fields that do not count as changes. The parameter existed
  inside the SCD2 layer but was never reachable from a caller.

## [0.2.1] - 2026-08-30

### Changed

- Spanish documentation rewritten in natural Spanish (tone, vocabulary and register); no technical content changed.
- Cloud Run recipe documents `--memory 2Gi`: 1 GiB gets OOM-killed on the wide `concesiones_busqueda` windows.

### Fixed

- Broken cross-links between `bdns-api-behavior.md` and its English mirror.

## [0.2.0] - 2026-07-10

### Added

- BigQuery as a first-class target (SQLAlchemy dialect adapters, load-job staging writes, clustering instead of indexes).
- `Sink` storage abstraction; SQL machinery under `bdns/sync/sinks/sql/`.
- Producer/consumer staging pipeline and paced parallel detail fetches (`bdns/sync/pipeline.py`).
- Window-scoped deletion detection for the incremental search endpoints.
- `_sync_runs` append-only event log, `_sync_state` watermark, and `_sync_errors` malformed-record log.
- Optional `bigquery` extra: `pip install bdns-sync[bigquery]`.

### Fixed

- `run_id`/`error_id` columns use `BigInteger`: epoch-microsecond identifiers overflow 32-bit `INTEGER` on PostgreSQL/MySQL.
- Version insertion deduplicates staging rows (`SELECT DISTINCT`), so a duplicated record in one batch can no longer produce two identical current versions.
- Silent pagination truncation: all paginated endpoints fetch every page (`num_pages=0`).
