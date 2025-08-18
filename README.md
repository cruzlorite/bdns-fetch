BDNS API
========
[![PyPI version](https://badge.fury.io/py/bdns-api.svg)](https://badge.fury.io/py/bdns-api)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive command-line tool for accessing and processing data from the BDNS (Base de Datos Nacional de Subvenciones) API - the Spanish government's national subsidies database.

## ✨ Features

- **29 API Commands**: Complete coverage of all BDNS API endpoints
- **JSONL Output Format**: Clean JSON Lines format for easy data processing
- **Flexible Configuration**: Customizable parameters for each command

## 📋 Available Commands

This tool provides access to all **29 BDNS API endpoints**. Each command fetches specific data from the Spanish government's subsidies database.

For a complete list of all commands and their parameters, use:
```bash
bdns-api --help
```

For help on a specific command:
```bash
bdns-api [command-name] --help
# Example: bdns-api organos --help
```

**📖 API Documentation**: Complete endpoint documentation is available at [BDNS API Swagger](https://www.infosubvenciones.es/bdnstrans/doc/swagger)

## 🚀 Quick Start

### Installation

**From PyPI (recommended):**
```bash
pip install bdns-api
```

**From source:**
```bash
git clone https://github.com/cruzlorite/bdns-api.git
cd bdns-api
poetry install
```

### CLI Usage

**Getting Help:**
```bash
# List all available commands
bdns-api --help

# Get help for a specific command  
bdns-api organos --help
bdns-api ayudasestado-busqueda --help
```

**Basic Examples:**
```bash
# Fetch government organs data to file
bdns-api organos --output-file government_organs.jsonl

# Get economic activities (to stdout by default)
bdns-api actividades

# Search state aids with filters
bdns-api ayudasestado-busqueda \
  --descripcion "innovation" \
  --num-pages 3 \
  --pageSize 1000 \
  --output-file innovation_aids.jsonl

# Get specific strategic plan by ID
bdns-api planesestrategicos --idPES 459 --output-file plan_459.jsonl
```

**Common Parameters:**
- `--output-file FILE`: Save output to file (defaults to stdout)
- `--vpd CODE`: Territory code (GE=Spain, specific regions available)
- `--num-pages N`: Number of pages to fetch (for paginated commands)
- `--pageSize N`: Records per page (default: 10000, max: 10000)

**Advanced Search Example:**
```bash
# Search concessions with multiple filters
bdns-api concesiones-busqueda \
  --descripcion "research" \
  --fechaDesde "2023-01-01" \
  --fechaHasta "2024-12-31" \
  --tipoAdministracion "C" \
  --num-pages 10 \
  --output-file research_concessions.jsonl
```

## 📖 More Examples

```bash
# Download all government organs
bdns-api organos --output-file government_structure.jsonl

# Search for innovation-related subsidies
bdns-api ayudasestado-busqueda --descripcion "innovation" --output-file innovation_aids.jsonl

# Get latest calls for proposals
bdns-api convocatorias-ultimas --output-file latest_calls.jsonl

# Search sanctions data
bdns-api sanciones-busqueda --output-file sanctions.jsonl
```

Output format (JSON Lines):
```json
{"id": 1, "descripcion": "MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN", "codigo": "E04"}
{"id": 2, "descripcion": "MINISTERIO DE ASUNTOS EXTERIORES, UNIÓN EUROPEA Y COOPERACIÓN", "codigo": "E05"}
```

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Poetry for dependency management

### Development Setup
```bash
# Clone and setup
git clone https://github.com/cruzlorite/bdns-api.git
cd bdns-api
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
