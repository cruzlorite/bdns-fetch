# 0005. Paginación concurrente, en orden y con memoria acotada

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Una búsqueda grande tiene miles de páginas. Pedirlas en serie desperdicia
el cupo de peticiones esperando latencia. La 1.3 las pedía en paralelo,
pero de una forma que causaba tres problemas:

- entregaba las páginas en el orden en que **terminaban**, así que el
  resultado salía barajado;
- enviaba **todas** las peticiones de golpe, de modo que con un
  consumidor lento el resultado entero se acumulaba en memoria;
- si el consumidor dejaba de iterar, se descargaban igualmente todas.

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
