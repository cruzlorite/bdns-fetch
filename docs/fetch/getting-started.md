# Primeros pasos

En cinco minutos vas a instalar el paquete, hacer una consulta desde la terminal, repetirla desde Python y ver qué pasa cuando algo falla.

## 1. Instalación

Necesitas Python 3.11 o posterior (hasta la 3.14).

```console
$ pip install bdns-tools
$ bdns-fetch --version
bdns-fetch 2.0.0
```

## 2. Una consulta desde la terminal

Los catálogos son pequeños y no necesitan parámetros, así que son un buen punto de partida:

```console
$ bdns-fetch sectores | head -1
{"descripcion": "Todos", "id": 24}
```

Cada línea es un registro en formato JSON ([JSON Lines](https://jsonlines.org/)), que puedes procesar directamente con `jq`, pandas o DuckDB. Con `-o` lo guardas en un fichero:

```console
$ bdns-fetch -o organos.jsonl organos --idAdmon C
```

Las búsquedas vienen paginadas. Desde la terminal se descarga **una sola página** por defecto, y si hay más te avisa:

```console
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 > enero.jsonl
... WARNING - Returning pages 0 to 0 of 5. Request all pages (num_pages=0) for the complete result.
$ bdns-fetch concesiones-busqueda --fechaDesde 2024-01-01 --fechaHasta 2024-01-07 --num-pages 0 > enero.jsonl
```

Cada comando explica sus parámetros, que se llaman igual que en la API:

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

Hay dos diferencias con la terminal. Desde Python se descargan **todas** las páginas por defecto (puedes limitarlo con `num_pages` y `from_page`), y los parámetros se pasan siempre por nombre, con las fechas como objetos `date`.

Además, la descarga no empieza hasta que recorres los resultados: llamar al método no hace ninguna petición.

## 4. Cuando algo falla

Los fallos pasajeros (problemas de red, `429`, errores `5xx` o `ERR_MANTENIMIENTO_BBDD`) se reintentan solos. Si se agotan los reintentos, o si el error no es pasajero, la terminal te lo dice y termina con código 1:

```console
$ bdns-fetch planesestrategicos-documentos --idDocumento 1
Error: ERR_VALIDACION: No se ha podido obtener el documento solicitado
Hint: Check the parameter values and formats; see the command's --help.
```

En Python recibes una excepción con los datos necesarios para decidir qué hacer:

```python
from bdns.fetch import BDNSError

try:
    pdf = client.fetch_planesestrategicos_documentos(idDocumento=1)
except BDNSError as error:
    print(error.status_code, error.code, error.message)
```

## Y ahora qué

- Si quieres descargar por fecha de registro sin perder días: [descargas incrementales](guides/incremental.md).
- Si quieres controlar los errores y los reintentos: [errores y reintentos](guides/errors.md).
- Si quieres saber por qué hace falta todo esto: [comportamiento de la API](explanation/api-behavior.md).
