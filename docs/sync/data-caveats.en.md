# Notes for consuming the data

Things to keep in mind when reading the synced tables. All of them come from the source API's behavior (see [`bdns-api-behavior.en.md`](bdns-api-behavior.en.md)), not from a `bdns-sync` bug.

## `_reg_date` at the day boundary

`_reg_date` holds the payload's own registration date (`fechaAlta`, `fechaRegistro`, or `fechaRecepcion`, depending on the entity). A record whose registration falls exactly at midnight can end up assigned to the following calendar day.

Impact for the consumer: if you compare per-day counts against a direct API query, expect differences of ±1 record at day boundaries. The record is neither missing nor duplicated; it just lands on one day or the other depending on how each endpoint treats midnight. To avoid this, compare over multi-day ranges rather than day by day.

## Residual duplicates in historical loads

The API paginates by offset. If a date window **receives new registrations while it is being paginated** (which only happens on recent dates), a row near a page boundary can be returned on two consecutive pages. `bdns-sync` deduplicates at insertion time, so normal incremental syncs leave no duplicates. A large historical load in one long pass can, in rare cases, leave a duplicate pair behind.

A residual duplicate is **two `_is_current` rows with the same `_natural_key`, byte-for-byte identical** (same `_row_hash`, same payload). It corrupts nothing, but it inflates counts and can double rows in a `JOIN`.

Detect them:

```sql
SELECT _natural_key, COUNT(*) AS n
FROM your_table
WHERE _is_current
GROUP BY _natural_key
HAVING COUNT(*) > 1;
```

Remove them (keeping one copy per key; the payload is identical between copies, so there is no ambiguity):

```sql
CREATE TABLE _dedup AS
SELECT DISTINCT * FROM your_table
WHERE _natural_key IN ( /* keys detected above */ ) AND _is_current;

DELETE FROM your_table
WHERE _natural_key IN ( /* the same keys */ ) AND _is_current;

INSERT INTO your_table SELECT * FROM _dedup;
DROP TABLE _dedup;
```

This can only affect dates that were receiving new registrations during the load (recent ones). Historical dates that are already closed get no concurrent writes, their pagination is stable, and they cannot contain duplicates.
