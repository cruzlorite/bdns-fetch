# Compatibilidad

`bdns-fetch` sigue el [versionado semántico](https://semver.org/lang/es/): una versión mayor (`3.0.0`) puede romper la compatibilidad, una menor (`2.1.0`) añade cosas sin romper nada y un parche (`2.0.1`) solo corrige errores. Todos los cambios se anotan en el [CHANGELOG](https://github.com/cruzlorite/bdns-fetch/blob/main/CHANGELOG.md).

## Qué se considera público

Esto no cambia de forma incompatible sin una versión mayor:

- lo que exporta el paquete en su `__all__`;
- los métodos `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] y [`pages`][bdns.fetch.client.BDNSClient.pages] de [`BDNSClient`][bdns.fetch.client.BDNSClient], y los argumentos de su constructor;
- los atributos de [`BDNSError`][bdns.fetch.exceptions.BDNSError] y [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
- los módulos [`dates`][bdns.fetch.dates] y [`contract`][bdns.fetch.contract];
- en la línea de comandos, los nombres de los comandos y sus opciones, los códigos de salida y el formato de lo que se escribe (JSON Lines, o el documento tal cual).

Todo lo demás puede cambiar en cualquier versión: los nombres que empiezan por guion bajo; los módulos [`cli`][bdns.fetch.cli], [`options`][bdns.fetch.options], [`endpoints`][bdns.fetch.endpoints] y [`utils`][bdns.fetch.utils] (salvo [`RateLimiter`][bdns.fetch.utils.RateLimiter]); los textos de los mensajes y los logs.

Los **registros** son los de la API tal cual ([decisión 0004](adr/0004-records-as-plain-dicts.md)), así que si la API cambia un campo, el cambio llega sin que haya una nueva versión de `bdns-fetch` por medio.

## Versiones de Python

Se da soporte a las versiones de Python que se prueban en la integración continua (ahora mismo, de la 3.11 a la 3.14). Una versión solo se deja de soportar cuando llega al final de su vida, y se avisa en el CHANGELOG como cambio menor.

## Con bdns-sync

`bdns-sync` indica qué versiones de `bdns-fetch` admite, y su integración continua se prueba también contra la rama principal de `bdns-fetch` para detectar cualquier incompatibilidad antes de publicarla.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## Cómo se publica una versión

Al crear una etiqueta `vX.Y.Z` en la rama principal se publica la versión, siempre que coincida con la de `pyproject.toml`, que el CHANGELOG tenga su apartado y que pasen los tests. Primero se sube a PyPI. Solo si eso sale bien se crea la release de GitHub, con las notas del CHANGELOG y los mismos ficheros que recibió PyPI, y se actualiza esta web. No hay otra forma de publicar.
