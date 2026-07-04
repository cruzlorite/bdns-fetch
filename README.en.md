# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

Python client and CLI for the [BDNS REST API](https://www.infosubvenciones.es/bdnstrans/api). Covers all 29 available endpoints with full parameter support, automatic pagination, and configurable retries.

## Installation

```bash
pip install bdns-fetch
```

or from the repository:

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
pip install .
```

## Usage

### Python Client

```python
from bdns.fetch.client import BDNSClient

client = BDNSClient()

for org in client.fetch_organos(idAdmon="C"):
    print(org["codigo"], "-", org["descripcion"])
```

Paginated search:

```python
results = client.fetch_ayudasestado_busqueda(
    descripcion="research",
    pageSize=1000,
    num_pages=5,
    from_page=0,
)
for item in results:
    print(item)
```

Binary document download:

```python
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)
```

Client configuration:

```python
client = BDNSClient(
    max_retries=5,    # retries per failed request
    wait_time=2,      # seconds between retries
    max_workers=10,   # concurrent threads for pagination
    return_raw=False, # True returns full page objects
)
```

### CLI

```bash
# Show help
bdns-fetch --help
bdns-fetch <command> --help

# Save to file
bdns-fetch --output-file organos.jsonl organos --idAdmon C

# Search with filters
bdns-fetch --output-file result.jsonl ayudasestado-busqueda \
    --descripcion "innovation" --fechaDesde "2023-01-01" --fechaHasta "2024-12-31"

# Pagination
bdns-fetch concesiones-busqueda --num-pages 0 --pageSize 10000

# Output to stdout (default)
bdns-fetch convocatorias-ultimas | jq .
```

Global options:

| Option | Alias | Default | Description |
|---|---|---|---|
| `--output-file` | `-o` | `-` (stdout) | Output file in JSONL format |
| `--max-retries` | `-mr` | `3` | Retries per failed request |
| `--wait-time` | `-wt` | `2` | Seconds between retries |
| `--max-workers` | `-mw` | `5` | Concurrent threads for pagination |
| `--return-raw` | `-rr` | `false` | Return full page objects |
| `--verbose` | `-v` | `false` | Detailed HTTP request logging |

### Available commands

| Command | Client method |
|---|---|
| `actividades` | `fetch_actividades` |
| `sectores` | `fetch_sectores` |
| `regiones` | `fetch_regiones` |
| `finalidades` | `fetch_finalidades` |
| `beneficiarios` | `fetch_beneficiarios` |
| `instrumentos` | `fetch_instrumentos` |
| `reglamentos` | `fetch_reglamentos` |
| `objetivos` | `fetch_objetivos` |
| `organos` | `fetch_organos` |
| `organos-agrupacion` | `fetch_organos_agrupacion` |
| `organos-codigo` | `fetch_organos_codigo` |
| `organos-codigoadmin` | `fetch_organos_codigoadmin` |
| `convocatorias` | `fetch_convocatorias` |
| `convocatorias-busqueda` | `fetch_convocatorias_busqueda` |
| `convocatorias-ultimas` | `fetch_convocatorias_ultimas` |
| `convocatorias-documentos` | `fetch_convocatorias_documentos` |
| `convocatorias-pdf` | `fetch_convocatorias_pdf` |
| `concesiones-busqueda` | `fetch_concesiones_busqueda` |
| `ayudasestado-busqueda` | `fetch_ayudasestado_busqueda` |
| `minimis-busqueda` | `fetch_minimis_busqueda` |
| `grandesbeneficiarios-anios` | `fetch_grandesbeneficiarios_anios` |
| `grandesbeneficiarios-busqueda` | `fetch_grandesbeneficiarios_busqueda` |
| `planesestrategicos` | `fetch_planesestrategicos` |
| `planesestrategicos-busqueda` | `fetch_planesestrategicos_busqueda` |
| `planesestrategicos-documentos` | `fetch_planesestrategicos_documentos` |
| `planesestrategicos-vigencia` | `fetch_planesestrategicos_vigencia` |
| `partidospoliticos-busqueda` | `fetch_partidospoliticos_busqueda` |
| `sanciones-busqueda` | `fetch_sanciones_busqueda` |
| `terceros` | `fetch_terceros` |

## Limitations

- Export endpoints (CSV/XLSX generation) and portal configuration routes are not implemented.
- Concurrent pagination results are not ordered by page number.

## License & links

- **License:** [GNU General Public License v3.0](./LICENSE)
- **Official API:** [https://www.infosubvenciones.es/bdnstrans/api](https://www.infosubvenciones.es/bdnstrans/api)
- **BDNS portal:** [https://www.infosubvenciones.es](https://www.infosubvenciones.es)
- **PyPI:** [https://pypi.org/project/bdns-fetch](https://pypi.org/project/bdns-fetch)

For more information about the available data, check the official portal.

---

**bdns-fetch** is free software. Contributions are welcome!
