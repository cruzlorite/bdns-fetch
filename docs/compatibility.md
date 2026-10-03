# Compatibilidad

`bdns-fetch` sigue [versionado semántico](https://semver.org/lang/es/): una
versión mayor (`3.0.0`) puede romper; una menor (`2.1.0`) añade sin romper;
un parche (`2.0.1`) solo corrige. Cada cambio queda en el
[CHANGELOG](https://github.com/cruzlorite/bdns-fetch/blob/main/CHANGELOG.md).

## Qué es la API pública

Lo que no cambia de forma incompatible sin una versión mayor:

- lo que exporta el paquete en su `__all__`;
- los métodos `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] y [`pages`][bdns.fetch.client.BDNSClient.pages] de
  [`BDNSClient`][bdns.fetch.client.BDNSClient], y los argumentos de su
  constructor;
- los atributos de [`BDNSError`][bdns.fetch.exceptions.BDNSError] y
  [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError];
- los módulos [`dates`][bdns.fetch.dates] y [`contract`][bdns.fetch.contract];
- en el CLI: los nombres de los comandos y sus opciones, los códigos de
  salida y el formato de salida (JSON Lines, o los bytes del documento).

Todo lo demás (nombres con guion bajo, los módulos
[`cli`][bdns.fetch.cli], [`options`][bdns.fetch.options],
[`endpoints`][bdns.fetch.endpoints] y [`utils`][bdns.fetch.utils] salvo
[`RateLimiter`][bdns.fetch.utils.RateLimiter], los textos de los mensajes y los logs) puede cambiar en
cualquier versión.

Los **registros** son los de la API, tal cual ([ADR 0004](adr/0004-records-as-plain-dicts.md)):
si la API cambia un campo, cambia sin que medie ninguna versión de
`bdns-fetch`.

## Versiones de Python

Se da soporte a las versiones de Python que prueba el CI (hoy, 3.11 a
3.14). Dejar de soportar una versión, solo cuando llegue al final de su
vida, es un cambio menor anunciado en el CHANGELOG.

## Con bdns-sync

`bdns-sync` declara el rango de `bdns-fetch` que admite y su CI lo prueba
también contra la rama principal de `bdns-fetch`, para detectar una
ruptura antes de publicarla.

| bdns-sync | bdns-fetch |
|---|---|
| 0.5.x | ^1.3 |
| 0.6.x | ^2.0 |

## Cómo se publica

Una etiqueta `vX.Y.Z` en la rama principal publica en PyPI, siempre que coincida con
la versión de `pyproject.toml` y pasen los tests. No hay otra forma de
publicar.
