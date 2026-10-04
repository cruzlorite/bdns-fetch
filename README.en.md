# BDNS Tools

[![CI](https://github.com/cruzlorite/bdns-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-tools/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-tools.svg)](https://pypi.org/project/bdns-tools/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/cruzlorite/bdns-tools/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Versión en español](https://github.com/cruzlorite/bdns-tools/blob/main/README.md)

Unofficial tools to download, keep and reuse the data of the [REST API of Spain's National Subsidies Database (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). The package brings two:

- **`bdns-fetch`**, a Python client and command-line tool covering the 29 query endpoints. They handle pagination, retries and the rate limit the API sets.
- **`bdns-sync`**, which keeps a copy of the BDNS, with the history of every version, in your database (SQLite, PostgreSQL, DuckDB or BigQuery). One command a day is enough.

**Documentation:** <https://cruzlorite.github.io/bdns-tools/en/>

## Install

Python 3.11 or later (up to 3.14).

```bash
pip install bdns-tools                # SQLite; for other databases, install their driver too
pip install "bdns-tools[bigquery]"    # with the BigQuery driver
```

## Usage

Downloading data:

```bash
bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-31 --num-pages 0 > january.jsonl
```

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import registration_range

client = BDNSClient()
for concesion in client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31))):
    print(concesion["beneficiario"], concesion["importe"])
```

Keeping a copy with its history, with the target given as a SQLAlchemy URL:

```bash
export BDNS_SYNC_TARGET_URL="sqlite:///bdns.db"          # or postgresql://..., bigquery://project/dataset
bdns-sync backfill                                       # once: the full history
bdns-sync delta                                          # daily: the cadence, with an API check
```

To start, each tool has its own get-started page: [bdns-fetch](https://cruzlorite.github.io/bdns-tools/en/fetch/getting-started/) and [bdns-sync](https://cruzlorite.github.io/bdns-tools/en/sync/getting-started/).

## Documentation

- **[bdns-fetch](https://cruzlorite.github.io/bdns-tools/en/fetch/)**: [get started](https://cruzlorite.github.io/bdns-tools/en/fetch/getting-started/) · [incremental downloads](https://cruzlorite.github.io/bdns-tools/en/fetch/guides/incremental/) · [API behaviour](https://cruzlorite.github.io/bdns-tools/en/fetch/explanation/api-behavior/) · [CLI](https://cruzlorite.github.io/bdns-tools/en/fetch/reference/cli/)
- **[bdns-sync](https://cruzlorite.github.io/bdns-tools/en/sync/)**: [get started](https://cruzlorite.github.io/bdns-tools/en/sync/getting-started/) · [daily sync](https://cruzlorite.github.io/bdns-tools/en/sync/guides/scheduling/) · [initial load](https://cruzlorite.github.io/bdns-tools/en/sync/guides/backfill/) · [cloud deployment](https://cruzlorite.github.io/bdns-tools/en/sync/guides/deployment/) · [data model](https://cruzlorite.github.io/bdns-tools/en/sync/reference/data-model/)
- **Project**: [compatibility](https://cruzlorite.github.io/bdns-tools/en/compatibility/) · [roadmap](https://cruzlorite.github.io/bdns-tools/en/roadmap/) · [shared decisions](https://cruzlorite.github.io/bdns-tools/en/adr/) · [changelog](https://github.com/cruzlorite/bdns-tools/blob/main/CHANGELOG.md)

Up to `bdns-fetch` 1.3.0 and `bdns-sync` 0.5.0, each tool was published as a separate package. Imports and commands are unchanged: install `bdns-tools` ([details](https://cruzlorite.github.io/bdns-tools/en/compatibility/#previous-names)).

## Development

You need [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/cruzlorite/bdns-tools.git
cd bdns
make install            # the package, its extras and the development tools
make test               # tests, offline
make check-docs         # links, docstrings and the site build
make docs               # serve the documentation locally
```

To contribute, read [CONTRIBUTING.md](https://github.com/cruzlorite/bdns-tools/blob/main/CONTRIBUTING.md). To report a vulnerability, follow [SECURITY.md](https://github.com/cruzlorite/bdns-tools/blob/main/SECURITY.md).

## Legal notice

This is a personal, unofficial project, not affiliated with the Intervención General de la Administración del Estado (IGAE), which runs the BDNS. The code is distributed under the MIT license, which excludes any warranty.

If you reuse the data, you must meet the IGAE's reuse conditions: cite the source, do not change the meaning of the information, do not suggest that the IGAE endorses you, and reuse personal data only for the permitted purposes. Whoever stores personal data is responsible for processing it under the GDPR and Spain's LOPDGDD, and bear in mind that `bdns-sync`'s history **keeps it even after the portal withdraws it**.

Every detail, including which personal data the BDNS publishes, is in the [legal notice](https://cruzlorite.github.io/bdns-tools/en/legal/).

## License and links

- [MIT license](https://github.com/cruzlorite/bdns-tools/blob/main/LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS portal](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-tools/)
