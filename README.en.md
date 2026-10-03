# BDNS Fetch

[![CI](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/cruzlorite/bdns-fetch/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

> The [Spanish README](./README.md) is the canonical version; this translation may occasionally lag behind it.

Python client and CLI for the [Spanish National Subsidies Database (BDNS) REST API](https://www.infosubvenciones.es/bdnstrans/api). Covers the 29 query endpoints, with pagination, retries and the API's rate limit applied by default.

It is the extraction layer of the family: [`bdns-sync`](https://github.com/cruzlorite/bdns-sync) builds on it to keep a local, versioned copy of the same data.

## Installation

Python 3.11 to 3.14.

```bash
pip install bdns-fetch
```

## Python client

```python
from bdns.fetch import BDNSClient, TipoAdministracion

client = BDNSClient()

for organo in client.fetch_organos(idAdmon=TipoAdministracion.C):
    print(organo["id"], organo["descripcion"])
```

Each method's parameters are the API's, spelled the same way (`fechaDesde`, `nifCif`...), and are always passed by name. Dates are `date` objects; lists are Python lists.

Search endpoints are paginated. By default **every** page is fetched; `num_pages` and `from_page` narrow the range:

```python
from datetime import date

for concesion in client.fetch_concesiones_busqueda(
    fechaRegInicio=date(2024, 1, 1),
    fechaRegFin=date(2024, 1, 31),
):
    ...

first = client.fetch_ayudasestado_busqueda(descripcion="investigación", num_pages=2)
```

Document endpoints return `bytes`:

```python
pdf = client.fetch_convocatorias_pdf(id=608268, vpd="GE")
```

Configuration:

```python
client = BDNSClient(
    max_retries=3,     # retries after the first attempt, for transient failures only
    wait_time=2,       # initial wait between retries (s); doubles each time, up to 60
    max_workers=5,     # threads fetching pages concurrently
    return_raw=False,  # True: whole pages instead of records
    progress=None,     # progress bar; None = only when stderr is a terminal
    timeout=30,        # seconds per HTTP response
)
```

### Behaviour

- **Rate limit.** At most 10 requests per second per process, shared by every instance and thread. That is the per-IP limit set by the [official good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).
- **Retries.** Network errors, HTTP 429 and 5xx, and the `ERR_MANTENIMIENTO_BBDD` code are retried with exponential, jittered backoff, honouring `Retry-After`. Any other error is raised at once: repeating a bad request does not fix it.
- **Pagination.** Pages are requested concurrently but delivered in order, with never more than `2 × max_workers` held in memory. Stop iterating and the remaining pages are not downloaded.
- **Errors.** Every failure is a `BDNSError` (`message`, `suggestion`, `technical_details`). Transient ones, once retries are exhausted, are its subclass `BDNSTransientError`.

## CLI

```bash
bdns-fetch --help
bdns-fetch <command> --help

bdns-fetch -o organos.jsonl organos --idAdmon C
bdns-fetch convocatorias-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-12-31 --num-pages 0
bdns-fetch -o convocatoria.pdf convocatorias-pdf --id 608268 --vpd GE
bdns-fetch convocatorias-ultimas | jq .descripcion
```

Records are written as [JSON Lines](https://jsonlines.org/), one per line; documents, as they are. By default the CLI fetches **one** page and warns if there are more; `--num-pages 0` fetches them all.

Options of the tool itself are kebab-case (`--max-retries`); options that map to an API parameter keep its spelling (`--fechaDesde`). Dates accept ISO (`2024-01-31`), day first (`31/01/2024`) or natural language (`two weeks ago`).

Global options:

| Option | Alias | Default | Description |
|---|---|---|---|
| `--output-file` | `-o` | `-` (stdout) | Output file |
| `--max-retries` | `-mr` | `3` | Retries for transient failures; 0 disables them |
| `--wait-time` | `-wt` | `2` | Initial wait between retries (s) |
| `--max-workers` | `-mw` | `5` | Threads fetching pages |
| `--return-raw` | `-rr` | off | Whole pages instead of records |
| `--progress/--no-progress` | | automatic | Progress bar |
| `--verbose` | `-v` | off | Log every HTTP request |

On an API error, the CLI prints the message and exits with code 1.

### Commands

One command per endpoint, named after the method without `fetch_`, with hyphens. The underscore form (`concesiones_busqueda`), which is how `bdns-sync` names it, is accepted too.

| Command | Method | Paginated |
|---|---|---|
| `actividades` | `fetch_actividades` | |
| `sectores` | `fetch_sectores` | |
| `regiones` | `fetch_regiones` | |
| `finalidades` | `fetch_finalidades` | |
| `beneficiarios` | `fetch_beneficiarios` | |
| `instrumentos` | `fetch_instrumentos` | |
| `reglamentos` | `fetch_reglamentos` | |
| `objetivos` | `fetch_objetivos` | |
| `organos` | `fetch_organos` | |
| `organos-agrupacion` | `fetch_organos_agrupacion` | |
| `organos-codigo` | `fetch_organos_codigo` | |
| `organos-codigoadmin` | `fetch_organos_codigoadmin` | |
| `convocatorias` | `fetch_convocatorias` | |
| `convocatorias-busqueda` | `fetch_convocatorias_busqueda` | yes |
| `convocatorias-ultimas` | `fetch_convocatorias_ultimas` | |
| `convocatorias-documentos` | `fetch_convocatorias_documentos` | document |
| `convocatorias-pdf` | `fetch_convocatorias_pdf` | document |
| `concesiones-busqueda` | `fetch_concesiones_busqueda` | yes |
| `ayudasestado-busqueda` | `fetch_ayudasestado_busqueda` | yes |
| `minimis-busqueda` | `fetch_minimis_busqueda` | yes |
| `partidospoliticos-busqueda` | `fetch_partidospoliticos_busqueda` | yes |
| `grandesbeneficiarios-anios` | `fetch_grandesbeneficiarios_anios` | |
| `grandesbeneficiarios-busqueda` | `fetch_grandesbeneficiarios_busqueda` | yes |
| `sanciones-busqueda` | `fetch_sanciones_busqueda` | yes |
| `planesestrategicos` | `fetch_planesestrategicos` | |
| `planesestrategicos-busqueda` | `fetch_planesestrategicos_busqueda` | yes |
| `planesestrategicos-documentos` | `fetch_planesestrategicos_documentos` | document |
| `planesestrategicos-vigencia` | `fetch_planesestrategicos_vigencia` | |
| `terceros` | `fetch_terceros` | |

## Official good practices

From ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf):

- **Rate limit:** 10 GET per second per IP. `bdns-fetch` enforces it per process; several processes on the same IP share it and must split it.
- **Incremental sync:** use `fechaRegInicio`/`fechaRegFin` (registration date) to detect new and changed records, not `fechaDesde`/`fechaHasta` (award date): they are independent filters. Available on `concesiones-busqueda`, `ayudasestado-busqueda`, `minimis-busqueda` and `partidospoliticos-busqueda`.
- **`terceros`:** the document calls it redundant; `concesiones-busqueda` already carries the beneficiary data.

## Limitations

- The export endpoints (CSV/XLSX) and the portal configuration endpoints are not implemented.

## Development

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
make test               # unit tests, no network
make test-integration   # against the live API
make lint
```

Unit tests mock HTTP and run on every push. Integration tests call the live API and run nightly in [Integration](.github/workflows/integration.yml). Changes are recorded in the [CHANGELOG](CHANGELOG.md).

## Legal notice

Unofficial project, not affiliated in any way with the Base de Datos Nacional de Subvenciones (BDNS) or Spain's Ministerio de Hacienda. Distributed under the GPL v3, which expressly excludes any warranty: use it at your own risk, with no warranty of any kind and no liability of the author for damages, data loss or misuse.

The data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es) and is subject to its own [legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and the [API good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf).

**Personal data.** Some endpoints (`concesiones-busqueda`, `sanciones-busqueda`, `terceros`, among others) return names and tax IDs of natural persons. `bdns-fetch` delivers them exactly as the API publishes them, untransformed. Whoever downloads and stores them is responsible for processing them in accordance with the GDPR and with the transparency purpose for which they are published.

## License and links

- [GNU GPL v3.0 or later](./LICENSE)
- [Official API](https://www.infosubvenciones.es/bdnstrans/api) · [BDNS portal](https://www.infosubvenciones.es) · [PyPI](https://pypi.org/project/bdns-fetch)
- Sister project: [bdns-sync](https://github.com/cruzlorite/bdns-sync) (versioned history)
