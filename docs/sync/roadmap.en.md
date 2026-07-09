# Roadmap

Pending work, in rough priority order. Issues with the source API do not belong here; they live in [section 8 of bdns-api-behavior.en.md](bdns-api-behavior.en.md#8-known-api-issues).

- **Group H endpoints** (`organos_codigo`, `organos_codigoadmin`). Not implemented; the rest of the official catalog is covered.
- **Live verification of PostgreSQL and MySQL.** They are compatible by design (portable SQL), but the full SCD2 cycle is only verified against SQLite (tests) and BigQuery (live). A CI job with a Postgres service container would close the gap.
- **Payload redaction (drop or anonymize fields).** A `Sink` decorator (`RedactingSink(inner, drop=[...], anonymize={...})`) applied in the CLI wiring: it wraps any sink without touching it and syncers never know. It must act **before** `_row_hash` is computed — redacting after would turn changes in a dropped field into new versions with identical stored payloads. It must refuse to touch `key_fields` and `reg_date_field` (they would break the natural key and deletion detection). Strategies: drop, null out, or pseudonymize with salted HMAC (allows grouping by beneficiary without exposing the tax ID). The policy is passed via repeatable CLI flags and lives in the operator's scripts, like the cadence and the dates. Caveat: changing the policy later changes every hash, and the next sync re-versions the whole table; redaction is ideally decided before the full load.
- **File sink (Parquet).** A second implementation of the `Sink` interface, for non-SQL targets. The interface is already designed to allow it.
