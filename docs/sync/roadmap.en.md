# Roadmap

What remains to be done, in rough order of priority. What is done is in
the [CHANGELOG](https://github.com/cruzlorite/bdns-sync/blob/main/CHANGELOG.md);
source API issues, in [what it does about each known API issue](explanation/sync-behavior.md#api-issues).

- **Group H endpoints** (`organos_codigo`, `organos_codigoadmin`). Not synced; the rest of the official catalog is covered. With the [entity registry][bdns.sync.entities] it is one entry per endpoint, plus its natural key.
- **Payload field suppression or pseudonymisation.** A [`Sink`][bdns.sync.sinks.Sink] decorator (`RedactingSink(inner, drop=[...], anonymize={...})`) wrapping any sink untouched. It must act **before** `_row_hash` is computed: suppressed afterwards, a change in a dropped field would produce new versions with an identical stored payload. It must refuse to touch key fields and the registration date. Strategies: drop the field, null it, or pseudonymise it with a salted HMAC (so beneficiaries can be grouped without exposing their tax ID). Changing the policy later changes every hash and re-versions the whole table, so it is best decided before the initial load.
- **File sink (Parquet).** A second [`Sink`][bdns.sync.sinks.Sink] implementation, for targets without SQL. The batch interface is already designed for it.
- **Query views.** One view per entity with only current versions and the most used fields extracted from `payload`, for anyone querying without knowing the SCD2 model.
