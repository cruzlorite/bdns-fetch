# 0003. Peticiones espaciadas, sin ráfagas

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Las buenas prácticas oficiales fijan 10 peticiones por segundo por IP. El
limitador de la 1.3 era un *token bucket* que arrancaba lleno: permitía
una ráfaga de 10 peticiones simultáneas y luego 10 por segundo de media.

Medido contra el servicio real, el servidor responde `429` a las ráfagas
aunque la media cumpla: 10 hilos que solo respetaban la media se cayeron
en segundos. Con los arranques espaciados acepta 9,8 peticiones por
segundo sostenidas ([medición](../explanation/api-behavior.md#rate-limit)).
`bdns-sync` lo sorteaba espaciando sus propias llamadas por encima del
cliente.

## Decisión

El [`RateLimiter`][bdns.fetch.utils.RateLimiter] espacia las peticiones
por defecto (`burst=1`). El limitador por defecto es uno por proceso,
compartido por todos los clientes y hilos, a 9,5 peticiones por segundo:
una cada ~105 ms, con margen sobre el límite. Se puede pasar otro al
constructor, y el CLI lo ajusta con `--rate-limit`.

## Consecuencias

- La paginación concurrente no provoca `429` al arrancar.
- Los consumidores no necesitan su propio espaciado.
- El límite es por proceso; el de la API es por IP. Varios procesos en la
  misma IP deben repartírselo con `rate_limiter` o `--rate-limit`. Un
  limitador entre procesos (fichero, Redis) queda fuera de alcance.
