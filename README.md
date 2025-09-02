# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Python library for accessing data from the **Base de Datos Nacional de Subvenciones (BDNS)** API. Provides both a programmatic client library and a command-line interface for data extraction.

## ✨ Features

- **📚 API Coverage**: 29 BDNS data endpoints with full parameter support
- **🐍 Python Interface**: Clean, type-hinted client library for programmatic access
- **🔄 Pagination**: Automatic pagination handling with configurable concurrency
- **🛡️ Error Handling**: Proper exception handling with retry logic
- **🔧 CLI Tool**: command-line interface for quick testing

## 🚀 Quick Start

### Installation

```bash
pip install bdns-fetch
```

### BDNS Client

```python
from bdns.fetch.client import BDNSClient

# Initialize the client
client = BDNSClient()

results = list(client.fetch_organos())

for r in results:
    print(r)
```

To easily check all available endpoints and paramenters:

```bash
bdns-fetch --help
```

[![CLI Help Message](https://raw.githubusercontent.com/cruzlorite/bdns-fetch/main/img/cli-help-2.png)](https://raw.githubusercontent.com/cruzlorite/bdns-fetch/main/img/cli-help-2.png)

To check the parameters of any given endpoint, use:

```bash
bdns-fetch [endpoint] --help
```
[![CLI Help Message](https://raw.githubusercontent.com/cruzlorite/bdns-fetch/main/img/cli-help-1.png)](https://raw.githubusercontent.com/cruzlorite/bdns-fetch/main/img/cli-help-1.png)

## 📄 Paginated Endpoints

The BDNS client handles pagination automatically and provides flexible control over data fetching:

### Basic Pagination

You can control the starting page, page size and number of pages to fetch. If `num_pages` is 0, it will fetch all available pages.

```python
from bdns.fetch.client import BDNSClient

client = BDNSClient()

results = client.fetch_ayudasestado_busqueda(
    descripcion="research",
    pageSize=100,    # Records per page (max: 10000)
    num_pages=5,     # Limit to 5 pages total
    from_page=0      # Start from first page
)

for r in results:
    print(r)
```

### Binary Documents

```python
# Download PDF documents
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)

# Download strategic plan documents
plan_doc = client.fetch_planesestrategicos_documentos(idDocumento=1272508)
with open("strategic_plan.pdf", "wb") as f:
    f.write(plan_doc)
```

## 🎯 Command Line Interface (Bonus)

For quick data extraction tasks, you can also use the included CLI tool:

### CLI Installation & Usage

```bash
# Install the package
pip install bdns-fetch

# Use the CLI for quick tasks
bdns-fetch --help
```

### CLI Examples

```bash
bdns-fetch --output-file results.jsonl organos

bdns-fetch --verbose --output-file results.jsonl ayudasestado-busqueda \
  --descripcion "innovation" \
  --fechaDesde "2023-01-01" \
  --fechaHasta "2024-12-31"

bdns-fetch --output-file results.jsonl convocatorias-ultimas
```

**CLI Output Format (JSON Lines):**
```json
{"id": 1, "descripcion": "MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN", "codigo": "E04"}
{"id": 2, "descripcion": "MINISTERIO DE ASUNTOS EXTERIORES, UNIÓN EUROPEA Y COOPERACIÓN", "codigo": "E05"}
```

## 🛠️ Development

### Development Setup

```bash
# Clone and setup
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install --with dev

# Available Make targets
make help               # Show all available targets
make install            # Install project dependencies  
make dev-install        # Install with development dependencies
make lint               # Run code linting with ruff
make format             # Format code with ruff formatter
make test-integration   # Run integration tests (29 endpoints)
make clean              # Remove build artifacts
make all                # Install, lint, format, and test
```

## ⚠️ API Limitations

### Not Included
The following BDNS API endpoints are **intentionally excluded**:

#### Export Endpoints (9 excluded)
File generation endpoints that create downloadable files rather than returning JSON data:
- `*/exportar` endpoints for CSV/Excel export functionality

#### Portal Configuration (2 excluded)  
Web portal UI configuration endpoints:
- `vpd/{vpd}/configuracion` - Portal navigation menus
- `enlaces` - Portal links and micro-windows

#### Subscription System (11 excluded)
User subscription and alert management endpoints requiring authentication:
- `suscripciones/*` endpoints for managing email alerts and user accounts

**Rationale**: This library focuses on **data extraction**, not web portal functionality or user account management.

## 🙏 Acknowledgments

This project is inspired by previous work from [Jaime Ortega Obregón](https://github.com/JaimeObregon/subvenciones/tree/main).

## 📜 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.
