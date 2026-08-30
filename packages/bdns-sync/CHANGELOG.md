# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-30

### Fixed

- `grandesbeneficiarios_busqueda` no longer re-versions half the table on every run: the API returns a different
  spelling of `beneficiario` for the same `idPersona` on nearly every call, so that field is now excluded from the
  content hash. It is still stored whole in the payload. The first run after upgrading re-versions the table once,
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
