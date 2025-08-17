BDNS API
========
[![PyPI version](https://badge.fury.io/py/bdns-api.svg)](https://badge.fury.io/py/bdns-api)

A command-line tool for ingesting and processing data from the BDNS (Base de Datos Nacional de Subvenciones) API.
This tool allows you to fetch subsidies data from the Spanish government BDNS API, process it, and store it in a variety of formats.
It is designed to be flexible and extensible, allowing you to customize the data processing and storage to suit your needs.

## Precedents & Special Thanks
The motivation for this project stems from the need to efficiently ingest and process data from the BDNS API. The BDNS API provides a wealth of information, but the process of fetching, processing, and storing that data can be complex and time-consuming. This tool aims to simplify that process and make it more accessible to developers and data scientists.
This project is inspired by the previous work from Jaime Ortega Obregón, which can be found at [jaimeortega/bdns-ingest](https://github.com/jaimeortega/bdns-ingest).
Special thanks to him and all contributors of previous projects that have paved the way for this tool.

## Features
- Fetch subsidies data from the Spanish government BDNS API
- Store data in various formats (CSV, JSON, PARQUET, Arrow IPC, Feather) and compression methods (gzip, brotli, lz4)
- Support for custom data processing functions
- Command-line interface for easy usage
- Integration with 27 different BDNS API endpoints

## Installation
To install the BDNS Ingestion Tool, you can clone the repository and install the required dependencies using pip:

```bash
git clone https://github.com/cruzlorite/bdns-api.git
cd bdns-api
poetry install
```

You can also install the package directly from PyPI:

```bash
pip install bdns-api
```

## Usage
To use the BDNS Ingestion Tool, you can run the following command:

```bash
bdns-api --help
```

This will display the help message with all available options and commands.

## Testing

The project includes integration tests that validate commands against the real BDNS API to ensure functionality and data integrity.

### Running Integration Tests

```bash
# Run integration tests against the real BDNS API
poetry run pytest tests/integration/ -v -s -m integration

# Using Make command
make test-integration
```

### Test Results
The integration tests validate:
- **API Connectivity**: Ensures commands can successfully connect to the BDNS API
- **Data Retrieval**: Verifies that data is properly fetched and processed
- **Output Format**: Confirms that output files are created in the correct JSONL format
- **Data Structure**: Validates that returned data contains expected fields

Example test output:
```
🚀 Running Integration Tests Against Real BDNS API...

✅ Organos Integration Test Passed!
   Records: 22
   Sample: MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACIÓN

✅ Actividades Integration Test Passed!
   Records: 21

🎉 All Integration Tests Completed!
```

### Available Commands Tested
- **organos**: Fetches government organs/ministries data
- **actividades**: Fetches economic activities data

The tests create temporary output files, validate the data structure, and clean up automatically.

## Cite
If you use this tool in your research or projects, please consider citing it as follows:

```bibtex
@misc{bdns-ingest,
  author = {José María Cruz-Lorite},
  title = {BDNS Ingest},
  year = {2025},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/cruzlorite/bdns-ingest}},
  note = {GitHub repository},
  url = {https://github.com/cruzlorite/bdns-ingest}
}
```

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for more details.
