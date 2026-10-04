# 0008. Una llamada cada vez por defecto

**Estado:** aceptada · **Fecha:** 2026-10-04

## Contexto

Las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) de la IGAE piden expresamente "no realizar llamadas de forma concurrente, ya que los recursos son limitados y es necesario un uso racional de los mismos", y advierten de que un uso abusivo puede acabar en el corte del acceso.

Hacer varias llamadas en paralelo acelera las descargas, pero no es lo que las hace posibles. Lo que permite descargar años de datos sin errores es dividir las consultas por fechas en tramos semanales ([las pruebas](../explanation/api-behavior.md#range-reliability)); el paralelismo solo reduce el tiempo total, sobre todo cuando hay que hacer miles de llamadas pequeñas, como al pedir el detalle de cada convocatoria.

## Decisión

Por defecto se hace una sola llamada cada vez (`max_workers=1`). Quien necesite ir más rápido puede subirlo con `max_workers` o `--max-workers`, sabiendo que se aparta de la recomendación oficial. El espaciado de las peticiones ([decisión 0003](0003-spaced-requests-no-bursts.md)) y la paginación en orden ([decisión 0005](0005-ordered-bounded-pagination.md)) se mantienen tal cual cuando se usan varios hilos.

## Consecuencias

- El uso por defecto sigue la recomendación de quien gestiona la API, lo que reduce el riesgo de que corte el acceso.
- Las descargas grandes tardan más. Donde más se nota es en los pasos que hacen una llamada por registro: el detalle de un mes de convocatorias (unas 6.000) pasa de unos 11 minutos con ocho hilos a entre 23 minutos y algo más de 3 horas, según la carga del servidor.
- Quien sube `max_workers` asume la responsabilidad de hacerlo.
