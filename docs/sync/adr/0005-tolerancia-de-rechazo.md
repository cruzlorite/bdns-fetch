# 0005. Tolerancia de rechazo fijada por ejecución

**Estado:** aceptada · **Fecha:** 2026-09-06

## Contexto

Algunos registros llegan malformados: el backend devuelve a veces una
página de error HTML en lugar de JSON para un registro concreto. Un
registro sin clave natural utilizable no se puede versionar.

Descartar alguno suelto es lo correcto: son un rasgo documentado y
permanente del origen, y perder un backfill de varias horas por uno de
ellos no ayuda a nadie.

Descartar la mayor parte de un lote no es el mismo suceso. Significa que
cambió la forma de lo que devuelve el origen, y aplicar lo que sobrevivió
es activamente destructivo: el staging queda casi vacío, y para una
reconciliación completa —o para la detección de bajas por ventana— un lote
vacío es indistinguible de "aquí se retiró todo".

## Decisión

Una ejecución rechaza el lote entero cuando los descartes cruzan un
límite. Tres parámetros, y los tres se fijan **por ejecución**, no por
entidad:

- `max_ratio`, fracción del lote que puede ser inservible (10% por
  defecto).
- `max_count`, tope absoluto. Atrapa un cambio de forma en un lote lo
  bastante grande como para esconderlo bajo la fracción: 200.000 registros
  malos de 20 millones es un 1%, por debajo de cualquier ratio sensato, y
  aun así significa que algo se rompió.
- `min_to_enforce_ratio`, por debajo de tantos descartes la fracción no
  se aplica. Una ventana estrecha puede traer tres registros, donde uno
  malo ya es un tercio del lote.

Son **tolerancias operativas, no afirmaciones sobre los datos**. Por eso,
a diferencia de la política de payload, no llevan valores por entidad.

## Consecuencias

- Un lote rechazado deja la ejecución como `failed`, con el motivo
  anotado, y los datos intactos.
- Los registros descartados van a `_sync_errors` con su contexto.
- Quien orquesta puede subir el límite para un origen que tiene un mal
  día, o bajarlo para enterarse antes.
