# Endpoints sin método propio

Los 29 endpoints de consulta tienen su `fetch_*`. Para el resto (configuración del portal, enlaces, exportaciones), el cliente pide cualquier ruta con las mismas políticas: límite de peticiones, reintentos y codificación de parámetros.

## Desde Python

```python
from bdns.fetch import BDNSClient

client = BDNSClient()

config = client.get("/vpd/GE/configuracion")         # un documento JSON
enlaces = client.get("/enlaces")
pdf = client.get_bytes("/convocatorias/pdf", {"id": 608268, "vpd": "GE"})

for pagina in client.pages("/concesiones/busqueda", {"pageSize": 1000}, num_pages=2):
    print(pagina["number"], pagina["totalElements"], len(pagina["content"]))
```

- [`get`][bdns.fetch.client.BDNSClient.get] devuelve el documento JSON decodificado (`None` si la API responde `204`).
- [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] devuelve el cuerpo tal cual.
- [`pages`][bdns.fetch.client.BDNSClient.pages] recorre una búsqueda paginada y entrega las páginas completas, con sus campos de paginación (`totalElements`, `totalPages`...), en orden.

Los parámetros se codifican igual que en los métodos `fetch_*`: fechas como `dd/mm/aaaa`, enums por su valor, listas como claves repetidas, `None` se omite.

## Desde el CLI

```console
$ bdns-fetch get /vpd/GE/configuracion
$ bdns-fetch get /concesiones/busqueda -p pageSize=5 -p page=0
$ bdns-fetch -o c.pdf get /convocatorias/pdf -p id=608268 -p vpd=GE --binary
```

`-p CLAVE=VALOR` se repite; repetir una clave la envía como lista.
