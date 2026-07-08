# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
