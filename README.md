# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Python library for accessing data from the **Base de Datos Nacional de Subvenciones (BDNS)** API. Provides both a programmatic client library and a command-line interface for data extraction.

## ✨ Features

- **📚 Complete API Coverage**: 29 BDNS data endpoints with full parameter support
- **🐍 Python Interface**: Clean, type-hinted client library for programmatic access
- **📄 Binary Document Support**: Download PDF documents and files from the API
- **⚙️ Flexible Configuration**: Comprehensive parameter support from official API specification
- **🔄 Smart Pagination**: Automatic pagination handling with configurable concurrency
- **🛡️ Robust Error Handling**: Proper exception handling with retry logic
- **🔧 CLI Tool**: Bonus command-line interface for quick data extraction

## 🚀 Quick Start

### Installation

```bash
pip install bdns-fetch
```

### BDNS Client

```python
from bdns.fetch.client import BDNSClient
from datetime import datetime

# Initialize the client
client = BDNSClient()

# Fetch government organs
organs = list(client.fetch_organos())
print(f"Found {len(organs)} government organs")

# Search for subsidies with filters
subsidies = client.fetch_ayudasestado_busqueda(
    descripcion="innovation",
    fechaDesde=datetime(2023, 1, 1),
    fechaHasta=datetime(2024, 12, 31),
    pageSize=100
)

for subsidy in subsidies:
    print(f"- {subsidy['descripcion']}: {subsidy['importe']}€")

# Download PDF documents
pdf_data = client.fetch_convocatorias_pdf(id=608268)
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_data)
```

## 📄 Paginated Endpoints

The BDNS client handles pagination automatically and provides flexible control over data fetching:

### Basic Pagination

You can control the starting page, page size and number of pages to fetch. If `num_pages` is 0, it will fetch all available pages.

```python
from bdns.fetch.client import BDNSClient
from datetime import datetime

client = BDNSClient()

subsidies = client.fetch_ayudasestado_busqueda(
    descripcion="research",
    pageSize=100,    # Records per page (max: 10000)
    num_pages=5,     # Limit to 5 pages total
    from_page=0      # Start from first page
)

subsidy_list = list(subsidies)
```

### Binary Documents

```python
# Download PDF documents from calls for proposals
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)

# Download strategic plan documents
plan_doc = client.fetch_planesestrategicos_documentos(idDocumento=1272508)
with open("strategic_plan.pdf", "wb") as f:
    f.write(plan_doc)

# Download call documents
call_doc = client.fetch_convocatorias_documentos(idDocumento=36605)
with open("call_document.pdf", "wb") as f:
    f.write(call_doc)

# Verify document formats
def verify_document_format(data, filename):
    if len(data) > 4:
        header = data[:4]
        if header == b'%PDF':
            print(f"✅ {filename}: Valid PDF ({len(data):,} bytes)")
        elif header[:2] == b'PK':
            print(f"✅ {filename}: Office/ZIP document ({len(data):,} bytes)")
        else:
            print(f"📄 {filename}: Unknown format ({len(data):,} bytes)")

verify_document_format(pdf_bytes, "convocatoria.pdf")
verify_document_format(plan_doc, "strategic_plan.pdf")
verify_document_format(call_doc, "call_document.pdf")
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
# Fetch government organs to file
bdns-fetch --output-file government_organs.jsonl organos

# Search state aids with filters
bdns-fetch --verbose --output-file results.jsonl ayudasestado-busqueda \
  --descripcion "innovation" \
  --fechaDesde "2023-01-01" \
  --fechaHasta "2024-12-31"

# Get latest calls for proposals
bdns-fetch --output-file latest_calls.jsonl convocatorias-ultimas
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
make help                # Show all available targets
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

## 🔧 Error Handling

The library provides comprehensive error handling:

```python
from bdns.fetch.exceptions import BDNSAPIError, BDNSConnectionError

try:
    data = client.fetch_organos()
except BDNSAPIError as e:
    print(f"API returned error: {e}")
    print(f"Status code: {e.status_code}")
except BDNSConnectionError as e:
    print(f"Connection failed: {e}")
```

**Common API Errors:**
- `ERR_VALIDACION`: Invalid parameter values
- `ERR_SIN_RESULTADOS`: No results found for query
- HTTP 404: Endpoint or resource not found

## 🙏 Acknowledgments

This project is inspired by previous work from [Jaime Ortega Obregón](https://github.com/JaimeObregon/subvenciones/tree/main).

## 📜 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.
