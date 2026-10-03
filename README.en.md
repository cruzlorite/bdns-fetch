# BDNS Fetch

[![CI](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

> The [Spanish README](./README.md) is the canonical version; this translation may occasionally lag behind it.

Python client and CLI for the [Spanish National Subsidies Database (BDNS) REST API](https://www.infosubvenciones.es/bdnstrans/api). Covers the 29 query endpoints, with pagination, retries and the API's rate limit applied by default, and documents how the API actually behaves.

It is the extraction layer of the family: [`bdns-sync`](https://github.com/cruzlorite/bdns-sync) builds on it to keep a local, versioned copy of the same data.

**Documentation:** <https://cruzlorite.github.io/bdns-fetch/en/>

## Installation

Python 3.11 to 3.14.

```bash
pip install bdns-fetch
```

## Usage

```bash
bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-31 --num-pages 0 > january.jsonl
bdns-fetch check-api
```

```python
from datetime import date

from bdns.fetch import BDNSClient
from bdns.fetch.dates import registration_range

client = BDNSClient()
for concesion in client.fetch_concesiones_busqueda(**registration_range(date(2024, 1, 1), date(2024, 1, 31))):
    print(concesion["beneficiario"], concesion["importe"])
```

From zero to a first query in five minutes: [Get started](https://cruzlorite.github.io/bdns-fetch/en/getting-started/).

## Documentation

- **[Get started](https://cruzlorite.github.io/bdns-fetch/en/getting-started/)**: tutorial, terminal and Python.
- **How-to guides**: [incremental downloads](https://cruzlorite.github.io/bdns-fetch/en/guides/incremental/) · [errors and retries](https://cruzlorite.github.io/bdns-fetch/en/guides/errors/) · [endpoints without a method](https://cruzlorite.github.io/bdns-fetch/en/guides/other-endpoints/)
- **Explanation**: [API behaviour](https://cruzlorite.github.io/bdns-fetch/en/explanation/api-behavior/) · [how the client works](https://cruzlorite.github.io/bdns-fetch/en/explanation/policies/)
- **Reference**: [CLI](https://cruzlorite.github.io/bdns-fetch/en/reference/cli/) · [Python API](https://cruzlorite.github.io/bdns-fetch/en/reference/api/)
- **[Architecture decisions](https://cruzlorite.github.io/bdns-fetch/en/adr/)** · **[Compatibility](https://cruzlorite.github.io/bdns-fetch/en/compatibility/)** · **[Changelog](CHANGELOG.md)**

## Development

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
make test               # unit tests, no network
make test-integration   # against the live API
make check-docs         # references, docstrings and site build
make docs               # serve the documentation locally
```

How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md). Vulnerabilities: [SECURITY.md](SECURITY.md).

## Legal notice

Unofficial project, not affiliated in any way with the Base de Datos Nacional de Subvenciones (BDNS) or Spain's Ministerio de Hacienda. Distributed under the GPL v3, which expressly excludes any warranty: use it at your own risk, with no warranty of any kind and no liability of the author for damages, data loss or misuse.

The data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) and is subject to its own [legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and the [API good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

**Personal data.** Some endpoints (`concesiones-busqueda`, `sanciones-busqueda`, `terceros`, among others) return names and tax IDs of natural persons. `bdns-fetch` delivers them exactly as the API publishes them, untransformed. Whoever downloads and stores them is responsible for processing them in accordance with the GDPR and with the transparency purpose for which they are published.

## License and links

- [GNU GPL v3.0 or later](./LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS portal](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-fetch)
- Sister project: [bdns-sync](https://github.com/cruzlorite/bdns-sync) (versioned history)
