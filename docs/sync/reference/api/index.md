# Referencia de la API

Generada desde los docstrings del paquete: una página por módulo, con el
nombre del módulo que documenta.

Cada página muestra todo lo que el módulo define, helpers privados
incluidos. Lo que distingue unos de otros es el nombre:

- **Sin guion bajo**: pensado para usarse desde fuera del módulo. Lo que
  además declara el `__all__` del módulo es el contrato: esos nombres no
  cambian sin nota de ruptura en el changelog.
- **Con guion bajo** (`_apply`, `_order_independent`…): internos. Nada de
  fuera del módulo debería importarlos, y pueden cambiar sin aviso. Están
  documentados porque el razonamiento que llevan dentro es lo que explica
  el diseño.

Para el porqué, y no el qué, están las páginas de
[Explicación](../../explanation/payload-policy.md).
