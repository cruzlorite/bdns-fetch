# 0012. Lo que se sabe de la API vive en bdns-fetch

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Hay dos proyectos: `bdns-fetch` habla con la API y `bdns-sync` guarda lo que esta devuelve. Lo que se sabe del comportamiento real de la API (que `fechaRegFin` y `fechaHasta` tratan al revés el último día, que los rangos largos fallan, que no admite ráfagas, cuánto histórico guarda cada endpoint o qué datos cambian de forma sin cambiar de verdad) le sirve a cualquiera que la use, no solo a quien guarda los datos.

Si ese conocimiento estuviera en la parte que guarda los datos, quien usara solo el cliente se encontraría con todos esos problemas sin ningún aviso, y la parte que guarda los datos acabaría compensando las carencias del cliente en lugar de corregirlas donde corresponde.

## Decisión

Todo lo que tiene que ver con la API está en `bdns-fetch`:

- la documentación de su [comportamiento](../fetch/explanation/api-behavior.md);
- [`dates`][bdns.fetch.dates], que convierte un rango cerrado en los parámetros que necesita cada familia de fechas y divide los rangos largos;
- [`contract`][bdns.fetch.contract] y `bdns-fetch check-api`, que comprueban ese comportamiento contra el servicio real.

`bdns-sync` usa todo esto y solo documenta lo que decide a partir de ello.

## Consecuencias

- Cualquiera que use `bdns-fetch` puede descargar por fechas correctamente sin conocer toda esta historia.
- Cada dato sobre la API está en un solo sitio, y la documentación de `bdns-sync` enlaza a él.
- Si cambia el comportamiento de la API, el cambio se hace en `bdns-fetch` y `bdns-sync` lo recibe al actualizarse.
