# API behaviour

How the BDNS API actually behaves, checked against the live service. None of this is in the [official documentation](https://www.infosubvenciones.es/bdnstrans/api), or it contradicts it, and each point loses or duplicates data silently when mishandled.

Each claim names the measurement behind it. Most were made while building [`bdns-sync`](https://cruzlorite.github.io/bdns-sync/en/), which downloads the whole API every day; this page is their home because they are about the API, not about storage. What `bdns-sync` does about each one is in its own documentation.

<a id="upper-bound"></a>
## The two date filters disagree on the upper bound

The API has two families of date parameters, and the upper bound behaves the **opposite** way in each:

| Family | Parameters | Endpoints | Upper bound | Checked (day `D`) |
|---|---|---|---|---|
| Registration date | `fechaRegInicio` / `fechaRegFin` | `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda`, `partidospoliticos-busqueda` | **Exclusive** | `fechaRegFin=D` returns ~0 rows of day `D`; `fechaRegFin=D+1` returns all of it (on `concesiones`, 1 row against 58,488) |
| Period | `fechaDesde` / `fechaHasta` | the other searches, `convocatorias-busqueda` among them | **Inclusive** | `fechaHasta=D` returns every call with `fechaRecepcion == D`; `fechaHasta=D+1` returns `D` and `D+1` |

Getting it wrong is expensive. Without adding a day to `fechaRegFin`, a one-day query returns almost nothing and any wider range loses its last day. Splitting a range multiplies the error, one day per boundary: a 28-day range split into days returned 8 rows instead of ~1.2 million.

`bdns-fetch` keeps the parameters exactly as the API defines them, and offers [`registration_range`][bdns.fetch.dates.registration_range] and [`period_range`][bdns.fetch.dates.period_range]: they take an inclusive `[first, last]` range and return the right arguments for each family.

<a id="range-reliability"></a>
## Long ranges fail; week-long ones do not

Measured on `concesiones-busqueda`:

- **Reliability.** A 4-year range (27.4 million rows) returns `ERR_MANTENIMIENTO_BBDD` intermittently, at any page depth. A weekly window over the same dates did not fail once in 6 attempts, and a 7-day range pulled 147,856 rows without errors.
- **Speed.** A 30-day range queried at once took 286.7 s; split into weeks, 142.5 s. Neither errored.

The exact piece size is not critical. Over a fixed 14-day range (~530,000 rows), pieces of 1, 3, 7 and 14 days took 51, 41, 47 and 57 s, differences within the service's load noise. Seven days is a good balance, and it is what [`split_range`][bdns.fetch.dates.split_range] uses by default ([`MAX_RANGE_DAYS`][bdns.fetch.dates.MAX_RANGE_DAYS]).

Nor does the result depend on the piece size, as long as each piece's upper bound is handled right: a 14-day range of `partidospoliticos-busqueda` returns the same 36 rows split into pieces of 1, 7 or 14 days.

<a id="boundary-check"></a>
## Consecutive days: disjoint and additive

To rule out both an overlap (fetching a day too many) and a gap (losing one), the five incremental searches were checked for two properties of consecutive days `X` and `X+1`, each queried with its family's correct upper bound:

1. they are **disjoint**: no record appears in both;
2. their union is exactly the query for `[X, X+1]` (**additivity**).

The counts match row for row: on `concesiones`, 115,862 + 68,457 = 184,319, with no overlap.

These two properties, plus each bound's semantics, are what [`check_api_contract`][bdns.fetch.contract.check_api_contract] (`bdns-fetch check-api`) checks against the live service. Unit tests can only pin our model of the API; this check is what notices when the API changes.

<a id="rate-limit"></a>
## The rate limit rejects bursts

The official limit is 10 requests per second per IP. On top of that, the server answers `429` when several requests **start at once**, even with the average under the limit: 10 threads that only respected the average died within seconds. The same server accepts a sustained 9.8 requests per second when their starts are spaced (tested at 100 ms apart).

That is why `bdns-fetch`'s limiter ([`RateLimiter`][bdns.fetch.utils.RateLimiter]) spaces requests instead of allowing bursts, with a margin by default: 9.5 per second, one every ~105 ms. The limit is per IP: several processes on one IP share it and must split it (`--rate-limit`).

<a id="latency"></a>
## Latency varies with load

The latency of a simple call, such as a call-for-applications detail, depends heavily on server load: ~0.22 s per call at good times, ~1.9 s at bad ones. One batch of 6,186 details (May 2026) took between 23 minutes and 3 h 12 min sequentially; in parallel, with 8 threads and spaced starts, 10 min 54 s, without a single `429`.

<a id="history-depth"></a>
## Retention differs per endpoint

How far back the data goes is set by each endpoint's retention:

| Endpoint | Data available | Limited by |
|---|---|---|
| `concesiones-busqueda` | ~4 years | 4 calendar years of retention |
| `partidospoliticos-busqueda` | ~4 years | follows concesiones |
| `ayudasestado-busqueda` | ~9-10 years | 10 years of retention |
| `minimis-busqueda` | ~10 years | 10 years of retention |
| `convocatorias-busqueda`, `convocatorias` | ~12 years | portal start (~2014) |

Asking for earlier dates is not an error: it returns empty weeks, one cheap call each.

<a id="api-issues"></a>
## Known issues

- **Occasional malformed records.** The backend sometimes rejects one specific record and returns an HTML error page instead of JSON. It is neither rate limiting nor a parameter problem: the calls right before and after succeed. On `planesestrategicos`, between 8 July and 30 August 2026, the same 10 `idPES` failed in all 57 runs; on 30 August it was 114 out of 2,029. A broken record tends to stay broken, but the set is not fixed.
- **Errors inside a 200 response.** Some errors arrive with status 200 and a `{"codigo": ..., "error": ...}` body. `bdns-fetch` treats them as errors.
- **`ERR_MANTENIMIENTO_BBDD` on long ranges.** See [above](#range-reliability). `bdns-fetch` treats it as transient and retries it.
- **Inconsistent date semantics.** `fechaRegFin` exclusive, `fechaHasta` inclusive, which the official documentation does not say. See [above](#upper-bound).
- **`partidospoliticos-busqueda` has no registration date.** Its payload carries no registration-date field, although the official documentation says it works like `concesiones-busqueda`. Checked against 70+ real rows across two date ranges.
- **Nested arrays in changing order.** `regiones` returns the same tree with its `children` in a different order between calls, with no data changed.
- **Unstable pagination on dates still receiving records.** Pagination is by offset. If new records arrive while a recent range is being paged through, a row near a page edge can come in two consecutive pages. Closed ranges page stably.
- **`terceros` is redundant.** The [official good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) advise against it: `concesiones-busqueda` already carries the beneficiary data.

<a id="spurious-changes"></a>
## The same data, written differently

Between one call and the next, the API can return an identical record written another way. There was no administrative correction: only how the response was composed changed. For anyone keeping history (as `bdns-sync` does) this produces false versions; in `bdns-sync`'s annual pass of 1 September 2026, 60% of new versions were of this kind. There are three families.

<a id="unstable-names"></a>
### Names rebuilt unstably

The `beneficiario` field of `concesiones-busqueda` and `grandesbeneficiarios-busqueda` comes back written differently for the same beneficiary, with the same amount and the same identifier:

```
GONZALEZ                      →  GONZÁLEZ            (accents, both ways)
REMEDIOS BENITEZ BASILIO .    →  REMEDIOS BENITEZ BASILIO . .
MONTSERRAT LOPEZ REYNOSO MECA →  MONTSERRAT LOPEZ-REYNOSO MECA
LIMMAT M&M, S.L.              →  LIMMAT MM SL        (six variants in eleven days)
```

On `concesiones-busqueda`, 230,878 changes of `beneficiario` keep **the same `idPersona` in 100% of cases**, and 213,176 are identical once accents and punctuation are removed. The value also **oscillates**: it returns to spellings it already had (`ASOCIACIÓN INCLUDD → ASOCIACION INCLUDD → ASOCIACIÓN INCLUDD`). On `grandesbeneficiarios-busqueda`, three downloads within four minutes returned all 148,170 names identical, but between 00:03 and 15:20 on the same day 79,000 changed: a periodic re-aggregation at the source, not per-request randomness. The name is probably composed from the underlying records, where each body typed it its own way.

<a id="shuffled-lists"></a>
### Lists shuffled inside a string

`sectorActividad` on `minimis-busqueda` (separated by `;`) and `sectores` on `ayudasestado-busqueda` (separated by `#`) carry several concatenated values in an order that changes between calls, with the same elements:

```
'52.3 - Intermediación del transporte; 52.2 - Auxiliares del transporte'
'52.2 - Auxiliares del transporte; 52.3 - Intermediación del transporte'
```

Careful when splitting: on `minimis` several CNAE descriptions carry a `;` of their own ("Administración Pública y defensa; Seguridad Social obligatoria"), so splitting at every `;` cuts 374 of 15,931 elements in half. Split before the start of each element instead (a code followed by a hyphen). On `ayudasestado`, `#` is unambiguous.

<a id="intermittent-fields"></a>
### Fields that disappear and come back

A field that normally has a value comes back `null` in one call and filled in the next. Measured over 3,000 version pairs of `convocatorias` and as many of the others:

| Endpoint | Field | `null→value` | `value→null` | % of pairs |
|---|---|---|---|---|
| `convocatorias` | `fechaInicioSolicitud` | 209 | 55 | 8.8% |
| `convocatorias` | `fechaFinSolicitud` | 123 | 61 | 6.1% |
| `convocatorias` | `textInicio` | 40 | 47 | 2.9% |
| `convocatorias` | `textFin` | 48 | 32 | 2.7% |
| `convocatorias-busqueda` | `descripcionLeng` | 18 | 17 | 6.4% |
| `convocatorias` | `descripcionLeng` | 13 | 14 | 0.9% |
| `convocatorias` | `sedeElectronica` | 6 | 7 | 0.4% |
| `minimis-busqueda` | `sectorActividad` | 23 | 40 | 2.1% |

Symmetric splits give away that this is not information being completed. And the nulls arrive together: 54 pairs lose `fechaInicioSolicitud` and `fechaFinSolicitud` at once, and 25 lose `textInicio` and `textFin`. It is the whole application-period block disappearing and coming back, which points at partial responses from the detail endpoint's backend. A field that is normally filled **can arrive `null`**.

### What is not affected

`convocatorias` and `convocatorias-busqueda` show no name or list noise: their changes are genuinely administrative (budgets going up, deadlines extended, documents added, bodies reorganised). The problem lies in how a few specific endpoints compose their responses, not in the API at large.

### How it was measured

Over pairs (previous version, new version) of the same record:

- **Formatting**: normalise both payloads to NFD, strip diacritics and anything non-alphanumeric, and compare.
- **Reordering**: split the field at its separator, sort the pieces, join them back and compare.

The first does not catch the second, since shuffling a list changes the character sequence.
