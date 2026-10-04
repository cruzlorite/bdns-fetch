# 0019. One call at a time by default

**Status:** accepted · **Date:** 2026-10-04

## Context

The IGAE's [official good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) explicitly ask for no concurrent calls ("no realizar llamadas de forma concurrente, ya que los recursos son limitados y es necesario un uso racional de los mismos") and warn that abusive use can get access cut off.

Concurrent calls make downloads faster, but they are not what makes them possible. What lets years of data be downloaded without errors is splitting queries by date into week-long ranges ([measurements](../fetch/explanation/api-behavior.md#range-reliability)); concurrency only shortens the total time, mostly on paginated searches, where each page takes a couple of seconds to arrive.

## Decision

One call at a time by default (`max_workers=1`). Anyone who needs to go faster can raise it with `max_workers` or `--max-workers`, knowing it departs from the official recommendation. Request spacing ([decision 0008](0008-spaced-requests-no-bursts.md)) and ordered pagination ([decision 0010](0010-ordered-bounded-pagination.md)) still apply with several threads.

## Consequences

- Default use follows the recommendation of whoever runs the API, reducing the risk of access being cut off.
- Large paginated searches take longer: a week of awards (236,113 rows) downloads in about 60 seconds instead of 15 with five threads ([measurements](../fetch/explanation/api-behavior.md#concurrency)). Small calls, such as a call for applications' detail, are barely affected while the server answers fast, since the rate limit already caps them.
- Within the recommendation there is no room to go faster from the client: each page takes as long as the server needs to prepare and send it.
- Whoever raises `max_workers` takes responsibility for doing so.
