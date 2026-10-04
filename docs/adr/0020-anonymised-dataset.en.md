# 0020. An anonymised, aggregated dataset

**Status:** proposed · **Date:** 2026-10-04

## Context

The BDNS API only returns a window of time, different for each kind of data: about 12 years of calls for applications, about 10 of state and de minimis aid, about 4 of awards, and only the award year and the next when the beneficiary is a natural person ([each endpoint keeps a different history](../fetch/explanation/api-behavior.md#history-depth)). Whatever leaves that window survives only where someone saved it in time, and `bdns-sync` saves it. That history is what makes a published dataset valuable: nobody else can offer it, not even the portal, which lets you download what is still published but not what it has withdrawn.

That same history holds personal data. The BDNS publishes natural persons' full names and hides only part of their tax ID (`***1234** NAME SURNAMES`), and on an ordinary day of 2026, 94% of awards went to natural persons, though they added up to only 12% of the amount. Each record also carries fields that identify the person even with the name removed: `idPersona`, an identifier repeated across all their awards; `urlBR`, the link to the official bulletin that names them; and `codConcesion` or `id`, which find the record on the portal while it is still published.

The legal framework limits what can be done with that data:

- The IGAE's reuse conditions allow personal data to be reused only to scrutinise public officials or for historical, statistical or scientific purposes, and in that case require dissociating it first.
- The GDPR leaves anonymous data out of its scope, but not pseudonymised data: replacing a tax ID with a code, even a hash, is still processing personal data, because the code lets you follow the person.
- The time limit on publishing awards to natural persons has a purpose, and republishing them in identifiable form after it would defeat it.

Official statistics solve this same problem by publishing aggregates and suppressing the cells that could identify someone, known as statistical disclosure control.

## Decision

The dataset **holds no personal data**. It may identify legal persons and public bodies, never natural persons.

1. **Each beneficiary is classified** as a natural person, an entity made of persons (communities of property and civil partnerships, often named after their members), a legal person, a public body or doubtful. The classification is conservative: anything doubtful is treated as a natural person ([how it is classified](../dataset/privacy.md#who)).
2. **What is published, and at what detail:**

    | Data | Level |
    |---|---|
    | Catalogs | As they are |
    | Calls for applications | Record by record, reviewing titles that name people |
    | Awards, state aid and de minimis aid to legal persons and public bodies | Record by record |
    | The same, to natural persons, entities made of persons and doubtful beneficiaries | Only as a summary per call: number of awards and beneficiaries, total amount, mean, standard deviation, median and quartiles of the amount, and the same percentiles of the award date |
    | Sanctions on natural persons | Not published |

3. **No summary about natural persons gathers fewer than 10 people**, or one holding more than half its amount: an amount that appears only once would single out who got it, even without a name, and could be matched against old copies of the BDNS that do carry names. The smallest and largest amount or date are never published, since each is one specific person's, and the 10th and 90th percentiles, which sit close to them, only when the summary gathers at least 20 people. Calls that fall short are gathered, per year, into a "rest" row, published only if it gathers at least two (with one, the rest would be that call as it is) and meets the thresholds too. Every statistic covers every award in its row, and there is no other table about them to compare it with.
4. **Never published**, in anything about natural persons: the name, the tax ID (full, partial or hashed), `idPersona`, `urlBR`, `codConcesion` or `id`.
5. **Generation stops** if what is about to be published holds a value shaped like a DNI, NIE or masked tax ID, a forbidden field or a cell below the minimum.
6. **The dataset is built where the data lives**, with DuckDB SQL that reads `bdns-sync`'s tables directly, so the method can be read and reviewed as it is ([the SQL](https://github.com/cruzlorite/bdns-tools/tree/main/dataset/sql)). The result stays private until a person reviews it, and is published outside the repository (on Zenodo, with a DOI per version) with the methodology, the IGAE citation and the update date. The only format is Parquet, one file per table: it carries each column's type, takes little space and every data tool reads it.
7. **Before the first publication**, a risk assessment and a legal review take place.

Still to decide: whether communities of property and civil partnerships are protected like natural persons (meanwhile, they are), how often a version is published, and the dataset's license (the IGAE's conditions plus, for example, CC BY 4.0 for the project's own work).

## Consequences

- If the anonymisation holds, what is published is no longer personal data, and reusing it does not bring anyone under the GDPR.
- A specific natural person cannot be followed over time. That is the point, even though it limits some analyses.
- Comparing two versions, the difference in a current-year summary shows what those who came in between received, though not who they are. It is accepted as residual risk: it identifies no one, and the BDNS itself publishes those amounts with names while they are within their period. The risk assessment will revisit it, and if needed, publishing at most one version per quarter would be enough.
- Natural-person summaries do not add up exactly to the real total, since what reaches no publishable summary is missing.
- `bdns-sync`'s data model becomes a contract of the generator: a change to it may require changing the dataset.
- Each dataset version can be rebuilt from a `bdns-sync` database, and the method is public, so it can be reviewed.
