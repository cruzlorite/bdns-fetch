# Python API reference

Generated from the package's docstrings: one page per module, named after
the module it documents.

**The public API** is what the package exports in its `__all__`
([`BDNSClient`][bdns.fetch.client.BDNSClient],
[`BDNSError`][bdns.fetch.exceptions.BDNSError],
[`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError],
[`RateLimiter`][bdns.fetch.utils.RateLimiter] and the enums in
[`types`][bdns.fetch.types]), the client's `fetch_*`, [`get`][bdns.fetch.client.BDNSClient.get], [`get_bytes`][bdns.fetch.client.BDNSClient.get_bytes]
and [`pages`][bdns.fetch.client.BDNSClient.pages] methods, and the [`dates`][bdns.fetch.dates] and
[`contract`][bdns.fetch.contract] modules. That does not change without a
major version; see [compatibility](../../compatibility.md).

The rest is documented because it explains the design, not because it is
stable: underscore names and the [`cli`][bdns.fetch.cli] and
[`options`][bdns.fetch.options] modules may change in any release.
