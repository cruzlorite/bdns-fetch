# Errores y reintentos

Qué reintenta el cliente por su cuenta, qué no, y cómo tratar los errores que llegan hasta tu código.

## Lo que se reintenta automáticamente

| Fallo | ¿Se reintenta? |
|---|---|
| Error de red o tiempo de espera agotado | Sí |
| HTTP `429` (demasiadas peticiones) | Sí, y si la respuesta trae `Retry-After`, se respeta |
| HTTP `500`, `502`, `503` y `504` | Sí |
| Código `ERR_MANTENIMIENTO_BBDD`, venga con el estado que venga | Sí |
| Cualquier otro error (`400`, `404`, `ERR_VALIDACION`...) | No, porque repetir una petición incorrecta no la arregla |

La primera espera dura `wait_time` segundos y cada reintento la duplica, con un pequeño margen aleatorio, hasta un máximo de 60 segundos. `max_retries` cuenta los reintentos **después** del primer intento; con 0 no se reintenta nada.

```python
client = BDNSClient(max_retries=5, wait_time=10)   # para un proceso desatendido
```

```console
$ bdns-fetch --max-retries 5 --wait-time 10 concesiones-busqueda ...
```

Para un proceso nocturno que no debería caerse por un bache de unos minutos, estos valores van bien: las esperas son de 10, 20, 40, 60 y 60 segundos (más el margen aleatorio), así que cada petición aguanta unos tres o cuatro minutos de problemas.

## Lo que llega a tu código

Cualquier error de la API llega como [`BDNSError`][bdns.fetch.exceptions.BDNSError]:

| Atributo | Qué contiene |
|---|---|
| `message` | Lo que ha dicho la API, normalmente en español |
| `status_code` | El código de estado HTTP |
| `code` | El código de error de la API (`ERR_VALIDACION`...), si lo trae |
| `url` | La URL que se pidió |
| `details` | Estado, URL, cabeceras y el principio de la respuesta, para los logs |

Los fallos pasajeros que han agotado sus reintentos llegan como [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError], que es una subclase de la anterior:

```python
from bdns.fetch import BDNSError, BDNSTransientError

try:
    registros = list(client.fetch_concesiones_busqueda(**rango))
except BDNSTransientError:
    reintentar_mas_tarde()
except BDNSError as error:
    if error.code == "ERR_VALIDACION":
        revisar_parametros(error.message)
    else:
        raise
```

Si lo que se agotan son los reintentos de un error de red, recibes la excepción original de `requests` (`ConnectionError` o `Timeout`).

!!! warning "El error salta al recorrer los resultados"
    Los métodos de búsqueda devuelven un iterador que no descarga nada hasta que lo recorres, así que el error aparece en el bucle y no al llamar al método. Pon el `try` alrededor del bucle.

## Desde la terminal

La terminal convierte cualquier [`BDNSError`][bdns.fetch.exceptions.BDNSError] en un mensaje y termina con código 1, con una pista distinta según el tipo de error. Con `--verbose` verás además los detalles de la respuesta y una línea por cada petición HTTP.

Por ejemplo, al pedir un documento que no existe:

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

- Las líneas `DEBUG` son las que añade `--verbose`: cada petición, con lo que tardó la respuesta (130,6 ms) y lo que ocupaba. Solo hay una, porque un `400` con `ERR_VALIDACION` no se reintenta.
- `Error:` es lo que dijo la API, con su código y su mensaje.
- `Hint:` es la pista de la terminal sobre qué revisar.
- El resto son los detalles de la respuesta (estado, cabeceras y cuerpo), que es lo que conviene adjuntar si abres un issue. Las cookies de sesión se han acortado aquí con `…`.
