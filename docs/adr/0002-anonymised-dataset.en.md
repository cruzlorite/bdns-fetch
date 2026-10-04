# 0002. An anonymised, aggregated dataset

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

1. **Each beneficiary is classified** as a natural person, an entity made of persons (communities of property and civil partnerships, often named after their members), a legal person, a public body or doubtful. The classification is conservative: anything doubtful is treated as a natural person ([`classify`][bdns.dataset.beneficiaries.classify]).
2. **What is published, and at what detail:**

    | Data | Level |
    |---|---|
    | Catalogs | As they are |
    | Calls for applications | Record by record, reviewing titles that name people |
    | Awards, state aid and de minimis aid to legal persons and public bodies | Record by record |
    | The same, to natural persons, entities made of persons and doubtful beneficiaries | Only aggregated by call and year (with its body, region and instrument): number of awards, number of beneficiaries and total amount |
    | Sanctions on natural persons | Not published |

3. **In the aggregates, any cell is suppressed** with fewer than 10 beneficiaries or where a single one holds most of the amount, and so are the cells that would let a suppressed one be recomputed by subtraction (secondary suppression).
4. **Never published**, in anything about natural persons: the name, the tax ID (full, partial or hashed), `idPersona`, `urlBR`, `codConcesion` or `id`.
5. **Generation stops** if what is about to be published holds a value shaped like a DNI, NIE or masked tax ID, a forbidden field or a cell below the minimum ([`bdns.dataset.privacy`][bdns.dataset.privacy]).
6. **The dataset is built where the data lives**, from `bdns-sync`'s tables. The result stays private until a person reviews it, and is published outside the repository (on Zenodo, with a DOI per version) with the methodology, the IGAE citation and the update date.
7. **Before the first publication**, a risk assessment and a legal review take place.

Still to decide: whether communities of property and civil partnerships are protected like natural persons (meanwhile, they are), the exact detail of the aggregates, how often a version is published, and the dataset's license (the IGAE's conditions plus, for example, CC BY 4.0 for the project's own work).

## Consequences

- If the anonymisation holds, what is published is no longer personal data, and reusing it does not bring anyone under the GDPR.
- A specific natural person cannot be followed over time. That is the point, even though it limits some analyses.
- Natural-person aggregates do not add up exactly to the real total, since suppressed cells are missing. What is suppressed is published grouped in a "rest" cell, provided that cell meets the thresholds too.
- `bdns-sync`'s data model becomes a contract of the generator: a change to it may require changing the dataset.
- Each dataset version can be rebuilt from a `bdns-sync` database, and the method is public, so it can be reviewed.
