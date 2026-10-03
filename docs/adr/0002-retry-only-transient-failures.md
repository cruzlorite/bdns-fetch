# 0002. Reintentar solo los fallos transitorios

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

La API falla de dos maneras. Unas veces de forma pasajera: errores de
red, `429`, `5xx`, o `ERR_MANTENIMIENTO_BBDD`, que devuelve de forma
intermitente en consultas largas
([medición](../explanation/api-behavior.md#range-reliability)). Otras de
forma permanente: un parámetro mal formado, un documento que no existe.

Un proceso desatendido tiene que aguantar las primeras sin intervención.
Reintentar las segundas no sirve de nada: un `400` repetido sigue siendo
un `400`, y reintentarlo solo retrasa el aviso y gasta cupo de
peticiones. Quien configura los reintentos espera además que el número
signifique reintentos, y que al agotarse le llegue el error real, no un
envoltorio de la librería de reintentos.

## Decisión

Se reintentan los errores de red, los HTTP `429`, `500`, `502`, `503` y
`504`, y el código `ERR_MANTENIMIENTO_BBDD` con cualquier estado. Esos
errores son [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
el resto se lanza al momento.

La espera es exponencial con margen aleatorio (empieza en `wait_time`, se
duplica, tope 60 s) y respeta `Retry-After`. `max_retries` cuenta
reintentos después del primer intento. Al agotarse se relanza el último
error.

## Consecuencias

- Un proceso desatendido aguanta baches de minutos sin configuración
  especial.
- El margen aleatorio evita que varios clientes reintenten a la vez.
- Quien solo quiere saber si algo falló captura [`BDNSError`][bdns.fetch.exceptions.BDNSError]; quien
  quiere distinguir lo transitorio tiene la subclase.
- La lista de códigos transitorios es una medición, no una certeza: si
  aparece otro, se añade a
  [`TRANSIENT_API_ERROR_CODES`][bdns.fetch.client.TRANSIENT_API_ERROR_CODES].
