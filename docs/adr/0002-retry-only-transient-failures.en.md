# 0002. Retry transient failures only

**Status:** accepted · **Date:** 2026-10-03

## Context

Up to 1.3 only network errors were retried. A `503`, a `429` or an
`ERR_MANTENIMIENTO_BBDD` was raised at the first attempt, whatever
`max_retries` said. `bdns-sync` configured 8 retries believing they
protected it from server trouble, and they did not. On top of that,
`max_retries=3` meant three *attempts*, and running out raised a
`tenacity.RetryError` instead of the real error.

Retrying everything is no better: a repeated `400` is still a `400`, and
retrying it only delays the news and spends request budget.

## Decision

Network errors, HTTP `429`, `500`, `502`, `503` and `504`, and the
`ERR_MANTENIMIENTO_BBDD` code with any status are retried. Those errors
are [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError]; the
rest are raised at once.

The wait is exponential with jitter (starts at `wait_time`, doubles,
capped at 60 s) and honours `Retry-After`. `max_retries` counts retries
after the first attempt. When they run out, the last error is re-raised.

## Consequences

- An unattended process rides out rough patches of minutes with no
  special configuration.
- Jitter stops several clients from retrying in lockstep.
- Code catching [`BDNSError`][bdns.fetch.exceptions.BDNSError] needs no change; code that wants to tell
  transient failures apart has the subclass.
- The list of transient codes is a measurement, not a certainty: if
  another one shows up, it is added to
  [`TRANSIENT_API_ERROR_CODES`][bdns.fetch.client.TRANSIENT_API_ERROR_CODES].
