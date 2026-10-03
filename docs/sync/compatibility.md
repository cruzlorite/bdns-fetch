# Compatibilidad

`bdns-sync` sigue [versionado semántico](https://semver.org/lang/es/).
Mientras esté en `0.x`, una versión menor (`0.7.0`) puede romper y un
parche (`0.6.1`) solo corrige; desde `1.0.0`, solo una versión mayor
puede romper. Cada cambio queda en el
[CHANGELOG](https://github.com/cruzlorite/bdns-sync/blob/main/CHANGELOG.md),
y los incompatibles van marcados.

## Qué es la API pública

- **El CLI**: los comandos (`sync`, `delta`, `backfill`, `list`,
  `check-api`), sus opciones y variables de entorno, y los códigos de
  salida.
- **El esquema del destino**: las columnas de las tablas de entidades y
  de las tablas `_sync_*` que describe el [modelo de datos](reference/data-model.md).
- **La API Python**: lo que cada módulo declara en su `__all__`; en
  particular [`ENTITIES`][bdns.sync.entities.ENTITIES],
  [`sync_entity`][bdns.sync.entities.sync_entity], la interfaz
  [`Sink`][bdns.sync.sinks.Sink] y [`SyncStats`][bdns.sync.sinks.SyncStats].

Los nombres con guion bajo, los mensajes y los logs pueden cambiar en
cualquier versión.

## El esquema solo crece

El esquema del destino cambia solo **añadiendo columnas que admiten
nulos**, y cada ejecución añade sola las que le falten a un destino
creado por una versión anterior
([ADR 0008](adr/0008-run-linked-versions-additive-migrations.md)). Nunca
se renombra, se cambia de tipo ni se borra una columna: actualizar
`bdns-sync` no exige migrar nada a mano. Un cambio que no fuera aditivo
sería una versión mayor con instrucciones de migración.

Cambiar la clave natural o las reglas de hash de una entidad no cambia
el esquema, pero sí los hashes: la siguiente ejecución versiona de nuevo
las filas afectadas. Esos cambios se anuncian en el CHANGELOG.

## Versiones de Python

Se da soporte a las versiones de Python que prueba el CI (hoy, 3.11 a
3.14). Dejar de soportar una, solo cuando llegue al final de su vida, se
anuncia en el CHANGELOG.

## Con bdns-fetch

`bdns-sync` declara el rango de `bdns-fetch` que admite. Su CI prueba
contra esa versión y, en un job aparte, contra la rama principal de
`bdns-fetch`, para detectar una ruptura antes de que se publique.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## Cómo se publica

Una etiqueta `vX.Y.Z` en la rama principal publica en PyPI y la imagen en
`ghcr.io`, siempre que coincida con la versión de `pyproject.toml`. No hay
otra forma de publicar.
