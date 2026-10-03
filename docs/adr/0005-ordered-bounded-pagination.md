# 0005. Paginación concurrente, en orden y con memoria acotada

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Una búsqueda grande tiene miles de páginas. Pedirlas en serie desperdicia
el cupo de peticiones esperando latencia, así que se piden en paralelo.
La forma ingenua (enviar todas las peticiones y entregar cada página
cuando llega) tiene tres problemas:

- el resultado sale en el orden en que **terminan** las peticiones, es
  decir, barajado;
- con un consumidor lento, el resultado entero se acumula en memoria;
- si el consumidor deja de iterar, se descargan igualmente todas.

## Decisión

Una ventana deslizante con `2 × max_workers` peticiones en vuelo. Las
páginas se entregan en orden de página: si la `k` llega antes que la
`k-1`, espera. Cada página entregada libera un hueco para la siguiente.
Al cerrar el iterador, las peticiones pendientes se cancelan.

## Consecuencias

- El resultado es determinista para un mismo conjunto de datos.
- La memoria está acotada por la ventana, no por el tamaño del resultado.
- Un consumidor lento frena la descarga (contrapresión) en vez de
  acumular.
- Una página lenta retiene la entrega de las siguientes hasta que llega;
  con la ventana, los hilos siguen trabajando mientras tanto.
