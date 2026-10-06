# How natural persons are protected

The dataset holds no personal data. It may identify companies and public bodies, but never a natural person, and this page explains how, with examples. The why, with the legal framework and the alternatives that were turned down, is in the [design decision](../adr/0020-anonymised-dataset.md).

<a id="who"></a>
## Which beneficiaries are protected

Each beneficiary is classified by the tax ID at the start of the `beneficiario` field, never by its name, because a company may be named like a person and the other way round. Anything not recognised is treated as a natural person. For example (names and tax IDs are made up):

| How it appears in the BDNS | `tipoPersona` | In the dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | `persona_fisica` | Summary only |
| `12345678Z NOMBRE APELLIDOS` | `persona_fisica` | Summary only |
| `E12345678 APELLIDO Y APELLIDO CB` | `comunidad_o_sociedad_civil` | Summary only |
| `123456789012 FOREIGN COMPANY LTD` | `desconocido` | Summary only |
| `B12345678 NOMBRE APELLIDOS 12345678Z SL` | `persona_juridica` | Summary only |
| `B12345678 EMPRESA DE EJEMPLO SL` | `persona_juridica` | Record by record |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | `entidad_publica` | Record by record |

Communities of property and civil partnerships have a tax ID of their own, but are usually named after their members, so they are protected like natural persons. So are companies and associations whose `beneficiario` field carries a person's DNI, which the BDNS does for companies named after their partner and for some that add their representative's details. Removing only the DNI would not do, because the person's name usually sits next to it.

Companies and public bodies are published record by record, with their tax ID and name, since they are not personal data. Even so, two fields are dropped from their awards: `urlBR`, because the bulletin it links to usually names natural persons too, and `idPersona`, which adds nothing the tax ID does not already say.

<a id="summary"></a>
## What is published about a call

Of the awards, state aid and de minimis aid to protected beneficiaries, only one summary per call is published (and per instrument, if the call uses several). Picture a call with these 12 awards, which belong to 11 people because one of them got two:

| Amount | Awards | Award date |
|---:|---:|---|
| €300 | 4 | 12/03/2026 |
| €450 | 3 | 20/04/2026 |
| €600 | 3 | two on 20/04/2026 and one on 05/06/2026 |
| €900 | 1 | 05/06/2026 |
| €1,200 | 1 | 05/06/2026 |

Its row in `concesiones_personas_fisicas` would be this (without the gross grant equivalent columns, which follow the same logic):

| Column | Value |
|---|---|
| `concesiones` | 12 |
| `beneficiarios` | 11 |
| `importeTotal` | 6,450.00 |
| `importeMedia` | 537.50 |
| `importeDesviacion` | 274.79 |
| `importeP25`, `importeMediana`, `importeP75` | 300.00, 450.00 and 600.00 |
| `fechaConcesionP25`, `fechaConcesionMediana`, `fechaConcesionP75` | 2026-03-12, 2026-04-20 and 2026-04-20 |
| `importeP10`, `importeP90`, `fechaConcesionP10`, `fechaConcesionP90` | Empty, because there are fewer than 20 people |

With it you can tell how much the call gave out, what a typical award was and when they were awarded, but not who got what. Nor do the €1,200 of the largest award appear, since they are one specific person's.

<a id="rules"></a>
## The rules

**Every row gathers at least 10 people.** With few people, a summary lets you guess what each one got. With two, for example, whoever knows what one got learns the other's by subtracting it from the total.

**No one holds more than half of any of their row's amounts** (the amount and the gross grant equivalent, where the entity carries both). If one person takes nearly everything, the total is practically their amount, however many others the row gathers. With 14 awards of €100 and one of €10,000, the total (€11,400) tells anyone who knows the call how much that person got.

**The smallest and largest values are never published, and the 10th and 90th percentiles only from 20 people.** The largest amount is one specific person's, and so are the smallest and the extreme dates. The 10th and 90th percentiles sit very close to them: in the example above, the 90th percentile would be €870, very close to the second largest award (€900). From 20 people on, the 10th percentile no longer falls below the second smallest award, nor the 90th above the second largest.

**Dates are real dates.** Date percentiles are picked among the award dates that exist, without interpolating, because a day halfway between two dates means nothing.

**What falls short goes into its year's rest row.** The awards of calls that cannot be published are gathered into one row with `esResto = true`, which does not say which calls it holds, and in `ejercicio` carries the year of each one's median award date. That row must meet the same rules and also gather at least two calls, because with only one, the rest would be that call under another name.

**Each person counts once.** A person is recognised by their BDNS identifier or, where it is missing, by the whole `beneficiario` field, and neither leaves the private file.

Every statistic covers every award in its row, and no other table summarises the same awards, so nothing can be learnt by subtracting one from the other. The thresholds are defined once, in the SQL, and [how it is built](build.md#thresholds) gives their values.

<a id="texts"></a>
## The texts of calls

A call is the administration's own announcement, not anyone's data, and is published record by record. But its texts are written by hand, and a nominative grant sometimes names its beneficiary, so the title, the description of the bases and the other free texts are published empty if they hold something shaped like a DNI, NIE or masked tax ID. So is the link to the bases when it has that shape, though it is nearly always a false alarm: some bulletins name their files with eight digits and a letter. Documents and bulletin announcements are left out, since they often list the beneficiaries.

A title naming a person without their DNI cannot be detected reliably, and is published as it is, just as the BDNS itself keeps it published.

<a id="checks"></a>
## What is checked before publishing

Before writing any file, the build checks what it is about to publish and **stops** if it finds:

- a protected beneficiary in a record-level table;
- anything shaped like a DNI, NIE or masked tax ID, in any column of any table;
- a column that identifies someone in the summary, such as `beneficiario`, `idPersona`, `urlBR` or `codConcesion`;
- a summary row with fewer than 10 people, or with the 10th or 90th percentiles and fewer than 20.

It reports what it finds without cleaning it up, because such a finding points to a fault in an earlier step, and quietly cleaning it would hide it behind a dataset that looks right. Each check's message is in [how it is built](build.md#checks).

## What the dataset does not allow

- Following a natural person over time, or knowing what a specific person got. That is exactly the aim, even though it limits some analyses.
- Matching the natural-person totals to the cent, because whatever reaches no publishable row is missing.
- Reading a summary call's title when it holds something shaped like a DNI, because it is published empty.
