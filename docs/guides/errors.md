# Errores y reintentos

Qué reintenta el cliente, qué no, y cómo reaccionar a lo que llega hasta tu código.

## Lo que se reintenta solo

| Fallo | ¿Se reintenta? |
|---|---|
| Error de red, timeout | Sí |
| HTTP `429` (límite de peticiones) | Sí, respetando `Retry-After` si llega |
| HTTP `500`, `502`, `503`, `504` | Sí |
| Código `ERR_MANTENIMIENTO_BBDD`, con cualquier estado | Sí |
| Cualquier otro error (`400`, `404`, `ERR_VALIDACION`...) | No: repetir una petición incorrecta no la arregla |

La espera empieza en `wait_time` segundos y se duplica en cada reintento, más un margen aleatorio, hasta un máximo de 60 s. `max_retries` cuenta los reintentos **después** del primer intento; 0 los desactiva.

```python
client = BDNSClient(max_retries=5, wait_time=10)   # para un proceso desatendido
```

```console
$ bdns-fetch --max-retries 5 --wait-time 10 concesiones-busqueda ...
```

Para un proceso nocturno que no debe caerse por un bache de unos minutos: 5 reintentos con 10 s de espera inicial esperan 10, 20, 40, 60 y 60 s (más el margen aleatorio), y aguantan unos 3-4 minutos de problemas por petición.

## Lo que llega a tu código

Todo error de la API es un [[`BDNSError`][bdns.fetch.exceptions.BDNSError]][bdns.fetch.exceptions.BDNSError]:

| Atributo | Contenido |
|---|---|
| `message` | Lo que dijo la API, normalmente en español |
| `status_code` | Estado HTTP |
| `code` | Código de error de la API (`ERR_VALIDACION`...), si lo trae |
| `url` | La URL pedida |
| `details` | Estado, URL, cabeceras y el principio del cuerpo, para logs |

Los transitorios que agotaron sus reintentos son [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError], subclase del anterior:

```python
from bdns.fetch import BDNSError, BDNSTransientError

try:
    registros = list(client.fetch_concesiones_busqueda(**rango))
except BDNSTransientError:
    programar_reintento_mas_tarde()
except BDNSError as error:
    if error.code == "ERR_VALIDACION":
        corregir_parametros(error.message)
    else:
        raise
```

Los errores de red agotados llegan como la excepción original de `requests` (`ConnectionError`, `Timeout`).

!!! warning "Los iteradores fallan al iterar"
    Un método de búsqueda devuelve un iterador perezoso: el error salta al consumirlo, no al llamar al método. Envuelve el bucle, no la llamada.

## Desde el CLI

El CLI convierte cualquier [`BDNSError`][bdns.fetch.exceptions.BDNSError] en un mensaje y código de salida 1, con una pista según el tipo de error. `--verbose` añade los detalles de la respuesta y el log de cada petición HTTP.
