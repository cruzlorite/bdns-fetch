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
