# BDNS

[![CI](https://github.com/cruzlorite/bdns/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns.svg)](https://pypi.org/project/bdns/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/cruzlorite/bdns/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Versión en español](https://github.com/cruzlorite/bdns/blob/main/README.md)

Tools to download, keep and reuse the data of the [REST API of Spain's National Subsidies Database (BDNS)](https://www.infosubvenciones.es/bdnstrans/api). The package brings two:

- **`bdns-fetch`**, a Python client and command-line tool covering the 29 query endpoints. They handle pagination, retries and the rate limit the API sets.
- **`bdns-sync`**, which keeps a copy of the BDNS, with the history of every version, in your database (SQLite, PostgreSQL, DuckDB or BigQuery). One command a day is enough.

**Documentation:** <https://cruzlorite.github.io/bdns/en/>

## Install

Python 3.11 or later (up to 3.14).

```bash
pip install bdns                # SQLite; for other databases, install their driver too
pip install "bdns[bigquery]"    # with the BigQuery driver
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

To start, each tool has its own get-started page: [bdns-fetch](https://cruzlorite.github.io/bdns/en/fetch/getting-started/) and [bdns-sync](https://cruzlorite.github.io/bdns/en/sync/getting-started/).

## Documentation

- **[bdns-fetch](https://cruzlorite.github.io/bdns/en/fetch/)**: [get started](https://cruzlorite.github.io/bdns/en/fetch/getting-started/) · [incremental downloads](https://cruzlorite.github.io/bdns/en/fetch/guides/incremental/) · [API behaviour](https://cruzlorite.github.io/bdns/en/fetch/explanation/api-behavior/) · [CLI](https://cruzlorite.github.io/bdns/en/fetch/reference/cli/)
- **[bdns-sync](https://cruzlorite.github.io/bdns/en/sync/)**: [get started](https://cruzlorite.github.io/bdns/en/sync/getting-started/) · [daily sync](https://cruzlorite.github.io/bdns/en/sync/guides/scheduling/) · [initial load](https://cruzlorite.github.io/bdns/en/sync/guides/backfill/) · [cloud deployment](https://cruzlorite.github.io/bdns/en/sync/guides/deployment/) · [data model](https://cruzlorite.github.io/bdns/en/sync/reference/data-model/)
- **Project**: [compatibility](https://cruzlorite.github.io/bdns/en/compatibility/) · [roadmap](https://cruzlorite.github.io/bdns/en/roadmap/) · [shared decisions](https://cruzlorite.github.io/bdns/en/adr/) · [changelog](https://github.com/cruzlorite/bdns/blob/main/CHANGELOG.md)

Up to `bdns-fetch` 1.3.0 and `bdns-sync` 0.5.0, each tool was published as a separate package. Imports and commands are unchanged: install `bdns` ([details](https://cruzlorite.github.io/bdns/en/compatibility/#previous-names)).

## Development

You need [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/cruzlorite/bdns.git
cd bdns
make install            # the package, its extras and the development tools
make test               # tests, offline
make check-docs         # links, docstrings and the site build
make docs               # serve the documentation locally
```

To contribute, read [CONTRIBUTING.md](https://github.com/cruzlorite/bdns/blob/main/CONTRIBUTING.md). To report a vulnerability, follow [SECURITY.md](https://github.com/cruzlorite/bdns/blob/main/SECURITY.md).

## Legal notice

This is a personal, unofficial project. It has no relationship with the Intervención General de la Administración del Estado (IGAE), the body that runs the BDNS, and is not endorsed by it. It is distributed under the MIT license, which excludes any warranty: you use it at your own risk and the author is not liable for damages, data loss or misuse.

The data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), and reusing it is subject to the [portal's legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and its [good practices for the API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf). In short, if you reuse it:

- cite the source (for example, "Origen de los datos: Intervención General de la Administración del Estado") and the date of the last update when the data carries it;
- do not change the meaning of the information;
- do not suggest that the IGAE takes part in, sponsors or supports your reuse;
- personal data may only be reused to scrutinise the actions of public officials, or for historical, statistical or scientific purposes, in which case you must dissociate it first and state that you did and who did it.

This summary does not replace the official text or [Law 37/2007 on the reuse of public sector information](https://www.boe.es/eli/es/l/2007/11/16/37/con), which provides for penalties. If in doubt, ask a legal adviser.

**Personal data.** Several endpoints and tables (`concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda` or `terceros`, among others) hold data on natural persons: the BDNS publishes their full name and hides only part of the tax ID. The tools deliver and store them exactly as the API publishes them, untransformed. Bear in mind that `bdns-sync`'s history **keeps them even after the portal withdraws them**: awards to natural persons, for instance, are only published during the award year and the next. Whoever downloads the data or runs the target database is responsible for processing it under the GDPR and Spain's LOPDGDD (with a legitimate purpose, a retention period and access control) and the conditions above.

## License and links

- [MIT license](https://github.com/cruzlorite/bdns/blob/main/LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS portal](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns/)
