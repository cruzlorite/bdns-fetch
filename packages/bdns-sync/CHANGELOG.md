# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
