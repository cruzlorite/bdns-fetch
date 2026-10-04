# 0006. Los parámetros se llaman como en la API y se pasan por nombre

**Estado:** aceptada · **Fecha:** 2026-10-03

## Contexto

Cada endpoint admite entre cero y veinticinco parámetros, con nombres en español y en camelCase (`fechaRegInicio`, `tipoAdministracion`). Si se pudieran pasar por posición, nadie recordaría el orden de veinte parámetros, y un argumento colocado en el sitio equivocado enviaría un filtro distinto sin dar ningún error.

Traducir los nombres al inglés o a `snake_case` haría el código más "pythónico", pero rompería la correspondencia con la documentación oficial, que es la única referencia de lo que hace cada parámetro.

## Decisión

Los parámetros de los métodos `fetch_*` se llaman **exactamente igual que en la API** y solo se pueden pasar **por nombre**. Los obligatorios no tienen valor por defecto. La línea de comandos sigue la misma regla: `--fechaDesde`, no `--fecha-desde`.

## Consecuencias

- La documentación oficial sirve tal cual, tanto para el cliente como para la línea de comandos.
- Una llamada se entiende sola: `fetch_organos(idAdmon="C")`.
- Añadir o reordenar parámetros no rompe nada a nadie.
- Los nombres no siguen la PEP 8. Es intencionado, y `ruff` no lo señala porque esa regla no está activada.
