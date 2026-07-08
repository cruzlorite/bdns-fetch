# Roadmap

Pending work, in rough priority order. Issues with the source API do not belong here; they live in [section 8 of bdns-api-behavior.en.md](bdns-api-behavior.en.md#8-known-api-issues).

- **Group H endpoints** (`organos_codigo`, `organos_codigoadmin`). Not implemented; the rest of the official catalog is covered.
- **Live verification of PostgreSQL and MySQL.** They are compatible by design (portable SQL), but the full SCD2 cycle is only verified against SQLite (tests) and BigQuery (live). A CI job with a Postgres service container would close the gap.
- **Backfill resumption.** An interrupted backfill re-runs from the start; idempotent but slow. The `_sync_state` watermark would allow resuming from the last confirmed chunk.
- **File sink (Parquet).** A second implementation of the `Sink` interface, for non-SQL targets. The interface is already designed to allow it.
- **PyPI publication.** Install with `pip install bdns-sync` without cloning the repository.
