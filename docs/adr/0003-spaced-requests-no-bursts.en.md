# 0003. Spaced requests, no bursts

**Status:** accepted · **Date:** 2026-10-03

## Context

The official good practices set 10 requests per second per IP. A classic
token bucket starts full: it allows a burst of as many simultaneous
requests as its capacity, then the average.

Measured against the live service, the server answers `429` to bursts
even when the average complies: 10 threads that only respected the
average died within seconds. With spaced starts it accepts a sustained
9.8 requests per second ([measurement](../explanation/api-behavior.md#rate-limit)).
If the client does not space requests, every threaded consumer has to do
it on its own.

## Decision

The [`RateLimiter`][bdns.fetch.utils.RateLimiter] spaces requests by
default (`burst=1`). The default limiter is one per process, shared by
every client and thread, at 9.5 requests per second: one every ~105 ms,
with a margin under the limit. Another can be passed to the constructor,
and the CLI sets it with `--rate-limit`.

## Consequences

- Concurrent pagination does not trigger `429` when it starts.
- Consumers need no spacing of their own.
- The limit is per process; the API's is per IP. Several processes on one
  IP must split it with `rate_limiter` or `--rate-limit`. A cross-process
  limiter (file, Redis) is out of scope.
