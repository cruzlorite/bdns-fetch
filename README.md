BDNS Ingest
===========
[![PyPI version](https://badge.fury.io/py/bdns-ingest.svg)](https://badge.fury.io/py/bdns-ingest)
[![Build Status](https://travis-ci.com/cruzlorite/bdns-ingest.svg?branch=main)](https://travis-ci.com/cruzlorite/bdns-ingest)
[![Coverage Status](https://coveralls.io/repos/github/cruzlorite/bdns-ingest/badge.svg?branch=main)](https://coveralls.io/github/cruzlorite/bdns-ingest?branch=main)

A command-line tool for ingesting and processing data from the BDNS API.
This tool allows you to fetch data from the BDNS API, process it, and store it in a variety of formats.
It is designed to be flexible and extensible, allowing you to customize the data processing and storage to suit your needs.

## Precedents & Special Thanks
The motivation for this project stems from the need to efficiently ingest and process data from the BDNS API. The BDNS API provides a wealth of information, but the process of fetching, processing, and storing that data can be complex and time-consuming. This tool aims to simplify that process and make it more accessible to developers and data scientists.
This project is inspired by the previous work from Jaime Ortega Obregón, which can be found at [jaimeortega/bdns-ingest](https://github.com/jaimeortega/bdns-ingest).
Special thanks to him and all contributors of previous projects that have paved the way for this tool.

## Features
- Fetch data from the BDNS API
- Store data in various formats (CSV, JSON, PARQUET, Arrow IPC, Feather) and compression methods (gzip, brotli, lz4)
- Support for custom data processing functions
- Command-line interface for easy usage

## Installation
To install the BDNS Ingestion Tool, you can clone the repository and install the required dependencies using pip:

```bash
git clone https://github.com/yourusername/bdns-ingest.git
cd bdns-ingest
poetry install
```

You can also install the package directly from PyPI:

```bash
pip install bdns-ingest
```

## Usage
To use the BDNS Ingestion Tool, you can run the following command:

```bash
bdns-ingest --help
```

This will display the help message with all available options and commands.

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
