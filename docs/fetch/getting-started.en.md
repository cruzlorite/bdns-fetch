# Get started

Five minutes: install, one query from the terminal, the same from Python, and what to do when something fails.

## 1. Install

Python 3.11 to 3.14.

```console
$ pip install bdns
$ bdns-fetch --version
bdns-fetch 2.0.0
```

## 2. A first query from the terminal

Catalogs are small and take no parameters:

```console
$ bdns-fetch sectores | head -1
{"descripcion": "Todos", "id": 24}
```

Each line is one record as JSON ([JSON Lines](https://jsonlines.org/)), ready for `jq`, pandas or DuckDB. `-o` writes to a file:

```console
$ bdns-fetch -o organos.jsonl organos --idAdmon C
```

Searches are paginated. The CLI fetches **one** page by default and warns if there are more:

```console
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 > january.jsonl
... WARNING - Returning pages 0 to 0 of 5. Request all pages (num_pages=0) for the complete result.
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 --num-pages 0 > january.jsonl
```

Each command documents its parameters, under the names the API gives them:

```console
$ bdns-fetch concesiones-busqueda --help
```

## 3. The same query from Python

```python
from datetime import date

from bdns.fetch import BDNSClient

client = BDNSClient()

for concesion in client.fetch_concesiones_busqueda(
    fechaDesde=date(2024, 1, 1),
    fechaHasta=date(2024, 1, 7),
):
    print(concesion["beneficiario"], concesion["importe"])
```

Two differences from the CLI:

- Python fetches **every** page by default. `num_pages` and `from_page` narrow it.
- Parameters are always passed by name, and dates are `date` objects.

Downloads are lazy: nothing is sent until you iterate.

## 4. When something fails

Transient failures (network, `429`, `5xx`, `ERR_MANTENIMIENTO_BBDD`) are retried automatically. If the retries run out, or the error is not transient, the CLI says so and exits with code 1:

```console
$ bdns-fetch planesestrategicos-documentos --idDocumento 1
Error: ERR_VALIDACION: No se ha podido obtener el documento solicitado
Hint: Check the parameter values and formats; see the command's --help.
```

In Python it is an exception carrying what you need to decide what to do:

```python
from bdns.fetch import BDNSError

try:
    pdf = client.fetch_planesestrategicos_documentos(idDocumento=1)
except BDNSError as error:
    print(error.status_code, error.code, error.message)
```

## Next steps

- Download by registration date without losing days: [incremental downloads](guides/incremental.md).
- Handle errors and retries: [errors and retries](guides/errors.md).
- Why the API makes all this necessary: [API behaviour](explanation/api-behavior.md).
