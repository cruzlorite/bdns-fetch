# Compatibilidad

`bdns-tools` sigue el [versionado semántico](https://semver.org/lang/es/): una versión mayor (`3.0.0`) puede romper la compatibilidad, una menor (`2.1.0`) añade cosas sin romper nada y un parche (`2.0.1`) solo corrige errores. La versión es la misma para todo el paquete, así que un cambio incompatible en cualquiera de sus módulos supone una versión mayor. Todos los cambios se anotan en el [CHANGELOG](https://github.com/cruzlorite/bdns-tools/blob/main/CHANGELOG.md), y los incompatibles van marcados.

## Qué se considera público en bdns.fetch

Esto no cambia de forma incompatible sin una versión mayor:

- lo que exporta el módulo en su `__all__`;
- los métodos `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] y [`pages`][bdns.fetch.client.BDNSClient.pages] de [`BDNSClient`][bdns.fetch.client.BDNSClient], y los argumentos de su constructor;
- los atributos de [`BDNSError`][bdns.fetch.exceptions.BDNSError] y [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
- los módulos [`dates`][bdns.fetch.dates] y [`contract`][bdns.fetch.contract];
- en la línea de comandos, los nombres de los comandos y sus opciones, los códigos de salida y el formato de lo que se escribe (JSON Lines, o el documento tal cual).

Todo lo demás puede cambiar en cualquier versión: los nombres que empiezan por guion bajo; los módulos [`cli`][bdns.fetch.cli], [`options`][bdns.fetch.options], [`endpoints`][bdns.fetch.endpoints] y [`utils`][bdns.fetch.utils] (salvo [`RateLimiter`][bdns.fetch.utils.RateLimiter]); los textos de los mensajes y los logs.

Los **registros** son los de la API tal cual ([decisión 0004](fetch/adr/0004-records-as-plain-dicts.md)), así que si la API cambia un campo, el cambio llega sin que haya una nueva versión de `bdns-tools` por medio.

## Qué se considera público en bdns.sync

- **La línea de comandos**: los comandos (`sync`, `delta`, `backfill`, `list` y `check-api`), sus opciones y variables de entorno, y los códigos de salida.
- **El esquema de la base de datos**: las columnas de las tablas de entidad y de las tablas `_sync_*` que describe el [modelo de datos](sync/reference/data-model.md).
- **La API de Python**: lo que cada módulo declara en su `__all__`, en particular [`ENTITIES`][bdns.sync.entities.ENTITIES], [`sync_entity`][bdns.sync.entities.sync_entity], la interfaz [`Sink`][bdns.sync.sinks.Sink] y [`SyncStats`][bdns.sync.sinks.SyncStats].

Los nombres que empiezan por guion bajo, los mensajes y los logs pueden cambiar en cualquier versión.

<a id="schema"></a>
### El esquema solo crece

El esquema de la base de datos solo cambia **añadiendo columnas que admiten valores nulos**, y cada ejecución añade por su cuenta las que le falten a una base de datos creada con una versión anterior ([decisión 0008](sync/adr/0008-run-linked-versions-additive-migrations.md)). Nunca se renombra una columna, se le cambia el tipo ni se borra, así que actualizar `bdns-tools` no te obliga a migrar nada a mano. Un cambio que no fuera de este tipo llegaría en una versión mayor, con instrucciones para migrar.

Cambiar la clave natural o las reglas de hash de una entidad no cambia el esquema, pero sí los hashes, de modo que la siguiente ejecución volvería a crear versiones de las filas afectadas. Cambios así se anuncian siempre en el CHANGELOG.

## Versiones de Python

Se da soporte a las versiones de Python que se prueban en la integración continua (ahora mismo, de la 3.11 a la 3.14). Una versión solo se deja de soportar cuando llega al final de su vida, y se avisa en el CHANGELOG.

<a id="previous-names"></a>
## Los nombres anteriores

Hasta la versión 1.3.0 de `bdns-fetch` y la 0.5.0 de `bdns-sync`, las dos herramientas se publicaban en PyPI como paquetes separados. Ahora vienen juntas en `bdns-tools`, con los mismos módulos ([`bdns.fetch`](fetch/reference/api/index.md) y [`bdns.sync`](sync/reference/api/index.md)) y los mismos comandos (`bdns-fetch` y `bdns-sync`), así que para actualizar basta con instalar `bdns-tools` en lugar de los paquetes anteriores. La numeración sigue la de `bdns-fetch`, de modo que la primera versión de `bdns-tools` es la 2.0.0.

## Cómo se publica una versión

Al crear una etiqueta `vX.Y.Z` en la rama principal se publica la versión, siempre que coincida con la de `pyproject.toml`, que el CHANGELOG tenga su apartado y que pasen los tests, tanto sobre el código como sobre el paquete ya construido. Primero se sube a PyPI. Solo si eso sale bien se publica la imagen en `ghcr.io`, se crea la release de GitHub, con las notas del CHANGELOG y los mismos ficheros que recibió PyPI, y se actualiza esta web. No hay otra forma de publicar.

Las etiquetas de las versiones anteriores se conservan: las de `bdns-fetch` hasta la 1.3.0 se llaman `v1.3.0`, y las de `bdns-sync` hasta la 0.5.0, `bdns-sync-v0.5.0`.
