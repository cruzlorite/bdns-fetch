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

## Expiry versus real withdrawal

`_valid_from` and `_valid_to` record when `bdns-sync` **observed** a version, not when the event happened in the real world. A row is closed when it stops coming back from the source, and that happens for two very different reasons that look identical in the table:

- **Real withdrawal**: the granting body removed or reissued the record.
- **Expiry**: the grant reached the end of its publication period and left the BDNS. For `concesiones_busqueda` that is the 4 calendar years following the concession; for `ayudasestado_busqueda` and `minimis_busqueda`, 10 years.

Expiry is deterministic, so the two are told apart with a rule rather than a guess: compare the year of `fechaConcesion` with the year of `_valid_to`.

```sql
SELECT
  CASE WHEN EXTRACT(YEAR FROM _valid_to)
            - CAST(SUBSTR(JSON_VALUE(payload,'$.fechaConcesion'),1,4) AS INT64) > 4
       THEN 'expiry' ELSE 'real withdrawal' END AS reason,
  COUNT(*)
FROM your_table
WHERE _valid_to IS NOT NULL AND NOT _is_current
GROUP BY reason;
```

Two things that do **not** tell them apart. Closures arriving in bulk say nothing: real withdrawals also come in batches, because a granting body corrects many records at once (measured in August 2026: batches of 5,420 and 2,032 closures on a single day, spanning four and five different concession years). Neither does version lifetime: it measures time since the last edit, not the age of the record, so an old concession edited recently has a young version.

### When expiries show up

The regular cadence barely sees them. The annual window reaches 365 days of registration date, so only rows registered within the last year fall in its scope; an old concession registered recently will be closed when it expires, but that is a trickle.

A **wide backfill is another matter**: its comparison scope is the whole requested range, so it closes everything expired at once, stamped with the day it ran. Re-running [`scripts/full_load.sh`](../scripts/full_load.sh) against an already-populated target does exactly that. As of September 2026, with 1.13 million 2022 concessions stored and about to reach the end of their period, a backfill run in 2027 would close them all together.

This is not a bug: the record is no longer at the source and the table reflects that. But that closing date says when you found out, not when it expired.
