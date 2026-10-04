# BDNS Sync

[![CI](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

> The [Spanish README](./README.md) is the canonical version; this translation may occasionally lag behind it.

Sync engine that maintains a local, versioned (SCD2) copy of the [Spanish National Subsidies Database (BDNS) REST API](https://www.infosubvenciones.es/bdnstrans/api).

It builds on [`bdns-fetch`](https://github.com/cruzlorite/bdns-fetch), which implements data extraction from the API; `bdns-sync` adds the storage layer: historical versioning, change and deletion detection, and run logging.

One command a day keeps the target up to date: it checks that the API has not changed, syncs the 22 entities with the window that day calls for, and records every run. No configuration file.

**Documentation:** <https://cruzlorite.github.io/bdns-sync/en/>

## Installation

Python 3.11 to 3.14.

```bash
pip install bdns-sync                # SQLite; for other engines, also install their driver
pip install "bdns-sync[bigquery]"    # with the BigQuery driver
```

## Usage

The target is any SQLAlchemy URL, in `BDNS_SYNC_TARGET_URL`:

```bash
export BDNS_SYNC_TARGET_URL="sqlite:///bdns.db"          # or postgresql://..., bigquery://project/dataset
bdns-sync backfill                                       # once: the full history
bdns-sync delta                                          # daily: the cadence, with an API check
bdns-sync sync concesiones_busqueda --window weekly      # a single entity
bdns-sync delta --dry-run                                # what it would do today, touching nothing
```

From nothing to a synced table in about ten minutes: [Get started](https://cruzlorite.github.io/bdns-sync/en/getting-started/). Every option: [CLI reference](https://cruzlorite.github.io/bdns-sync/en/reference/cli/).

## Documentation

- **[Get started](https://cruzlorite.github.io/bdns-sync/en/getting-started/)**: tutorial, from nothing to a queryable table.
- **How-to guides**: [scheduled operation](https://cruzlorite.github.io/bdns-sync/en/guides/scheduling/) · [initial loads and backfills](https://cruzlorite.github.io/bdns-sync/en/guides/backfill/) · [cloud deployment](https://cruzlorite.github.io/bdns-sync/en/guides/deployment/)
- **Explanation**: [endpoint types](https://cruzlorite.github.io/bdns-sync/en/explanation/endpoint-types/) · [what counts as a change](https://cruzlorite.github.io/bdns-sync/en/explanation/payload-policy/) · [how it syncs](https://cruzlorite.github.io/bdns-sync/en/explanation/sync-behavior/) · [official good practices](https://cruzlorite.github.io/bdns-sync/en/explanation/official-practices/) · [before querying the data](https://cruzlorite.github.io/bdns-sync/en/explanation/data-caveats/) · [known limitations](https://cruzlorite.github.io/bdns-sync/en/explanation/limitations/) · [target databases](https://cruzlorite.github.io/bdns-sync/en/explanation/sinks/)
- **Reference**: [CLI](https://cruzlorite.github.io/bdns-sync/en/reference/cli/) · [data model](https://cruzlorite.github.io/bdns-sync/en/reference/data-model/) · [Python API](https://cruzlorite.github.io/bdns-sync/en/reference/api/)
- **[Architecture decisions](https://cruzlorite.github.io/bdns-sync/en/adr/)** · **[Compatibility](https://cruzlorite.github.io/bdns-sync/en/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Development

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install -E bigquery
make test         # tests
make check-docs   # docs/ references, docstrings, and the site build
make docs         # serve the documentation locally
```

How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md). Vulnerabilities: [SECURITY.md](SECURITY.md). Pending work is in the [roadmap](docs/roadmap.en.md).

## Legal notice

This is a personal, unofficial project. It has no relationship with the Intervención General de la Administración del Estado (IGAE), the body that runs the BDNS, and is not endorsed by it. It is distributed under the MIT license, which excludes any warranty: you use it at your own risk and the author is not liable for damages, data loss or misuse.

The synced data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), and reusing it is subject to the [portal's legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and its [API good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf). In short, if you reuse the data:

- cite the source (for example, "Origen de los datos: Intervención General de la Administración del Estado") and the date of the last update when the data carries it;
- do not change the meaning of the information;
- do not suggest that the IGAE takes part in, sponsors or supports your reuse;
- personal data may only be reused to scrutinise the actions of public officials, or for historical, statistical or scientific purposes, in which case you must dissociate it first and state that you did and who did it.

This summary does not replace the official text or [Law 37/2007 on the reuse of public sector information](https://www.boe.es/eli/es/l/2007/11/16/37/con), which provides for penalties. If in doubt, ask a legal adviser.

**Personal data.** Several tables (`concesiones_busqueda` or `sanciones_busqueda`, among others) hold names and tax IDs of natural persons, which the BDNS publishes partially anonymised. Keep in mind that the history **keeps them after the portal withdraws them**: awards to natural persons, for instance, are only published during the year of the award and the next. Whoever operates the target database is responsible for processing that data under the GDPR (a legitimate purpose, a retention period and access control) and the conditions above.

## License and links

- [MIT license](./LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS Portal](https://www.infosubvenciones.es) · [BDNS legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal)
- Sibling project: [bdns-fetch](https://github.com/cruzlorite/bdns-fetch) (extraction)
