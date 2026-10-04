# Endpoints sin método propio

Los 29 endpoints de consulta tienen su método `fetch_*`. Para el resto (la configuración de los portales, los enlaces, las exportaciones...) puedes pedir cualquier ruta y se aplican igualmente el límite de peticiones, los reintentos y la conversión de parámetros.

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

- [`get`][bdns.fetch.client.BDNSClient.get] devuelve el documento JSON ya convertido, o `None` si la API responde con un `204`.
- [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] devuelve el contenido tal cual llega.
- [`pages`][bdns.fetch.client.BDNSClient.pages] recorre una búsqueda paginada y te da cada página completa, en orden y con sus campos de paginación (`totalElements`, `totalPages`...).

Los parámetros se convierten igual que en los métodos `fetch_*`: las fechas pasan a `dd/mm/aaaa`, los enums a su valor y las listas a claves repetidas, y los `None` se omiten.

## Desde la terminal

```console
$ bdns-fetch get /vpd/GE/configuracion
$ bdns-fetch get /concesiones/busqueda -p pageSize=5 -p page=0
$ bdns-fetch -o c.pdf get /convocatorias/pdf -p id=608268 -p vpd=GE --binary
```

`-p CLAVE=VALOR` se puede repetir, y si repites una clave se envía como lista.
