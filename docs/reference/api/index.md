# Referencia de la API Python

Generada desde los docstrings del paquete: una página por módulo, con el
nombre del módulo que documenta.

**Lo público** es lo que exporta el paquete en su `__all__`
([`BDNSClient`][bdns.fetch.client.BDNSClient],
[`BDNSError`][bdns.fetch.exceptions.BDNSError],
[`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError],
[`RateLimiter`][bdns.fetch.utils.RateLimiter] y los enums de
[`types`][bdns.fetch.types]), los métodos `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] y
[`pages`][bdns.fetch.client.BDNSClient.pages] del cliente, y los módulos [`dates`][bdns.fetch.dates] y
[`contract`][bdns.fetch.contract]. Eso no cambia sin una versión mayor; ver
[compatibilidad](../../compatibility.md).

El resto se documenta porque explica el diseño, no porque sea estable:
los nombres con guion bajo y los módulos [`cli`][bdns.fetch.cli] y
[`options`][bdns.fetch.options] pueden cambiar en cualquier versión.
