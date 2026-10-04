---
icon: material/chart-box
---

# BDNS Dataset

!!! warning "In preparation"

    No version has been published yet. This section explains what the dataset will be and how it is being built, and the code is experimental: it may change in any release until the first version is published.

A ready-to-use dataset with **the whole history** of the BDNS that `bdns-sync` keeps, not only the years the portal still publishes ([why it matters](../sync/index.md#why-history)). It will always be **anonymised and aggregated**: protecting natural persons comes first, and the whole process must comply with the IGAE's reuse conditions, the GDPR and Spain's LOPDGDD. What is published, at what detail and why is in [decision 0002](../adr/0002-anonymised-dataset.md), still a proposal.

## How natural persons are protected

Each beneficiary is classified by its tax ID, never by its name, and anything not recognised is treated as a natural person. For example (names and tax IDs are made up):

| How it appears in the BDNS | Classified as | In the dataset |
|---|---|---|
| `***1234** NOMBRE APELLIDOS` | Natural person | Aggregated only |
| `E12345678 APELLIDO Y APELLIDO CB` | Entity made of persons | Aggregated only |
| `123456789012 FOREIGN COMPANY LTD` | Doubtful | Aggregated only |
| `B12345678 EMPRESA DE EJEMPLO SL` | Legal person | Record by record |
| `P1234567D AYUNTAMIENTO DE EJEMPLO` | Public body | Record by record |

Communities of property and civil partnerships have a tax ID of their own, but are usually named after their members, so they are protected like natural persons.

Before writing anything, the build checks what it is about to publish and **stops** if it finds a value shaped like a DNI, NIE or masked tax ID, a column that identifies someone (`beneficiario`, `idPersona`, `urlBR`...) or an aggregated cell with fewer than ten beneficiaries. It does not clean up what it finds: it reports it, because such a finding points to an earlier fault that needs fixing.

## Status

- [x] The design decision, as a proposal ([decision 0002](../adr/0002-anonymised-dataset.md))
- [x] Beneficiary classification ([`beneficiaries`][bdns.dataset.beneficiaries]) and privacy checks ([`privacy`][bdns.dataset.privacy])
- [ ] Extraction from `bdns-sync`'s tables
- [ ] The aggregates, with statistical disclosure control
- [ ] The dataset card, the schema and publication
- [ ] The risk assessment and legal review, before the first version
