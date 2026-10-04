# Endpoints without a method

The 29 query endpoints each have their `fetch_*`. For the rest (portal configuration, links, exports), the client requests any path under the same policies: rate limit, retries and parameter encoding.

## From Python

```python
from bdns.fetch import BDNSClient

client = BDNSClient()

config = client.get("/vpd/GE/configuracion")         # one JSON document
links = client.get("/enlaces")
pdf = client.get_bytes("/convocatorias/pdf", {"id": 608268, "vpd": "GE"})

for page in client.pages("/concesiones/busqueda", {"pageSize": 1000}, num_pages=2):
    print(page["number"], page["totalElements"], len(page["content"]))
```

- [`get`][bdns.fetch.client.BDNSClient.get] returns the decoded JSON document (`None` if the API answers `204`).
- [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] returns the body as is.
- [`pages`][bdns.fetch.client.BDNSClient.pages] walks a paginated search and yields whole pages, with their pagination fields (`totalElements`, `totalPages`...), in order.

Parameters are encoded as in the `fetch_*` methods: dates as `dd/mm/yyyy`, enums by value, lists as repeated keys, `None` dropped.

## From the CLI

```console
$ bdns-fetch get /vpd/GE/configuracion
$ bdns-fetch get /concesiones/busqueda -p pageSize=5 -p page=0
$ bdns-fetch -o c.pdf get /convocatorias/pdf -p id=608268 -p vpd=GE --binary
```

`-p KEY=VALUE` repeats; repeating a key sends it as a list.
