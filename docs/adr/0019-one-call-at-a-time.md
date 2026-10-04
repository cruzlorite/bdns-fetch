# 0019. Una llamada cada vez por defecto

**Estado:** aceptada · **Fecha:** 2026-10-04

## Contexto

Las [buenas prácticas oficiales](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) de la IGAE piden expresamente "no realizar llamadas de forma concurrente, ya que los recursos son limitados y es necesario un uso racional de los mismos", y advierten de que un uso abusivo puede acabar en el corte del acceso.

Hacer varias llamadas en paralelo acelera las descargas, pero no es lo que las hace posibles. Lo que permite descargar años de datos sin errores es dividir las consultas por fechas en tramos semanales ([las pruebas](../fetch/explanation/api-behavior.md#range-reliability)); el paralelismo solo reduce el tiempo total, sobre todo en las búsquedas paginadas, donde cada página tarda un par de segundos en llegar.

## Decisión

Por defecto se hace una sola llamada cada vez (`max_workers=1`). Quien necesite ir más rápido puede subirlo con `max_workers` o `--max-workers`, sabiendo que se aparta de la recomendación oficial. El espaciado de las peticiones ([decisión 0008](0008-spaced-requests-no-bursts.md)) y la paginación en orden ([decisión 0010](0010-ordered-bounded-pagination.md)) se mantienen tal cual cuando se usan varios hilos.

## Consecuencias

- El uso por defecto sigue la recomendación de quien gestiona la API, lo que reduce el riesgo de que corte el acceso.
- Las búsquedas paginadas grandes tardan más: una semana de concesiones (236.113 filas) se descarga en unos 60 segundos en lugar de 15 con cinco hilos ([las mediciones](../fetch/explanation/api-behavior.md#concurrency)). Las llamadas pequeñas, como el detalle de una convocatoria, apenas se ven afectadas mientras el servidor responde rápido, porque ya las limita el máximo de peticiones por segundo.
- Dentro de la recomendación no hay margen para ir más rápido desde el cliente: cada página tarda lo que tarda el servidor en prepararla y enviarla.
- Quien sube `max_workers` asume la responsabilidad de hacerlo.
