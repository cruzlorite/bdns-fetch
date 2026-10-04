# 0010. Concurrent pagination, in order, with bounded memory

**Status:** accepted · **Date:** 2026-10-03

## Context

A large search has thousands of pages. Requesting them one after another
wastes the request budget waiting on latency, so they are requested in
parallel. The naive way (send every request and deliver each page as it
arrives) has three problems:

- the result comes out in the order the requests **finish**, that is,
  shuffled;
- with a slow consumer, the whole result piles up in memory;
- a consumer that stops iterating still downloads every page.

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
