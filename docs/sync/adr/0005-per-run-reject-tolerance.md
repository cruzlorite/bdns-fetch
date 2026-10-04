# 0005. Los límites de rechazo se fijan en cada ejecución

**Estado:** aceptada · **Fecha:** 2026-09-06

## Contexto

Algunos registros llegan mal: a veces el servidor devuelve una página de error en HTML en lugar del JSON de un registro concreto. Y un registro sin una clave natural utilizable no se puede versionar.

Descartar alguno suelto es lo correcto, porque es algo conocido y permanente de la API, y perder una carga de varias horas por uno de ellos no beneficia a nadie.

Pero descartar la mayor parte de un lote es algo muy distinto: significa que ha cambiado la forma de lo que devuelve la API, y aplicar lo que queda es directamente dañino. El staging se queda casi vacío, y para una comparación completa, o para la detección de bajas por periodo, un lote vacío no se distingue de «aquí se ha retirado todo».

## Decisión

Una ejecución rechaza el lote entero cuando los descartes superan un límite. Hay tres parámetros, y los tres se fijan **en cada ejecución**, no para cada entidad:

- `max_ratio`, la parte del lote que puede ser inservible (un 10% por defecto);
- `max_count`, un número máximo absoluto, que detecta un cambio de forma en un lote tan grande que quedaría por debajo de la proporción: 200.000 registros mal de 20 millones son un 1%, menos de lo que permitiría cualquier proporción razonable, y aun así significan que algo se ha roto;
- `min_to_enforce_ratio`, el número de descartes por debajo del cual no se aplica la proporción, porque un periodo corto puede traer tres registros y entonces uno mal ya es un tercio del lote.

Son **tolerancias de funcionamiento, no afirmaciones sobre los datos**, y por eso, a diferencia de la política de cada entidad, no tienen valores distintos por entidad.

## Consecuencias

- Un lote rechazado deja la ejecución como `failed`, con el motivo anotado, y no toca los datos.
- Los registros descartados se guardan en `_sync_errors` junto con su contexto.
- Quien lanza la sincronización puede subir el límite si la API tiene un mal día, o bajarlo para enterarse antes de cualquier problema.
