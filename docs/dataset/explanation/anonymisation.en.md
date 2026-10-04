# How natural persons are protected

The dataset holds no personal data. It may identify companies and public bodies, but never a natural person, and this page explains how, with examples. The why, with the legal framework and the alternatives that were turned down, is in the [design decision](../../adr/0002-anonymised-dataset.md).

<a id="who"></a>
## Which beneficiaries are protected

Each beneficiary is classified by the tax ID at the start of the `beneficiario` field, never by its name, because a company may be named like a person and the other way round. Anything not recognised is treated as a natural person. For example (names and tax IDs are made up):

| How it appears in the BDNS | `tipo_persona` | In the dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | `persona_fisica` | Summary only |
| `12345678Z NOMBRE APELLIDOS` | `persona_fisica` | Summary only |
| `E12345678 APELLIDO Y APELLIDO CB` | `comunidad_o_sociedad_civil` | Summary only |
| `123456789012 FOREIGN COMPANY LTD` | `desconocido` | Summary only |
| `B12345678 EMPRESA DE EJEMPLO SL` | `persona_juridica` | Record by record |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | `entidad_publica` | Record by record |

Communities of property and civil partnerships have a tax ID of their own, but are usually named after their members, so they are protected like natural persons.

Companies and public bodies are published record by record, with their tax ID and name, since they are not personal data. Even so, two fields are dropped from their awards: `urlBR`, because the bulletin it links to usually names natural persons too, and `idPersona`, which adds nothing the tax ID does not already say.

<a id="summary"></a>
## What is published about a call

Of the awards to protected beneficiaries, only one summary per call is published (and per instrument, if the call uses several). Picture a call with these 12 awards, which belong to 11 people because one of them got two:

| Amount | Awards | Award date |
|---:|---:|---|
| €300 | 4 | 12/03/2026 |
| €450 | 3 | 20/04/2026 |
| €600 | 3 | two on 20/04/2026 and one on 05/06/2026 |
| €900 | 1 | 05/06/2026 |
| €1,200 | 1 | 05/06/2026 |

Its row in `concesiones_personas` would be this:

| Column | Value |
|---|---|
| `concesiones` | 12 |
| `beneficiarios` | 11 |
| `importe_total` | 6,450.00 |
| `importe_media` | 537.50 |
| `importe_desviacion` | 274.79 |
| `importe_p25`, `importe_mediana`, `importe_p75` | 300.00, 450.00 and 600.00 |
| `fecha_p25`, `fecha_mediana`, `fecha_p75` | 2026-03-12, 2026-04-20 and 2026-04-20 |
| `importe_p10`, `importe_p90`, `fecha_p10`, `fecha_p90` | Empty, because there are fewer than 20 people |

With it you can tell how much the call gave out, what a typical award was and when they were awarded, but not who got what. Nor do the €1,200 of the largest award appear, since they are one specific person's.

<a id="rules"></a>
## The rules

**Every row gathers at least 10 people.** With few people, a summary lets you guess what each one got. With two, for example, whoever knows what one got learns the other's by subtracting it from the total.

**No one holds more than half their row's amount.** If one person takes nearly everything, the total is practically their amount, however many others the row gathers. With 14 awards of €100 and one of €10,000, the total (€11,400) tells anyone who knows the call how much that person got.

**The smallest and largest values are never published, and the 10th and 90th percentiles only from 20 people.** The largest amount is one specific person's, and so are the smallest and the extreme dates. The 10th and 90th percentiles sit very close to them: in the example above, the 90th percentile would be €870, very close to the second largest award (€900). From 20 people on, the 10th percentile no longer falls below the second smallest award, nor the 90th above the second largest.

**Dates are real dates.** Date percentiles are picked among the award dates that exist, without interpolating, because a day halfway between two dates means nothing.

**What falls short goes into its year's rest row.** The awards of calls that cannot be published are gathered into one row with `es_resto = true`, which does not say which calls it holds, and in `ejercicio` carries the year of each one's median award date. That row must meet the same rules and also gather at least two calls, because with only one, the rest would be that call under another name.

**Each person counts once.** A person is recognised by their BDNS identifier or, where it is missing, by the whole `beneficiario` field, and neither leaves the private file.

Every statistic covers every award in its row, and no other table summarises the same awards, so nothing can be learnt by subtracting one from the other. The thresholds are defined once, in the SQL, and the [reference](../reference/build.md#thresholds) gives their values.

<a id="checks"></a>
## What is checked before publishing

Before writing any file, the build checks what it is about to publish and **stops** if it finds:

- a protected beneficiary in a record-level table;
- anything shaped like a DNI, NIE or masked tax ID, in any column of any table;
- a column that identifies someone in the summary, such as `beneficiario`, `id_persona`, `url_br` or `cod_concesion`;
- a summary row with fewer than 10 people, or with the 10th or 90th percentiles and fewer than 20.

It reports what it finds without cleaning it up, because such a finding points to a fault in an earlier step, and quietly cleaning it would hide it behind a dataset that looks right. Each check's message is in the [reference](../reference/build.md#checks).

## What the dataset does not allow

- Following a natural person over time, or knowing what a specific person got. That is exactly the aim, even though it limits some analyses.
- Matching the natural-person totals to the cent, because whatever reaches no publishable row is missing.
- Reading a summary call's title when it holds something shaped like a DNI, because it is published empty.
