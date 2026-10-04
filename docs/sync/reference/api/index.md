# Referencia de Python

Se genera a partir de los docstrings del código, con una página por módulo que lleva su nombre. Por eso está en inglés.

Cada página muestra todo lo que define el módulo, incluidas las funciones internas, y lo que distingue unas de otras es el nombre:

- **Sin guion bajo**: pensadas para usarse desde fuera del módulo. Lo que además aparece en el `__all__` del módulo se considera público, y no cambia sin avisarlo en el CHANGELOG como cambio incompatible.
- **Con guion bajo** ([`_apply`][bdns.sync.sinks.sql.scd2._apply], [`_order_independent`][bdns.sync.hashing._order_independent]...): internas. Nada de fuera del módulo debería importarlas, y pueden cambiar sin aviso. Están documentadas porque explican muchas de las decisiones del diseño.

Si lo que buscas es el porqué y no el qué, mira las páginas de [conceptos](../../explanation/payload-policy.md).
