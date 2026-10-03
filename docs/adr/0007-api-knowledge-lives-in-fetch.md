# 0007. El conocimiento de la API vive en bdns-fetch

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Casi todo lo que se sabe del comportamiento real de la API (la semántica
contraria de `fechaRegFin` y `fechaHasta`, los fallos en rangos largos,
el rechazo de ráfagas, la retención por endpoint, los cambios espurios)
se midió construyendo `bdns-sync`, y vivía allí: en su documentación, en
su `api_contract.py` y en sus helpers de fechas.

Pero son hechos de la API, no del almacenamiento. Quien usaba solo
`bdns-fetch` tropezaba con ellos sin aviso, y `bdns-sync` compensaba
defectos del cliente (el espaciado de peticiones) en vez de corregirlos
donde tocaba.

## Decisión

Lo que trata de la API vive en `bdns-fetch`:

- la documentación de su [comportamiento](../explanation/api-behavior.md);
- [`dates`][bdns.fetch.dates], que traduce un rango inclusivo a los
  argumentos de cada familia de fechas y trocea rangos largos;
- [`contract`][bdns.fetch.contract] y `bdns-fetch check-api`, que
  comprueban esa semántica contra el servicio real.

`bdns-sync` los usa y documenta solo lo que decide él a partir de ellos.

## Consecuencias

- Cualquier usuario de `bdns-fetch` descarga bien por fechas sin conocer
  la historia.
- Un hecho de la API tiene un solo sitio; la documentación de `bdns-sync`
  enlaza aquí.
- Cambiar esa semántica es un cambio de `bdns-fetch`, que `bdns-sync`
  recoge al subir de versión.
