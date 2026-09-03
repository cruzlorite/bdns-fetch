# BDNS API behavior: date windows

[🇪🇸 Spanish version](./bdns-api-behavior.md)

This document records the actual behavior of the BDNS API with respect to date parameters, verified through live tests against the service. It is documented in detail because these behaviors are subtle, absent from the official documentation (or contradicted by it), and mishandling them causes silent data loss.

Each claim states the empirical check that supports it.

## 1. Internal convention: inclusive day range

In `bdns-sync`, a window is a day range **inclusive on both ends**: the `daily` window for day `X` means "the records registered on day `X`". The upper end of every window is *yesterday* (`date.today() - 1`), because the current day's data is not final until the following morning.

## 2. Upper-bound semantics per endpoint

The API has two families of date parameters, and their upper bounds behave in **opposite** ways:

| Family | Parameters | Endpoints | Upper bound | Live check (day `D`) |
|---|---|---|---|---|
| Registration-date search | `fechaRegInicio` / `fechaRegFin` | `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `partidospoliticos_busqueda` | **Exclusive** (excludes day `D`) | `fechaRegFin=D` returns ~0 rows for day `D`; `fechaRegFin=D+1` returns the full day `D` (concesiones: 1 row vs. 58,488) |
| Convocatorias discovery | `fechaDesde` / `fechaHasta` | `convocatorias` (discovery step) | **Inclusive** (includes day `D`) | `fechaHasta=D` returns every convocatoria with `fechaRecepcion == D`; `fechaHasta=D+1` returns days `D` and `D+1` |

The conversion between the internal convention (inclusive) and the exclusive family is centralized in a single function, `generic.to_api_upper_bound(inclusive_end)`, which adds one day to the upper bound. The `convocatorias` endpoint does not use it: its `fechaHasta` is already inclusive, and adding a day would pull in convocatorias from outside the window.

For `convocatorias`, the date parameters only apply to the discovery step (`convocatorias_busqueda`): each discovered code is then fetched in full through the detail endpoint (by `numConv`), which has no date parameters and is what gets stored.

The cost of `convocatorias` is therefore linear in the number of codes, not in the window width. Measured live with a real month (May 2026, 6,186 codes): discovery takes ~1 s, and the detail step dominates entirely. Per-call detail latency varies with server load: ~0.22 s/call under favorable conditions (one month ≈ 23 minutes), but a full run of the same month took as long as 3 h 12 min (~1.9 s/call) with a single timeout retry. The run succeeded in both regimes (6,186 rows, 0 skips); only the duration changes.

The detail step is parallelized to approach the 10 req/s limit instead of being bound to single-connection latency. The server rejects bursts, so request starts are spaced apart; the measured detail is in [section 7](#7-measured-performance).

Consequences of mishandling this, measured live:

- Without the conversion, the `daily` window for the four `fechaReg` endpoints would return almost nothing, and every wider window would drop its most recent day.
- With chunking (see section 3), the error compounds: one day is lost per chunk boundary. A 28-day range chunked by day returned 8 rows instead of ~1.2 million.

## 3. Windows are chunked into 7-day pieces

Every window is split into pieces of at most 7 days before being queried (`generic.iter_date_chunks`). The `daily` and `weekly` windows fit in a single piece and are unaffected; `monthly` and `annual` are chunked. Two reasons, both verified against `concesiones_busqueda`:

- **Reliability.** A 4-year range (27.4 million rows) returns `ERR_MANTENIMIENTO_BBDD` intermittently at any page depth. A one-week window over the same dates did not fail once in 6 attempts.
- **Speed.** A 30-day range queried in a single call took 286.7 s; the same range chunked into weeks took 142.5 s, both without errors.

### The result does not depend on chunk size

Because the date conversion is applied per piece, the result is invariant to chunk size: a 14-day `partidospoliticos_busqueda` range returns exactly the same 36 rows whether chunked into 1-, 7-, or 14-day pieces (verified live).

The 7-day size is not speed-critical either: over a fixed 14-day `concesiones_busqueda` range (~530,000 rows), chunk sizes of 1, 3, 7, and 14 days took 51, 41, 47, and 57 s respectively — differences within the service's load noise, with no errors at any size. The 7-day size is kept as a balance: fast, reliable, and aligned with the weekly window.

## 4. Window-boundary verification

To rule out both an overlap (fetching one day too many) and a gap (dropping a day), it was verified live, across all 5 incremental entities, that two consecutive days `X` and `X+1`, queried through the real production path with the correct per-family conversion, satisfy two properties:

1. `fetch(X)` and `fetch(X+1)` are **disjoint** (zero overlap).
2. Their union is exactly `fetch([X, X+1])` (**additivity**).

The counts reconcile row by row: for `concesiones`, 115,862 + 68,457 = 184,319 rows, with no overlap. An extra `+1` on the exclusive family, or a misapplied bound on the inclusive one, would have double-counted the boundary day; a dropped day would have broken the union. The invariant is fixed as a permanent test in `tests/test_generic.py`.

## 5. Window-scoped deletion detection

The entities `concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda`, `convocatorias_busqueda`, and `convocatorias` detect real deletions by comparing, within the same run, what was fetched from the API against the table rows whose own registration date (`fechaAlta`, `fechaRegistro`, or `fechaRecepcion`, depending on the entity) falls in the same range.

The comparison is never made against the previous run: that would produce constant false positives, because every row eventually ages out of a rolling window without that meaning a deletion.

`partidospoliticos_busqueda` is excluded from deletion detection: it was confirmed live, with more than 70 real rows across two different date ranges, that its payload does not expose any registration-date field. The official documentation states that this endpoint "works the same, with the same filters and results" as `concesiones_busqueda`; in practice it does not. This is a permanent limitation unless the API changes.

## 6. Historical depth per endpoint

The reach of a full historical load is determined by the API's data retention per endpoint, measured live:

| Entity | Data available back to ~ | Bounded by |
|---|---|---|
| `concesiones_busqueda` | ~4 years | 4 calendar-year retention |
| `partidospoliticos_busqueda` | ~4 years | (tracks concesiones) |
| `ayudasestado_busqueda` | ~9-10 years | 10-year retention |
| `minimis_busqueda` | ~10 years | 10-year retention |
| `convocatorias_busqueda` | ~12 years | (tracks `convocatorias`, same discovery source) |
| `convocatorias` | ~12 years | Portal start (~2014) |

These dates are not encoded in `bdns-sync`: the tool is a pure primitive and does not know each endpoint's historical depth. Just as `scripts/delta_load.sh` owns the cadence, `scripts/full_load.sh` owns the start dates and passes them via `--since`. Querying dates before the retention limit simply returns empty weeks (one cheap call each), so the script's dates are conservative floors, not exact first records.

## 7. Measured performance

Live-measured figures behind design decisions. Operational details live next to the code (`bdns/sync/sinks/sql/dialects.py`, `bdns/sync/pipeline.py`); this is the evidence record.

### Rate limit and the parallel detail step

The official limit is 10 requests/second per IP. The client's token bucket honors it as an average, but starts full: a fresh thread pool fires its first requests simultaneously and the server 429s the burst (confirmed live: 10 workers through the token bucket alone died within seconds). The same server accepts a sustained 9.8 req/s with zero 429s when request *starts* are spaced (confirmed at 100 ms); the spacing used is 105 ms.

With one real month of `convocatorias` (May 2026, 6,186 codes): the sequential detail step took between 23 minutes and 3 h 12 min depending on server load (0.2-1.9 s/call); in parallel (8 workers, paced starts) it took 10 min 54 s, with zero 429s.

### Producer/consumer overlap

Staging overlaps the fetch of the next batch with the write of the current one (`bdns/sync/pipeline.py`): +40% measured on fetch-heavy endpoints. The fetch runs on the helper thread and writes on the connection-owning thread because SQLite's DBAPI objects are thread-affine; the bounded queue provides backpressure.

### Long-range reliability

A 7-day range against `concesiones_busqueda` pulled 147,856 rows with zero errors; a 4-year range failed intermittently with `ERR_MANTENIMIENTO_BBDD` at every page depth. Hence the universal 7-day chunking (see [section 3](#3-windows-are-chunked-into-7-day-pieces)).

### Client retries

`bdns-fetch`'s defaults (3 retries, 2 s fixed wait) give up after ~1 minute of server trouble: a real multi-hour backfill died to a single request exhausting its 3 attempts. 8 × 15 s rides out a ~2-minute rough patch; the only cost is extra delay before a genuinely permanent failure.

## 8. Known API issues

Every entry follows the same order: what the API does, what we observed, and what `bdns-sync` does about it. The rest of the project (README, code comments) links here instead of repeating the explanation.

- **Individual malformed records.** The backend sometimes rejects a specific record and returns an HTML error page instead of JSON. It is not a rate limit or a parameter problem: the calls immediately before and after the same record work. In `planesestrategicos`, between 8 July and 30 August 2026, the same 10 `idPES` values failed on all 57 runs, always with the same HTML page; on 30 August there were 114 out of 2,029 keys, so a broken record tends to stay broken but the set is not fixed. `bdns-sync` discards the record with a warning, counts it in `_sync_runs.rows_skipped`, and stores the content in `_sync_errors`, linked to the run.
- **`ERR_MANTENIMIENTO_BBDD` on long ranges.** Multi-year ranges fail intermittently, at every page depth. A 4-year range over `concesiones_busqueda` (27.4M rows) failed repeatedly, while a weekly window over those same dates did not fail once in 6 attempts. `bdns-sync` splits every query into 7-day chunks; see [section 3](#3-windows-are-chunked-into-7-day-pieces).
- **Inconsistent date semantics across endpoints.** `fechaRegFin` is exclusive and `fechaHasta` is inclusive, and the official documentation does not say so. Querying the same day `D`, `fechaRegFin=D` returns ~0 rows and `fechaRegFin=D+1` returns the whole day, while `fechaHasta=D` does return day `D` in full. `bdns-sync` centralizes the conversion in `generic.to_api_upper_bound` and applies it only to the exclusive family; see [section 2](#2-upper-bound-semantics-per-endpoint).
- **`partidospoliticos_busqueda` has no registration date.** Its payload exposes no registration-date field, although the official documentation claims this endpoint works the same as `concesiones_busqueda`. Confirmed with more than 70 real rows across two different date ranges. Without that field deletion detection is impossible, so `bdns-sync` leaves this entity out of it; see [section 5](#5-window-scoped-deletion-detection).
- **Unstable beneficiary name in `grandesbeneficiarios_busqueda`.** For one `idPersona`, the API changes the spelling of the name from one hour to the next, with the rest of the record identical. Measured on 30 August 2026: three consecutive fetches within four minutes returned all 148,170 names identical, yet 79,000 rows changed between the 00:03 run and the 15:20 one, which points to a cache or a periodic re-aggregation at the source rather than per-request randomness. For `idPersona=7818535`, six variants of the same company name were observed over eleven days (`M&M, S.L.`, `M M S.L.`, `MM SL`, `M&M S.L.`, `M&M SOCIEDAD LIMITADA`, with and without a trailing dot), always with the same amount; the name is probably assembled from the underlying grant records, where each granting body typed it its own way. With that field inside the hash, 30% to 60% of the table was re-versioned every day: 3.7M history rows for 148,000 current records, 25 versions per key in 53 days. `bdns-sync` excludes the field from the hash (`exclude_from_hash` in the syncer): it is still stored whole in the payload, it just stops counting as a change. It is neither the only case nor the only shape this takes: `concesiones_busqueda` has the same problem in its own `beneficiario` field, and `minimis_busqueda` and `ayudasestado_busqueda` a different variant. The detail, with per-entity measurements, is in [section 9](#9-spurious-changes-the-same-data-written-differently).
- **Nondeterministic order of nested arrays.** `regiones` returns the same tree with `children` in a different order across calls, with no data actually changed. `bdns-sync` sorts object keys and array elements recursively before hashing, so no spurious versions are produced. The same disorder shows up inside delimited strings, where canonicalization cannot reach; see [section 9](#9-spurious-changes-the-same-data-written-differently).
- **Bursts rejected even when the average respects the limit.** The server returns `429` when several requests start at once, even when the average stays under the official 10 req/s. A pool of 10 threads respecting only the average died within seconds, while the same server accepted a sustained 9.8 req/s with spaced starts. `bdns-sync` spaces request starts 105 ms apart; see [section 7](#7-measured-performance).
- **Limited retention, different per endpoint.** Available data ranges from ~4 years (`concesiones_busqueda`) to ~12 (`convocatorias`), depending on the entity. `bdns-sync` does not hardcode those dates — querying further back only returns empty weeks, which are cheap calls — the operator's script decides them via `--since`; see [section 6](#6-historical-depth-per-endpoint).
- **Pagination instability against dates still receiving new registrations.** If the result set changes while a wide window is being paginated, because new grants come in, offset-based pagination can repeat rows near a page boundary across two consecutive pages. It only affects recent dates, never ranges already closed, whose pagination is stable. `bdns-sync` deduplicates at insertion time, so normal syncs leave no duplicates; a large historical load in a single pass can leave a residual pair. How to detect and clean it: [`data-caveats.en.md`](data-caveats.en.md).

## 9. Spurious changes: the same data written differently

SCD2 versioning creates a new version whenever the payload hash changes. If the API returns the same data written differently from one call to the next, the result is a version that carries no information: the record did not change and no correction was made, only the way the response was assembled.

Measured over the annual pass of 1 September 2026, comparing every new version against the one it closed:

| Entity | Versions | Spurious | Culprit field |
|---|---|---|---|
| `concesiones_busqueda` | 368,818 | **213,176 (58%)** | `beneficiario` |
| `minimis_busqueda` | 35,995 | **30,033 (83%)** | `sectorActividad` |
| `ayudasestado_busqueda` | 6,758 | **5,046 (75%)** | `sectores` |
| `grandesbeneficiarios_busqueda` | ~65,000 per day | **~100%** | `beneficiario` |
| `convocatorias` | 2,366 | 0 | — |
| `convocatorias_busqueda` | 437 | 13 (3%) | — |
| `partidospoliticos_busqueda` | 21 | 1 | — |

Of the 414,395 versions the annual pass produced, around 248,000 are noise: 60%. Real corrections come to about 166,000.

### Family 1: the name is rebuilt inconsistently

Affects `concesiones_busqueda` and `grandesbeneficiarios_busqueda`. For the same beneficiary, with the same amount and the same identifier, the name field comes back written differently:

```
GONZALEZ                      →  GONZÁLEZ            (accents, in both directions)
REMEDIOS BENITEZ BASILIO .    →  REMEDIOS BENITEZ BASILIO . .
MONTSERRAT LOPEZ REYNOSO MECA →  MONTSERRAT LOPEZ-REYNOSO MECA
LIMMAT M&M, S.L.              →  LIMMAT MM SL        (six variants in eleven days)
```

In `concesiones_busqueda`, all 230,878 `beneficiario` changes keep **the same `idPersona` in 100% of cases**, and 213,176 are identical once accents and punctuation are stripped. It is never a different person: it is the same one written another way. The name is probably assembled from the underlying records, where each granting body typed it its own way.

### Family 2: shuffled lists inside a string

Affects `minimis_busqueda` and `ayudasestado_busqueda`. The field carries several values concatenated together and their order changes between calls, with the same elements:

```
minimis_busqueda      sectorActividad, separator ";"
  '52.3 - Transport intermediation; 52.2 - Auxiliary transport activities'
  '52.2 - Auxiliary transport activities; 52.3 - Transport intermediation'

