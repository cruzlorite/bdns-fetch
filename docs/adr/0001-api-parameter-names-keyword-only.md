# 0001. Parámetros con el nombre de la API, solo por nombre

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Cada endpoint acepta entre cero y veinticinco parámetros, con nombres en
camelCase y en español (`fechaRegInicio`, `tipoAdministracion`). Si se
pueden pasar por posición, nadie recuerda el orden de veinte parámetros:
un argumento en el sitio equivocado manda un filtro distinto sin ningún
error.

Traducir los nombres a `snake_case` o al inglés haría el código más
"pythónico", pero rompería la correspondencia con la documentación
oficial, que es la única referencia de qué hace cada parámetro.

## Decisión

Los parámetros de los métodos `fetch_*` llevan **exactamente el nombre
que les da la API** y son **solo por nombre** (keyword-only). Los
obligatorios no tienen valor por defecto. El CLI sigue la misma regla:
`--fechaDesde`, no `--fecha-desde`.

## Consecuencias

- La documentación oficial se aplica tal cual, al cliente y al CLI.
- Una llamada se lee sola: `fetch_organos(idAdmon="C")`.
- Añadir o reordenar parámetros nunca rompe a nadie.
- Los nombres no siguen PEP 8. Es deliberado, y `ruff` no lo marca porque
  la regla de nombres no está activada.
