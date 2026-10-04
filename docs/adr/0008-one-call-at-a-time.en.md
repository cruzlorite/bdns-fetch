# 0008. One call at a time by default

**Status:** accepted · **Date:** 2026-10-04

## Context

The IGAE's [official good practices](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) explicitly ask for no concurrent calls ("no realizar llamadas de forma concurrente, ya que los recursos son limitados y es necesario un uso racional de los mismos") and warn that abusive use can get access cut off.

Concurrent calls make downloads faster, but they are not what makes them possible. What lets years of data be downloaded without errors is splitting queries by date into week-long ranges ([measurements](../explanation/api-behavior.md#range-reliability)); concurrency only shortens the total time, mostly when thousands of small calls are needed, such as fetching each call for applications' detail.

## Decision

One call at a time by default (`max_workers=1`). Anyone who needs to go faster can raise it with `max_workers` or `--max-workers`, knowing it departs from the official recommendation. Request spacing ([decision 0003](0003-spaced-requests-no-bursts.md)) and ordered pagination ([decision 0005](0005-ordered-bounded-pagination.md)) still apply with several threads.

## Consequences

- Default use follows the recommendation of whoever runs the API, reducing the risk of access being cut off.
- Large downloads take longer. It shows most in steps making one call per record: the detail of a month of calls for applications (about 6,000) goes from about 11 minutes with eight threads to between 23 minutes and just over 3 hours, depending on server load.
- Whoever raises `max_workers` takes responsibility for doing so.
