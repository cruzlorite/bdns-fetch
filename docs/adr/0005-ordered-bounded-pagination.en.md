# 0005. Concurrent pagination, in order, with bounded memory

**Status:** accepted · **Date:** 2026-10-03

## Context

A large search has thousands of pages. Requesting them one after another
wastes the request budget waiting on latency. 1.3 requested them in
parallel, but in a way that caused three problems:

- it delivered pages in the order they **finished**, so the result came
  out shuffled;
- it sent **every** request at once, so with a slow consumer the whole
  result piled up in memory;
- a consumer that stopped iterating still downloaded every page.

## Decision

A sliding window of `2 × max_workers` requests in flight. Pages are
delivered in page order: if page `k` arrives before `k-1`, it waits.
Each delivered page frees a slot for the next one. Closing the iterator
cancels the pending requests.

## Consequences

- The result is deterministic for a given data set.
- Memory is bounded by the window, not by the size of the result.
- A slow consumer slows the download (backpressure) instead of piling up.
- A slow page holds back delivery of the following ones until it
  arrives; thanks to the window, the threads keep working meanwhile.
