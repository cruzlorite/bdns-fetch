# 0007. Retry transient failures only

**Status:** accepted · **Date:** 2026-10-03

## Context

The API fails in two ways. Sometimes transiently: network errors, `429`,
`5xx`, or `ERR_MANTENIMIENTO_BBDD`, which it returns intermittently on
long queries ([measurement](../fetch/explanation/api-behavior.md#range-reliability)).
Sometimes permanently: a malformed parameter, a document that does not
exist.

An unattended process must ride out the former without intervention.
Retrying the latter is pointless: a repeated `400` is still a `400`, and
retrying it only delays the news and spends request budget. Whoever
configures retries also expects the number to mean retries, and the real
error to reach them when they run out, not a wrapper from the retry
library.

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
- Code that only needs to know something failed catches
  [`BDNSError`][bdns.fetch.exceptions.BDNSError]; code that wants to tell transient failures apart has the
  subclass.
- The list of transient codes is a measurement, not a certainty: if
  another one shows up, it is added to
  [`TRANSIENT_API_ERROR_CODES`][bdns.fetch.client.TRANSIENT_API_ERROR_CODES].
