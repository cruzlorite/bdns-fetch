# BDNS Sync

[![CI](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-sync/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

> The [Spanish README](./README.md) is the canonical version; this translation may occasionally lag behind it.

Sync engine that maintains a local, versioned (SCD2) copy of the [Spanish National Subsidies Database (BDNS) REST API](https://www.infosubvenciones.es/bdnstrans/api).

It builds on [`bdns-fetch`](https://github.com/cruzlorite/bdns-fetch), which implements data extraction from the API; `bdns-sync` adds the storage layer: historical versioning, change and deletion detection, and run logging.

It is a single-purpose tool: each invocation syncs one endpoint, with no configuration file. Scheduling cadence lives in [`scripts/delta_load.sh`](scripts/delta_load.sh).

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
bdns-sync sync sectores                                  # catalog: full replace
bdns-sync sync concesiones_busqueda --window daily       # incremental: yesterday
bdns-sync sync concesiones_busqueda --since 2020-01-01   # historical load, up to yesterday
```

From nothing to a synced table in about ten minutes: [Get started](https://cruzlorite.github.io/bdns-sync/en/getting-started/). Every option: [CLI reference](https://cruzlorite.github.io/bdns-sync/en/reference/cli/).

## Documentation

- **[Get started](https://cruzlorite.github.io/bdns-sync/en/getting-started/)**: tutorial, from nothing to a queryable table.
- **How-to guides**: [scheduled operation](https://cruzlorite.github.io/bdns-sync/en/guides/scheduling/) · [initial loads and backfills](https://cruzlorite.github.io/bdns-sync/en/guides/backfill/) · [cloud deployment](https://cruzlorite.github.io/bdns-sync/en/guides/deployment/)
- **Explanation**: [endpoint types](https://cruzlorite.github.io/bdns-sync/en/explanation/endpoint-types/) · [what counts as a change](https://cruzlorite.github.io/bdns-sync/en/explanation/payload-policy/) · [API behaviour](https://cruzlorite.github.io/bdns-sync/en/explanation/bdns-api-behavior/) · [official good practices](https://cruzlorite.github.io/bdns-sync/en/explanation/official-practices/) · [before querying the data](https://cruzlorite.github.io/bdns-sync/en/explanation/data-caveats/) · [known limitations](https://cruzlorite.github.io/bdns-sync/en/explanation/limitations/) · [target databases](https://cruzlorite.github.io/bdns-sync/en/explanation/sinks/)
- **Reference**: [CLI](https://cruzlorite.github.io/bdns-sync/en/reference/cli/) · [data model](https://cruzlorite.github.io/bdns-sync/en/reference/data-model/) · [Python API](https://cruzlorite.github.io/bdns-sync/en/reference/api/)
- **[Architecture decisions](https://cruzlorite.github.io/bdns-sync/en/adr/)**

## Development

```bash
git clone https://github.com/cruzlorite/bdns-sync.git
cd bdns-sync
poetry install -E bigquery
make test         # tests
make check-docs   # docs/ references, docstrings, and the site build
make docs         # serve the documentation locally
```

Docstring conventions are in [docs/contributing/docstrings.md](docs/contributing/docstrings.md), and pending work in the [roadmap](docs/roadmap.en.md).

## Legal notice

Unofficial project, not affiliated with the Base de Datos Nacional de Subvenciones (BDNS) or Spain's Ministerio de Hacienda. Distributed under the GPL v3, which expressly disclaims any warranty: use is at your own risk, with no warranty of any kind and no liability accepted by the author for damages, data loss, or misuse.

The synced data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) and is subject to its own [legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and to the [API good-practices document](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

## License and links

- [GNU GPL v3.0](./LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS Portal](https://www.infosubvenciones.es) · [BDNS legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal)
- Sibling project: [bdns-fetch](https://github.com/cruzlorite/bdns-fetch) (extraction)
