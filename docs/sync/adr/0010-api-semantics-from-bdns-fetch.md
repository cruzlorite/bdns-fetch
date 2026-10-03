# 0010. La semántica de la API la aporta bdns-fetch

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Sincronizar por fechas depende de hechos medidos sobre la API: que
`fechaRegFin` es exclusivo y `fechaHasta` inclusivo, que los rangos
largos fallan, que la API rechaza las ráfagas, que hay que comprobar cada
día que nada de eso ha cambiado. Esos hechos son de la API, no del
almacenamiento: los necesita cualquiera que la use.

Si la capa de almacenamiento los implementa por su cuenta, el cliente de
la API se queda sin ellos y la capa de almacenamiento compensa sus
limitaciones (espaciar peticiones encima del cliente, parchear su barra
de progreso, forzar que descargue todas las páginas) en vez de
corregirlas donde tocan.

## Decisión

`bdns-sync` usa lo que aporta `bdns-fetch`: traducción de rangos con
`registration_range` y `period_range`, troceo con `split_range`,
comprobación de contrato con `check_api_contract` y espaciado de
peticiones en el cliente. Es la otra mitad de la decisión que
`bdns-fetch` registra en su
[ADR 0007](https://cruzlorite.github.io/bdns-fetch/adr/0007-api-knowledge-lives-in-fetch/).

## Consecuencias

- Las mediciones de la API tienen un solo sitio, en la documentación de
  `bdns-fetch`; la de `bdns-sync` enlaza allí y explica solo sus propias
  decisiones.
- `bdns-sync` depende de una versión mayor concreta de `bdns-fetch`, y su
  CI prueba también contra la rama principal de `bdns-fetch` para
  detectar una ruptura antes de que se publique.
