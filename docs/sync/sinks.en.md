# Target databases (sinks)

All sync logic uses portable SQL (correlated `EXISTS`/`NOT EXISTS` subqueries, no engine-specific `MERGE` or `UPDATE ... FROM`), so any database with a SQLAlchemy dialect works as a target. Verified:

| Target | Status | Notes |
|---|---|---|
| SQLite | Verified (full test suite) | No extra setup |
| BigQuery | Verified (live, full SCD2 cycle) | Requires the `bigquery` extra; see below |
| PostgreSQL / MySQL | Compatible by design (portable SQL) | Install the driver (`psycopg2`, `pymysql`, ...) |

## Architecture

Storage sits behind a `Sink` interface ([`bdns/sync/sinks/`](../bdns/sync/sinks/)): the fetch layer hands over batches of records and the sink owns everything else (SCD2 versioning, deletion detection, run logging). The current implementation is [`SQLSink`](../bdns/sync/sinks/sql/__init__.py), covering any engine with a SQLAlchemy dialect; per-engine differences are confined to its internal adapters ([`bdns/sync/sinks/sql/dialects.py`](../bdns/sync/sinks/sql/dialects.py)). A future non-SQL target (e.g. Parquet) would be another `Sink` implementation, leaving the fetch layer untouched.

The staging load overlaps the fetch of the next batch with the write of the current one through a generic producer/consumer pipeline ([`bdns/sync/pipeline.py`](../bdns/sync/pipeline.py)), with a bounded queue as backpressure. Figures and rationale in [section 7 of bdns-api-behavior.en.md](bdns-api-behavior.en.md#7-measured-performance).

## BigQuery

```bash
export BDNS_SYNC_TARGET_URL="bigquery://<project>/<dataset>"
```

- **Authentication**: application default credentials (`gcloud auth application-default login`) or a service account via `GOOGLE_APPLICATION_CREDENTIALS`.
- **Minimum permissions**: `roles/bigquery.dataEditor` on the dataset and `roles/bigquery.jobUser` on the project.
- **Indexes**: BigQuery has no secondary indexes; the adapter skips them and tables are created with `CLUSTER BY (_natural_key, _is_current)` instead, the columns every SCD2 diff filters on.
- **Writes via load jobs, not DML**: staging uses `load_table_from_json` instead of INSERT statements, which is 3-4x faster and **free** (load jobs don't count against the query/DML byte quota). Measured live on the same backfill: ~250-325 rows/s with batched DML versus ~900-1,300 rows/s with load jobs.
- **Writes strictly serial**: BigQuery caps table update operations at a low fixed rate; submitting load jobs concurrently trips `429 too many table update operations`, a hard platform limit, not a raisable quota.
- **No autoincrement**: control-table identifiers (`run_id`, `error_id`) are app-generated (epoch microseconds), not database-generated.
- The remaining differences (JSON type without bind-parameter support, `DELETE` requiring `WHERE`, `NULL` literals needing an explicit type) are handled and documented in [`dialects.py`](../bdns/sync/sinks/sql/dialects.py) and the `sinks/sql/` code.
