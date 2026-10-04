# Errors and retries

What the client retries, what it does not, and how to react to what reaches your code.

## What is retried automatically

| Failure | Retried? |
|---|---|
| Network error, timeout | Yes |
| HTTP `429` (rate limit) | Yes, honouring `Retry-After` when sent |
| HTTP `500`, `502`, `503`, `504` | Yes |
| `ERR_MANTENIMIENTO_BBDD` code, with any status | Yes |
| Any other error (`400`, `404`, `ERR_VALIDACION`...) | No: repeating a bad request does not fix it |

The wait starts at `wait_time` seconds and doubles on each retry, plus random jitter, up to 60 s. `max_retries` counts retries **after** the first attempt; 0 disables them.

```python
client = BDNSClient(max_retries=5, wait_time=10)   # for an unattended process
```

```console
$ bdns-fetch --max-retries 5 --wait-time 10 concesiones-busqueda ...
```

For a nightly job that should not die over a rough patch of a few minutes: 5 retries starting at 10 s wait 10, 20, 40, 60 and 60 s (plus jitter), riding out about 3-4 minutes of trouble per request.

## What reaches your code

Every API error is a [[`BDNSError`][bdns.fetch.exceptions.BDNSError]][bdns.fetch.exceptions.BDNSError]:

| Attribute | Content |
|---|---|
| `message` | What the API said, usually in Spanish |
| `status_code` | HTTP status |
| `code` | The API's error code (`ERR_VALIDACION`...), if any |
| `url` | The requested URL |
| `details` | Status, URL, headers and the start of the body, for logs |

Transient ones that ran out of retries are [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError], a subclass:

```python
from bdns.fetch import BDNSError, BDNSTransientError

try:
    records = list(client.fetch_concesiones_busqueda(**date_range))
except BDNSTransientError:
    schedule_retry_later()
except BDNSError as error:
    if error.code == "ERR_VALIDACION":
        fix_parameters(error.message)
    else:
        raise
```

Network errors that ran out of retries arrive as the original `requests` exception (`ConnectionError`, `Timeout`).

!!! warning "Iterators fail when iterated"
    A search method returns a lazy iterator: the error is raised while consuming it, not when calling the method. Wrap the loop, not the call.

## From the CLI

The CLI turns any [`BDNSError`][bdns.fetch.exceptions.BDNSError] into a message and exit code 1, with a hint depending on the kind of error. `--verbose` adds the response details and a log line per HTTP request.

For example, asking for a document that does not exist:

```console
$ bdns-fetch --verbose planesestrategicos-documentos --idDocumento 1
2026-10-04 20:02:23,995 - bdns.fetch.client - DEBUG - HTTP REQUEST: GET https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/documentos?idDocumento=1
2026-10-04 20:02:23,997 - urllib3.connectionpool - DEBUG - Starting new HTTPS connection (1): www.infosubvenciones.es:443
2026-10-04 20:02:24,125 - urllib3.connectionpool - DEBUG - https://www.infosubvenciones.es:443 "GET /bdnstrans/api/planesestrategicos/documentos?idDocumento=1 HTTP/1.1" 400 None
2026-10-04 20:02:24,126 - bdns.fetch.client - DEBUG - HTTP RESPONSE: 400  - 130.6ms, 89 bytes
Error: ERR_VALIDACION: No se ha podido obtener el documento solicitado
Hint: Check the parameter values and formats; see the command's --help.
HTTP 400 from https://www.infosubvenciones.es/bdnstrans/api/planesestrategicos/documentos?idDocumento=1
Response headers:
  Date: Sun, 04 Oct 2026 18:02:24 GMT
  Content-Type: application/json
  Connection: keep-alive
  Vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers
  Set-Cookie: XSRF-TOKEN=…; Path=/bdnstrans; Version=1; Secure, TS01bc68c4=…; Path=/; Secure; HttpOnly, TS014c174a=…; path=/bdnstrans; HttpOnly; Secure
  Cache-Control: no-cache, no-store, max-age=0, must-revalidate
  Pragma: no-cache
  Expires: 0
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=15552000; includeSubDomains
  Referrer-Policy: strict-origin-when-cross-origin
  Transfer-Encoding: chunked
Response body: {"codigo":"ERR_VALIDACION","errores":["No se ha podido obtener el documento solicitado"]}
```

- The `DEBUG` lines are the ones `--verbose` adds: each request, with how long the response took (130.6 ms) and its size. There is only one, because a `400` with `ERR_VALIDACION` is not retried.
- `Error:` is what the API said, with its code and message.
- `Hint:` is the terminal's hint on what to check.
- The rest are the response details (status, headers and body), which is what to attach if you open an issue. The session cookies are shortened here with `…`.
