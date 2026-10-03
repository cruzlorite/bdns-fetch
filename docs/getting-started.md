# Empezar

Cinco minutos: instalar, una consulta desde la terminal, la misma desde Python, y qué hacer cuando algo falla.

## 1. Instalar

Python 3.11 a 3.14.

```console
$ pip install bdns-fetch
$ bdns-fetch --version
bdns-fetch 2.0.0
```

## 2. Primera consulta desde la terminal

Los catálogos son pequeños y no necesitan parámetros:

```console
$ bdns-fetch sectores | head -1
{"descripcion": "Todos", "id": 24}
```

Cada línea es un registro en JSON ([JSON Lines](https://jsonlines.org/)), listo para `jq`, pandas o DuckDB. Con `-o` se guarda en un fichero:

```console
$ bdns-fetch -o organos.jsonl organos --idAdmon C
```

Las búsquedas están paginadas. El CLI trae **una** página por defecto y avisa si hay más:

```console
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 > enero.jsonl
... WARNING - Returning pages 0 to 0 of 5. Request all pages (num_pages=0) for the complete result.
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 --num-pages 0 > enero.jsonl
```

Cada comando documenta sus parámetros, con el nombre que les da la API:

```console
$ bdns-fetch concesiones-busqueda --help
```

## 3. La misma consulta desde Python

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

Dos diferencias con el CLI:

- En Python se descargan **todas** las páginas por defecto. `num_pages` y `from_page` acotan.
- Los parámetros se pasan siempre por nombre, y las fechas son objetos `date`.

Las descargas son perezosas: no se envía nada hasta que se itera.

## 4. Cuando algo falla

Los fallos transitorios (red, `429`, `5xx`, `ERR_MANTENIMIENTO_BBDD`) se reintentan solos. Si se agotan los reintentos, o el error no es transitorio, el CLI lo dice y sale con código 1:

```console
$ bdns-fetch planesestrategicos-documentos --idDocumento 1
Error: Error (ERR_VALIDACION): No se ha podido obtener el documento solicitado
Hint: Check the parameter values and formats; see the command's --help.
```

En Python es una excepción con los datos para decidir qué hacer:

```python
from bdns.fetch import BDNSError

try:
    pdf = client.fetch_planesestrategicos_documentos(idDocumento=1)
except BDNSError as error:
    print(error.status_code, error.code, error.message)
```

## Siguientes pasos

- Descargar por fecha de registro sin perder días: [descargas incrementales](guides/incremental.md).
- Manejar errores y reintentos: [errores y reintentos](guides/errors.md).
- Por qué la API obliga a todo esto: [comportamiento de la API](explanation/api-behavior.md).
