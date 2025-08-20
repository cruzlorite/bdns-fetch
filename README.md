BDNS Fetch
===========
[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive command-line tool for accessing and processing data from the Base de Datos Nacional de Subvenciones (BDNS) API.

## ✨ Features

- **29+ Data Extraction Commands**: Covers all key data extraction endpoints from the BDNS API
- **JSONL Output Format**: Clean JSON Lines format for easy data processing
- **Flexible Configuration**: Customizable parameters for each command
- **Clean Error Handling**: User-friendly error messages for API issues
- **Verbose Logging**: Detailed HTTP request/response logging for debugging
- **Concurrent Processing**: Built-in pagination and concurrent request handling

## 📋 Available Commands

This tool provides access to **29+ BDNS API data extraction endpoints**. Each command fetches specific data from the Base de Datos Nacional de Subvenciones (BDNS).

For a complete list of all commands and their parameters, use:
```bash
bdns-fetch --help
```

For help on a specific command:
```bash
bdns-fetch [command-name] --help
# Example: bdns-fetch organos --help
```

**📖 API Documentation**: Complete endpoint documentation is available at [BDNS API Swagger](https://www.infosubvenciones.es/bdnstrans/estaticos/doc/snpsap-api.json)

## 🚀 Quick Start

### Installation

**From PyPI (recommended):**
```bash
pip install bdns-fetch
```

**From source:**
```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
poetry install
```

### CLI Usage

**Getting Help:**
```bash
# List all available commands
bdns-fetch --help

# Get help for a specific command  
bdns-fetch organos --help
bdns-fetch ayudasestado-busqueda --help
```

**Basic Examples:**
```bash
# Fetch government organs data to file
bdns-fetch organos --output-file government_organs.jsonl

# Get economic activities (to stdout by default)
bdns-fetch actividades

# Search state aids with filters and verbose logging
bdns-fetch --verbose ayudasestado-busqueda \
  --descripcion "innovation" \
  --num-pages 3 \
  --pageSize 1000 \
  --output-file innovation_aids.jsonl

# Get specific strategic plan by ID with debugging
bdns-fetch --verbose planesestrategicos \
  --idPES 459 \
  --output-file plan_459.jsonl
```

**Common Parameters:**
- `--output-file FILE`: Save output to file (defaults to stdout)  
- `--verbose, -v`: Enable detailed HTTP request/response logging
- `--vpd CODE`: Territory code (GE=Spain, specific regions available)
- `--num-pages N`: Number of pages to fetch (for paginated commands)
- `--pageSize N`: Records per page (default: 10000, max: 10000)
- `--max-concurrent-requests N`: Maximum concurrent API requests (default: 5)

**Advanced Search Example:**
```bash
# Search concessions with multiple filters and verbose logging
bdns-fetch --verbose concesiones-busqueda \
  --descripcion "research" \
  --fechaDesde "2023-01-01" \
  --fechaHasta "2024-12-31" \
  --tipoAdministracion "C" \
  --num-pages 10 \
  --max-concurrent-requests 8 \
  --output-file research_concessions.jsonl
```

## 📖 More Examples

```bash
# Download all government organs
bdns-fetch organos --output-file government_structure.jsonl

# Search for innovation-related subsidies with verbose logging
bdns-fetch --verbose ayudasestado-busqueda \
  --descripcion "innovation" \
  --output-file innovation_aids.jsonl

# Get latest calls for proposals
bdns-fetch convocatorias-ultimas --output-file latest_calls.jsonl

# Search sanctions data with detailed HTTP logging
bdns-fetch --verbose sanciones-busqueda --output-file sanctions.jsonl
```

Output format (JSON Lines):
```json
{"id": 1, "descripcion": "MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN", "codigo": "E04"}
{"id": 2, "descripcion": "MINISTERIO DE ASUNTOS EXTERIORES, UNIÓN EUROPEA Y COOPERACIÓN", "codigo": "E05"}
```

## 🔧 Error Handling & Debugging

The tool provides user-friendly error messages for common API issues:

```bash
# Invalid parameter example
$ bdns-fetch ayudasestado-busqueda --vpd INVALID_PORTAL
Error (ERR_VALIDACION): El parámetro 'vpd' indica un portal no válido.
```

Use --verbose for detailed logging.

## ⚠️ Current Limitations

### Missing Commands
**This tool implements 30 out of 46 total API endpoints**. The following 16 commands are **intentionally not included**:

#### Export/Download Endpoints (9 missing)
These endpoints generate PDF, CSV, or Excel files instead of JSON data:
- `convocatorias/exportar` - Export search results to files
- `convocatorias/ultimas/exportar` - Export latest calls to files
- `concesiones/exportar` - Export concessions search to files
- `ayudasestado/exportar` - Export state aids search to files
- `minimis/exportar` - Export minimis search to files
- `grandesbeneficiarios/exportar` - Export large beneficiaries to files
- `partidospoliticos/exportar` - Export political parties search to files
- `planesestrategicos/exportar` - Export strategic plans to files
- `sanciones/exportar` - Export sanctions search to files

**Why excluded**: These endpoints return binary file data (PDF/Excel/CSV) instead of structured JSON data, making them unsuitable for a CLI tool focused on data extraction and processing.

#### Portal Configuration Endpoints (2 missing)
- `vpd/{vpd}/configuracion` - Get portal navigation configuration
- `enlaces` - Get portal links and micro-windows

**Why excluded**: These endpoints return web portal configuration data (navigation menus, links) that are not relevant for data extraction purposes.

#### Subscription/Alert System (5 missing)
- `suscripciones/alta` - Create new alert subscription
- `suscripciones/altaidentificado` - Create subscription with token
- `suscripciones/activar` - Activate subscription
- `suscripciones/login` - Login to subscription service
- `suscripciones/cerrar` - Close session
- `suscripciones/detalle` - Get subscription details
- `suscripciones/modificar` - Modify subscription
- `suscripciones/anular` - Cancel subscription
- `suscripciones/reactivar` - Reactivate subscription
- `suscripciones/recuperarcontrasena` - Recover password
- `suscripciones/restablecercontrasena` - Reset password

**Why excluded**: The subscription system requires user authentication, password management, and email verification - functionality better suited for the official web portal rather than a CLI data extraction tool.

### Recommended Usage
- **Test First**: Always test commands with small datasets before large-scale usage
- **Use Verbose Mode**: Enable `--verbose` for debugging API issues or monitoring large extractions
- **Check API Status**: Verify that specific endpoints are working before relying on them for production use
- **Monitor for Updates**: The Spanish government may update the API without notice

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Poetry for dependency management

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
make test-integration   # Run integration tests
make clean              # Remove build artifacts
make all                # Install, lint, format, and test
```

## 🙏 Acknowledgments

This project is inspired by previous work from [Jaime Ortega Obregón](https://github.com/JaimeObregon/subvenciones/tree/main).

## 📜 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.
