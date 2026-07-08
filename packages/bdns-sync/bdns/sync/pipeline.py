# SPDX-License-Identifier: GPL-3.0-or-later

"""Concurrency helpers shared by the fetch and storage code.

Nothing here knows about the BDNS API or SQL. Callers pass plain
iterables and callables, which also keeps these functions easy to test.
"""

import concurrent.futures
import itertools
import queue
import threading
import time
from collections.abc import Callable, Iterable, Iterator
from typing import Any


def chunked(items: Iterable[Any], chunk_size: int) -> Iterator[list[Any]]:
    """Group `items` into lists of at most `chunk_size`. Pure: no threads."""
    chunk = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def prefetch(iterable: Iterable[Any]) -> Iterator[Any]:
    """Yield the items of `iterable`, pulling them on a helper thread that
    reads ahead of the caller.

    While the caller processes one item, the helper is already producing
    the next. The queue holds at most two items: if the caller falls
    behind, the helper blocks instead of filling memory.

    The caller does its work on its own thread. That matters for SQLite
    connections, which must stay on the thread that created them.

    If the helper raises, the exception is re-raised here. If the caller
    stops iterating early, the helper is unblocked and joined before the
    generator exits.
    """
    item_queue: queue.Queue = queue.Queue(maxsize=2)
    done = object()
    consumer_gone = threading.Event()

    def put(item) -> bool:
        # Re-check every second whether the consumer went away. Without
        # this, a full queue would block the helper thread forever.
        while not consumer_gone.is_set():
            try:
                item_queue.put(item, timeout=1)
                return True
            except queue.Full:
                continue
        return False

    def read_ahead():
        try:
            for item in iterable:
                if not put(item):
                    return  # consumer is gone, nothing left to do
            put(done)
        except Exception as exc:
            put(exc)  # re-raised on the caller's thread below

    helper = threading.Thread(target=read_ahead, daemon=True)
    helper.start()
    try:
        while True:
            item = item_queue.get()
            if item is done:
                return
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        consumer_gone.set()
        helper.join()


def rate_limited_map(
    keys: Iterable[Any],
    fn: Callable[[Any], Any],
    spacing_seconds: float,
    max_workers: int,
) -> Iterator[tuple[Any, Any]]:
    """Run `fn(key)` on a thread pool and yield `(key, result)` as calls
    finish.

    Call starts are spaced at least `spacing_seconds` apart across all
    workers. Rate-limited servers reject bursts, not averages: a fresh
    pool firing all its workers at once gets 429s even when the average
    rate is fine. With spaced starts, `max_workers` only needs to be
    large enough to cover call latency.

    At most `2 * max_workers` calls are submitted ahead of the consumer,
    so a large key set never piles up results in memory. If `fn` raises,
    the exception propagates and stops the iteration.
    """
    lock = threading.Lock()
    next_start = 0.0

    def run_one(key):
        nonlocal next_start
        with lock:
            now = time.monotonic()
            wait = max(0.0, next_start - now)
            next_start = now + wait + spacing_seconds
        if wait:
            time.sleep(wait)
        return key, fn(key)

    keys_iter = iter(keys)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending = {
            executor.submit(run_one, key)
            for key in itertools.islice(keys_iter, max_workers * 2)
        }
        while pending:
            finished, pending = concurrent.futures.wait(
                pending, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for key in itertools.islice(keys_iter, len(finished)):
                pending.add(executor.submit(run_one, key))
            for future in finished:
                yield future.result()
