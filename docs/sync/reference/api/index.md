# Referencia de la API

Generada desde los docstrings del paquete. Está dividida en dos partes, y
la diferencia importa:

- **Superficie pública.** Lo que declara el `__all__` de cada módulo. Es
  el contrato: estos nombres no cambian sin nota de ruptura en el
  changelog.
- **Internals.** Los submódulos de `sinks.sql`, con sus helpers privados
  incluidos. Nada fuera de `bdns.sync.sinks.sql` debería importarlos y
  pueden cambiar sin aviso. Están documentados porque el razonamiento que
  llevan dentro es lo que explica el diseño.

Las páginas se llaman como el módulo que documentan.

Para el porqué, y no el qué, están las páginas de
[Diseño](../../explanation/payload-policy.md).
