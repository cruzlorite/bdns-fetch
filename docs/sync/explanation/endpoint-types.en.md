# Endpoint types

There are two families, determined by data volume.

## Full replace (`bdns-sync sync <entity>`)

Small catalogs, where fetching the complete set on every run is affordable.

They come in three shapes:

- **One call**, since they need no parameters: `sectores`, `actividades`, `finalidades`, `beneficiarios`, `instrumentos`, `objetivos`, `regiones` and `sanciones_busqueda`.
- **Swept over a parameter**, since the API does not return everything when it is omitted: `organos` and `organos_agrupacion` sweep `idAdmon`, and `reglamentos` sweeps `ambito`. Each value is queried separately and the results are merged into one table.
- **Listing first, then detail**, since the listing does not carry every field: `planesestrategicos_busqueda`, `planesestrategicos` and `planesestrategicos_vigencia`, and also `grandesbeneficiarios_anios` and `grandesbeneficiarios_busqueda`.

## Registration-date incremental (`bdns-sync sync <entity> --window {daily,weekly,monthly,annual}`)

Endpoints with tens of millions of rows, where full replacement is not viable.

| Entity | Natural key |
|---|---|
| `concesiones_busqueda` | `id` |
| `ayudasestado_busqueda` | `idConcesion` |
| `minimis_busqueda` | `idConcesion` |
| `partidospoliticos_busqueda` | `id` |
| `convocatorias_busqueda` | `numeroConvocatoria` |
| `convocatorias` | `codigoBDNS` |

`convocatorias` is a two-step case: discovery queries the `convocatorias_busqueda` listing by date range to collect the codes registered in the window, and each discovered code is then fetched in full through the detail endpoint (`convocatorias`, by `numConv`). The detail record is what gets versioned into the `convocatorias` table; the discovery listing is also synced as its own table, `convocatorias_busqueda`, through the same incremental machinery as the rest of this section.

`convocatorias_busqueda` does **not** replace `convocatorias`: the listing carries only 10 of the ~30 detail fields (no budget, application dates, documents, instruments, etc.), and its hash staying the same says nothing about whether a detail-only field changed. Never use the listing to decide whether a code's detail fetch can be skipped.

The detail step of `convocatorias` is the expensive one: one real API call per discovered code, with no pagination possible. By default calls are made one at a time, as the official good practices ask. While the server answers fast it does not matter, since the rate limit sets the pace; when it is loaded, `--max-workers` allows several at once and cuts the time a lot (figures in [performance](sync-behavior.md#performance)). The same machinery ([`bdns.sync.pipeline`](../reference/api/pipeline.md)) drives the detail steps of `planesestrategicos` and `planesestrategicos_vigencia`.

A record's registration date does not change when the record is edited, so re-querying the same window later finds no new additions, but does detect edits via the hash. Corrections cluster near the registration date and taper off with age; hence the window cascade: every level reaches back to yesterday ([`window_bounds`][bdns.sync.windows.window_bounds]), so `annual` contains `monthly` contains `weekly` contains `daily` on any given day. Which window `bdns-sync delta` runs on which day ([`cadence_window`][bdns.sync.windows.cadence_window]), and why they are never stacked, is in [scheduled operation](../guides/scheduling.md).
