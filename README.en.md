# BDNS Fetch

[![PyPI version](https://badge.fury.io/py/bdns-fetch.svg)](https://badge.fury.io/py/bdns-fetch)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[🇪🇸 Spanish version](./README.md)

## Introduction

The **National Subsidies Database (BDNS)** is a Spanish public repository that provides transparency on all subsidies and public aid granted by administrations. Managed by the General Intervention of the State Administration (IGAE) under the Ministry of Finance, the BDNS has centralized information since 2014 for the state public sector and since 2016 for other administrations (see [datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones), [transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html)).
These data include the awarding body, amount, purpose, beneficiaries, and other relevant details of each subsidy.  
The BDNS is regulated by Article 20 of Law 38/2003, the General Subsidies Law, and by Royal Decree 130/2019 (see [datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones), [BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2019-4671)).  
The data are published online while respecting the honor and privacy of individuals.

BDNS data are accessible through the **National System for the Publicity of Subsidies and Public Aid (SNPSAP)**. Information can be consulted in HTML format on the official Ministry of Finance portal and exported to open formats such as CSV, XLSX, or PDF. There is also a REST API that provides data in JSON format ([datos.gob.es](https://datos.gob.es/en/catalogo/e05188501-base-de-datos-nacional-de-subvenciones)).  
The database is updated daily, but the official portal imposes limitations: for example, downloads are restricted to a maximum of 10,000 records per query.  
Legal data retention also applies: grants remain published for 4 years from their award date (only 1 year more in the case of individuals), after which they are automatically removed.

## Project Purpose

The goal of the **bdns-fetch** repository is to facilitate **programmatic** access to BDNS data. It is a Python library and command-line tool (CLI) that implements the official BDNS API, enabling automated extraction and analysis of subsidies. Specifically, bdns-fetch covers all 29 data endpoints available in the BDNS API, with full parameter support and automatic pagination handling. It offers both a clean, typed Python client interface and a `bdns-fetch` command for quick testing.  

This overcomes the limitations of the official web portal (basic and often slow search, no option for bulk downloads) since bdns-fetch allows automated queries and full extraction of data into JSONL files.

**Key advantages of bdns-fetch:**  
- Quickly download subsidies filtered by criteria (organization, date, description, etc.)  
- Apply automatic pagination without manually handling each page  
- Manage errors and retries automatically  

## Installation

```bash
pip install bdns-fetch
````

or

```bash
git clone https://github.com/cruzlorite/bdns-fetch.git
cd bdns-fetch
pip install .
```

## Usage

### Python Client

The library exposes a Python client for calling BDNS endpoints. For example, to get the list of registered organizations (ministries, agencies, etc.):

```python
from bdns.fetch.client import BDNSClient

# Initialize client
client = BDNSClient()

# Query the "organos" endpoint
organos = list(client.fetch_organos())
for org in organos:
    print(org["codigo"], "-", org["descripcion"])
```

Another example: search for state subsidies containing the text "research". Pagination is controlled by defining the page size and number of pages to retrieve:

```python
resultados = client.fetch_ayudasestado_busqueda(
    descripcion="research",
    pageSize=1000,   # records per page (max 10000)
    num_pages=5,     # maximum number of pages to retrieve
    from_page=0      # starting page (0 = first page)
)
for element in resultados:
    print(element["titulo"], "-", element["importe"])
```

It is also possible to download associated binary documents (e.g., calls for proposals or strategic plans) using the appropriate methods that return bytes. For example:

```python
# Download call-for-proposals PDF by ID (id and vpd obtained from BDNS)
pdf_bytes = client.fetch_convocatorias_pdf(id=608268, vpd="A07")
with open("convocatoria.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Command-Line Interface (CLI)

bdns-fetch includes a simple CLI. After installation, run
`bdns-fetch --help` to see options.

Retrieve and save the list of organizations:

```bash
bdns-fetch --output-file organos.jsonl organos
```

Search for State aid with a keyword and date range:

```bash
bdns-fetch --verbose --output-file ayudas_busqueda.jsonl ayudasestado-busqueda \
    --descripcion "innovation" --fechaDesde "2023-01-01" --fechaHasta "2024-12-31"
```

Download the latest official calls for proposals:

```bash
bdns-fetch --output-file convocatorias.jsonl convocatorias-ultimas
```

All data extracted by the CLI are saved in **JSON Lines** (`.jsonl`) format, where each line is an independent JSON object.

## Known Limitations and Warnings

* **Library limitations:** bdns-fetch **does not implement** certain endpoints that do not return JSON data. Specifically, it does not handle the *export* endpoints (file generation in CSV/XLSX from BDNS) nor the portal configuration or subscription system routes.

* **Data retention:** BDNS follows the legal regime of limited publicity. Subsidy records are automatically deleted **4 calendar years** after the year of award (only 2 years for subsidies to individuals). Therefore, you will not find very old grants in BDNS.

* **Use of public data:** Although the data come from official sources, it is the user’s responsibility to verify their suitability for each case. This tool provides no guarantee of accuracy, which may depend on the reporting administration. Furthermore, some personal data are protected: BDNS "publishes while respecting personal or family honor and privacy." Responsible use of information and compliance with data protection regulations is recommended.

* **Legal notice:** bdns-fetch is provided under the premise of open data reuse. **Law 38/2003** and **Royal Decree 130/2019** establish the conditions for subsidy publication. Use of this tool for purposes other than research and civic transparency must comply with current legislation. The author assumes no responsibility for misinterpretation or misuse of the obtained public data.

## License and Relevant Links

* **License:** bdns-fetch is licensed under the **GNU General Public License v3.0** (GPLv3) ([PyPI](https://pypi.org/project/bdns-fetch/), [GitHub](https://github.com/cruzlorite/bdns-fetch)). See the [LICENSE](https://chatgpt.com/c/LICENSE) file for details.

* **Official BDNS portal:** National System for the Publicity of Subsidies and Public Aid -- [Ministry of Finance (SNPSAP portal)](https://www.infosubvenciones.es/).

* **Law 38/2003 (General Subsidies Law):** official text in BOE ([link](https://www.boe.es/eli/es/l/2003/11/17/38)).

* **Royal Decree 130/2019:** regulates BDNS and publicity of subsidies, BOE ([link](https://www.boe.es/eli/es/rd/2019/03/08/130)).

* **Additional information:** State transparency portal on subsidies -- [transparencia.gob.es](https://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/Contratos/Subvenciones.html).

* **GPLv3:** license text at [gnu.org](https://www.gnu.org/licenses/gpl-3.0.html).

**bdns-fetch** is free software, developed to facilitate the reuse of public data and promote transparency. Contributions and collaboration are welcome!