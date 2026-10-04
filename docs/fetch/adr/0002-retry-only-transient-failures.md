# 0002. Solo se reintentan los fallos pasajeros

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

La API falla de dos maneras. A veces es algo pasajero: un error de red, un `429`, un error `5xx` o un `ERR_MANTENIMIENTO_BBDD`, que aparece de vez en cuando en las consultas largas ([las pruebas](../explanation/api-behavior.md#range-reliability)). Otras veces el fallo es definitivo: un parámetro mal escrito o un documento que no existe.

Un proceso que se ejecuta solo tiene que superar los primeros sin que nadie intervenga. Reintentar los segundos no sirve de nada, porque un `400` repetido sigue siendo un `400`, y lo único que se consigue es tardar más en enterarse y gastar peticiones. Además, quien configura los reintentos espera que el número que pone sean reintentos y que, cuando se agoten, le llegue el error real y no un envoltorio de la librería de reintentos.

## Decisión

Se reintentan los errores de red, los HTTP `429`, `500`, `502`, `503` y `504`, y el código `ERR_MANTENIMIENTO_BBDD` venga con el estado que venga. Estos errores son [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError]; los demás se lanzan en el momento.

La espera crece de forma exponencial con un margen aleatorio (empieza en `wait_time`, se duplica en cada intento y no pasa de 60 segundos), y se respeta la cabecera `Retry-After`. `max_retries` cuenta los reintentos que se hacen después del primer intento, y cuando se agotan se relanza el último error.

## Consecuencias

- Un proceso desatendido aguanta baches de varios minutos sin configurar nada especial.
- El margen aleatorio evita que varios clientes reintenten todos a la vez.
- Quien solo necesita saber si algo ha fallado captura [`BDNSError`][bdns.fetch.exceptions.BDNSError]; quien quiere distinguir los fallos pasajeros tiene la subclase.
- La lista de códigos pasajeros sale de lo que hemos observado, no de una especificación. Si aparece otro, se añade a [`TRANSIENT_API_ERROR_CODES`][bdns.fetch.client.TRANSIENT_API_ERROR_CODES].
