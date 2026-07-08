# BDNS API behavior: date windows

[🇪🇸 Spanish version](./api-behavior.md)

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

Consolidated list of the API's problematic behaviors, all verified live. The rest of the project (README, code comments) links here instead of repeating each explanation.

- **Individual malformed records.** The backend sometimes rejects a specific record with an HTML error page instead of JSON. It is not a rate limit or a parameter problem: the calls immediately before and after the same record work. `bdns-sync` discards the record with a warning, counts it in `_sync_runs.rows_skipped`, and stores it in `_sync_errors`.
- **`ERR_MANTENIMIENTO_BBDD` on long ranges.** Multi-year date ranges fail intermittently at every page depth. Every query is therefore chunked into 7-day pieces; see [section 3](#3-windows-are-chunked-into-7-day-pieces).
- **Inconsistent date semantics across endpoints.** `fechaRegFin` is exclusive and `fechaHasta` is inclusive, and the official documentation does not say so. See [section 2](#2-upper-bound-semantics-per-endpoint).
- **`partidospoliticos_busqueda` has no registration date.** Its payload exposes no registration-date field, although the official documentation claims it works the same as `concesiones_busqueda`. Without that field, deletion detection is impossible. See [section 5](#5-window-scoped-deletion-detection).
- **Nondeterministic order of nested arrays.** `regiones` returns the same tree with `children` in a different order across calls, with no actual change. `bdns-sync`'s canonical hash sorts keys and array elements recursively to avoid spurious versions.
- **Bursts rejected even when the average respects the limit.** The server returns `429` to a simultaneous batch of request starts even when the average stays under 10 req/s. Starts are spaced 105 ms apart; see [section 7](#7-measured-performance).
- **Limited retention per endpoint.** Between ~4 and ~12 years depending on the entity. See [section 6](#6-historical-depth-per-endpoint).
- **Pagination instability against dates still receiving new registrations.** If the underlying result set changes (new grants registered) while a wide window is being paginated, offset-based pagination can repeat rows near a page boundary across two consecutive pages. `bdns-sync` deduplicates at insertion time, so normal syncs leave no duplicates; a large historical load can leave a residual pair. Only affects recent dates, never ranges already closed. How to detect and clean it: [`data-caveats.en.md`](data-caveats.en.md).
