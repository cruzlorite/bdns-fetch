# 0010. Paginación en orden y sin acumular memoria

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Una búsqueda grande tiene miles de páginas. Cuando se piden varias en paralelo, la forma más sencilla de hacerlo (lanzar todas las peticiones y entregar cada página según llega) tiene tres problemas:

- el resultado sale en el orden en que **terminan** las peticiones, es decir, desordenado;
- si el código que recorre los resultados va más despacio que la descarga, el resultado entero se acaba acumulando en memoria;
- si se deja de recorrer a medias, se descargan igualmente todas las páginas.

## Decisión

Cuando se usan varios hilos, como mucho hay `2 × max_workers` peticiones pendientes. Las páginas se entregan en su orden: si la `k` llega antes que la `k-1`, espera. Cada página entregada deja sitio para pedir la siguiente, y al cerrar el iterador se cancelan las peticiones que quedaban.

## Consecuencias

- Para unos mismos datos, el resultado siempre sale en el mismo orden.
- La memoria que se usa depende del número de hilos, no del tamaño del resultado.
- Si el código que recorre los resultados va despacio, la descarga se frena en vez de acumular páginas.
- Una página lenta retrasa la entrega de las siguientes hasta que llega, aunque mientras tanto los demás hilos siguen descargando.
