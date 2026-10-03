# 0002. Reintentar solo los fallos transitorios

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Hasta la 1.3 solo se reintentaban los errores de red. Un `503`, un `429`
o un `ERR_MANTENIMIENTO_BBDD` se lanzaban al primer intento, dijera lo que
dijera `max_retries`. `bdns-sync` configuraba 8 reintentos creyendo que le
protegían de los baches del servidor, y no lo hacían. Además,
`max_retries=3` significaba tres *intentos*, y al agotarse llegaba un
`tenacity.RetryError` en lugar del error real.

Reintentarlo todo tampoco vale: un `400` repetido sigue siendo un `400`,
y reintentarlo solo retrasa el aviso y gasta cupo de peticiones.

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
- Quien captura [`BDNSError`][bdns.fetch.exceptions.BDNSError] no tiene que cambiar nada; quien quiera
  distinguir lo transitorio tiene la subclase.
- La lista de códigos transitorios es una medición, no una certeza: si
  aparece otro, se añade a
  [`TRANSIENT_API_ERROR_CODES`][bdns.fetch.client.TRANSIENT_API_ERROR_CODES].
