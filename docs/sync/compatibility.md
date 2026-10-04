# Compatibilidad

`bdns-sync` sigue el [versionado semántico](https://semver.org/lang/es/). Mientras esté en `0.x`, una versión menor (`0.7.0`) puede romper la compatibilidad y un parche (`0.6.1`) solo corrige errores; a partir de la `1.0.0`, solo podrá romperla una versión mayor. Todos los cambios se anotan en el [CHANGELOG](https://github.com/cruzlorite/bdns-sync/blob/main/CHANGELOG.md), y los incompatibles van marcados.

## Qué se considera público

- **La línea de comandos**: los comandos (`sync`, `delta`, `backfill`, `list` y `check-api`), sus opciones y variables de entorno, y los códigos de salida.
- **El esquema de la base de datos**: las columnas de las tablas de entidad y de las tablas `_sync_*` que describe el [modelo de datos](reference/data-model.md).
- **La API de Python**: lo que cada módulo declara en su `__all__`, en particular [`ENTITIES`][bdns.sync.entities.ENTITIES], [`sync_entity`][bdns.sync.entities.sync_entity], la interfaz [`Sink`][bdns.sync.sinks.Sink] y [`SyncStats`][bdns.sync.sinks.SyncStats].

Los nombres que empiezan por guion bajo, los mensajes y los logs pueden cambiar en cualquier versión.

## El esquema solo crece

El esquema de la base de datos solo cambia **añadiendo columnas que admiten valores nulos**, y cada ejecución añade por su cuenta las que le falten a una base de datos creada con una versión anterior ([decisión 0008](adr/0008-run-linked-versions-additive-migrations.md)). Nunca se renombra una columna, se le cambia el tipo ni se borra, así que actualizar `bdns-sync` no te obliga a migrar nada a mano. Un cambio que no fuera de este tipo llegaría en una versión mayor, con instrucciones para migrar.

Cambiar la clave natural o las reglas de hash de una entidad no cambia el esquema, pero sí los hashes, de modo que la siguiente ejecución volvería a crear versiones de las filas afectadas. Cambios así se anuncian siempre en el CHANGELOG.

## Versiones de Python

Se da soporte a las versiones de Python que se prueban en la integración continua (ahora mismo, de la 3.11 a la 3.14). Una versión solo se deja de soportar cuando llega al final de su vida, y se avisa en el CHANGELOG.

## Con bdns-fetch

`bdns-sync` indica qué versiones de `bdns-fetch` admite. Su integración continua se prueba con esa versión y, en un trabajo aparte, con la rama principal de `bdns-fetch`, para detectar cualquier incompatibilidad antes de que se publique.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## Cómo se publica una versión

Al crear una etiqueta `vX.Y.Z` en la rama principal se publica la versión, siempre que coincida con la de `pyproject.toml`, que el CHANGELOG tenga su apartado y que pasen los tests. Primero se sube a PyPI. Solo si eso sale bien se publica la imagen en `ghcr.io`, se crea la release de GitHub, con las notas del CHANGELOG y los mismos ficheros que recibió PyPI, y se actualiza esta web. No hay otra forma de publicar.
