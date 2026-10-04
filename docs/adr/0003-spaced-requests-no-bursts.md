# 0003. Peticiones espaciadas, sin ráfagas

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Las buenas prácticas oficiales fijan un máximo de 10 peticiones por segundo y por IP. Un limitador clásico de tipo *token bucket* empieza con el cubo lleno, así que deja pasar de golpe tantas peticiones como su capacidad y después se ajusta a la media.

Las pruebas contra el servicio real muestran que el servidor responde con un `429` a las ráfagas aunque la media esté dentro del límite: diez hilos que solo respetaban la media dejaron de funcionar en cuestión de segundos. En cambio, con las peticiones espaciadas aguanta 9,8 por segundo de forma continuada ([las pruebas](../explanation/api-behavior.md#rate-limit)). Si el cliente no espacia las peticiones, cualquier programa que use varios hilos tiene que hacerlo por su cuenta.

## Decisión

El [`RateLimiter`][bdns.fetch.utils.RateLimiter] espacia las peticiones por defecto (`burst=1`). El limitador por defecto es uno solo por proceso, compartido por todos los clientes y todos los hilos, y deja pasar 9,5 peticiones por segundo, es decir, una cada 105 milisegundos aproximadamente, con algo de margen respecto al límite. Se puede pasar otro limitador al constructor, y en la línea de comandos se ajusta con `--rate-limit`.

## Consecuencias

- Al empezar una descarga no aparecen errores `429`.
- Quien usa el cliente no necesita espaciar las peticiones por su cuenta.
- El límite es por proceso y el de la API es por IP, así que varios procesos desde la misma IP tienen que repartírselo con `rate_limiter` o `--rate-limit`. Un limitador compartido entre procesos (con un fichero o con Redis, por ejemplo) queda fuera del alcance del proyecto.
