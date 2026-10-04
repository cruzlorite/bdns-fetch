# 0010. Lo que hace falta saber de la API lo aporta bdns-fetch

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Para sincronizar por fechas hay que tener en cuenta cosas que se han medido sobre la API: que `fechaRegFin` no incluye el último día y `fechaHasta` sí, que los rangos largos fallan, que la API no admite ráfagas y que hay que comprobar cada día que nada de eso ha cambiado. Todo eso tiene que ver con la API, no con cómo se guardan los datos, y lo necesita cualquiera que la use.

Si la parte que guarda los datos lo resolviera por su cuenta, el cliente de la API se quedaría sin ello, y la parte que guarda los datos acabaría compensando las carencias del cliente (espaciando las peticiones por encima de él, desactivando su barra de progreso, obligándole a descargar todas las páginas) en lugar de corregirlas donde corresponde.

## Decisión

`bdns-sync` usa lo que aporta `bdns-fetch`: `registration_range` y `period_range` para traducir los periodos, `split_range` para dividirlos, `check_api_contract` para comprobar la API, y el propio cliente para espaciar las peticiones. Es la otra mitad de la decisión que `bdns-fetch` recoge en su [decisión 0007](https://cruzlorite.github.io/bdns-fetch/adr/0007-api-knowledge-lives-in-fetch/).

## Consecuencias

- Lo que se ha medido sobre la API está en un solo sitio, la documentación de `bdns-fetch`, y la de `bdns-sync` enlaza a ella y solo explica sus propias decisiones.
- `bdns-sync` depende de una versión mayor concreta de `bdns-fetch`, y su integración continua se prueba también contra la rama principal de `bdns-fetch` para detectar cualquier incompatibilidad antes de que se publique.
