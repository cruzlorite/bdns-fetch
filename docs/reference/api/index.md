# Referencia de Python

Se genera a partir de los docstrings del código, con una página por módulo que lleva su nombre. Por eso está en inglés.

**La parte pública** es lo que exporta el paquete en su `__all__`
([`BDNSClient`][bdns.fetch.client.BDNSClient],
[`BDNSError`][bdns.fetch.exceptions.BDNSError],
[`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError],
[`RateLimiter`][bdns.fetch.utils.RateLimiter] y los enums de
[`types`][bdns.fetch.types]), los métodos `fetch_*`,
[`get`][bdns.fetch.client.BDNSClient.get],
[`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes] y
[`pages`][bdns.fetch.client.BDNSClient.pages] del cliente, y los módulos
[`dates`][bdns.fetch.dates] y [`contract`][bdns.fetch.contract]. Nada de
esto cambia de forma incompatible sin una versión mayor; lo explica la
página de [compatibilidad](../../compatibility.md).

El resto está documentado porque ayuda a entender el diseño, no porque sea
estable: los nombres que empiezan por guion bajo y los módulos
[`cli`][bdns.fetch.cli] y [`options`][bdns.fetch.options] pueden cambiar en
cualquier versión.