ayudasestado_busqueda sectores, separator "#"
```

This is the same root cause as the nondeterministic array order in `regiones` (see [section 8](#8-known-api-issues)), but the hash canonicalization cannot fix it: it sorts object keys and JSON array elements, and here the list travels inside a single text value, so it is seen as just another string.

### Family 3: fields that stop coming back and then return

A field that normally carries a value comes back `null` on one call and populated on the next. Measured over 3,000 `convocatorias` pairs and as many for the rest:

| Entity | Field | `null→value` | `value→null` | % of pairs |
|---|---|---|---|---|
| `convocatorias` | `fechaInicioSolicitud` | 209 | 55 | 8.8% |
| `convocatorias` | `fechaFinSolicitud` | 123 | 61 | 6.1% |
| `convocatorias` | `textInicio` | 40 | 47 | 2.9% |
| `convocatorias` | `textFin` | 48 | 32 | 2.7% |
| `convocatorias_busqueda` | `descripcionLeng` | 18 | 17 | 6.4% |
| `convocatorias` | `descripcionLeng` | 13 | 14 | 0.9% |
| `convocatorias` | `sedeElectronica` | 6 | 7 | 0.4% |
| `minimis_busqueda` | `sectorActividad` | 23 | 40 | 2.1% |

The symmetric splits (`textInicio` 40 against 47, `descripcionLeng` 18 against 17) give away that this is not information being filled in. The one-directional ones are: `reglamento` (8 and 0), `urlAyudaEstado` (3 and 0) and `ayudaEstado` (3 and 0) are fields that get populated and stay that way.

**The nulls arrive in blocks, not one at a time.** Among the `convocatorias` pairs where some field goes `null`, 81 lose two fields at once and only 51 lose one. And the ones that fall together are paired up:

```
54 pairs:  fechaInicioSolicitud + fechaFinSolicitud
25 pairs:  textInicio + textFin
```

That is the whole application-period block, dates and texts, disappearing and coming back. It points to partial responses from the backend on the detail endpoint rather than fields flapping on their own.

**This family cannot be fixed with hashing rules**, unlike the previous two. A `null` cannot be normalized away: either it counts as a change, or the field is excluded and detection of a deadline actually being set is lost, which is legitimate information. The versions it produces are accepted as valid; the volume is small, around 650 of the 4,320 closed versions in `convocatorias`.

What is worth knowing when consuming the data is that **the record is truthful but invites a false reading**: it looks as though a call had its application period removed one day and restored another, when no administrative change took place. See [`data-caveats.en.md`](data-caveats.en.md).

It also leaves a lesson for the engine: the API **can return `null` in fields that normally carry values**. Today none of them is critical — `fechaRecepcion`, the registration date for `convocatorias`, is not on the list — but if the block that drops ever includes one, the run breaks; see the record-validation entry in the [roadmap](roadmap.en.md).

### What is not affected

`convocatorias` and `convocatorias_busqueda` show no appreciable noise, which is worth stating because they share a source with the rest. Their changes are genuinely administrative: budgets going up (€25,000 → €40,000), application deadlines extended, documents added, and bodies reorganized (336 of their 437 versions change `nivel3`, spread across 80 distinct bodies: a secretaría general turning into a dirección general drags all of its calls with it). That is exactly what a history should record.

That the concesiones family is affected and the convocatorias family is not suggests the problem is not the API in general, but how the response is assembled in specific endpoints.

### How it was measured

Two separate checks, both over (closed version, new version) pairs from the same run:

- **Formatting**: normalize both payloads to NFD, strip diacritics and everything non-alphanumeric, then compare. If they match, the change was one of spelling.
- **Reordering**: split the field on its separator, sort the pieces alphabetically, rejoin and compare. If they match, the list was merely shuffled.

The first check does not catch the second, because shuffling a list changes the character sequence. Both were needed.
