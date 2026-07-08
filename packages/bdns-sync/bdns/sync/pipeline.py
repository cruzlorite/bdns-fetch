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
from typing import Any, Optional


def buffered_chunks(
    items: Iterable[Any],
    chunk_size: int,
    transform: Optional[Callable[[Any], Any]] = None,
) -> Iterator[list[Any]]:
    """Group `items` into lists of `chunk_size`, reading ahead on a helper
    thread.

    While the caller processes one chunk, the helper thread is already
    building the next one, so work on both sides overlaps. The queue holds
    at most two chunks: if the caller falls behind, the helper blocks
    instead of filling memory.

    The caller does its work on its own thread. That matters for SQLite
    connections, which must stay on the thread that created them.
    `transform`, if given, runs on the helper thread, one item at a time.

    If the helper raises, the exception is re-raised here. If the caller
    stops iterating early, the helper is unblocked and joined before the
    generator exits.
    """
    chunk_queue: queue.Queue = queue.Queue(maxsize=2)
    done = object()
    consumer_gone = threading.Event()

    def put(item) -> bool:
        # Re-check every second whether the consumer went away. Without
        # this, a full queue would block the helper thread forever.
        while not consumer_gone.is_set():
            try:
                chunk_queue.put(item, timeout=1)
                return True
            except queue.Full:
                continue
        return False

    def read_ahead():
        try:
            chunk = []
            for item in items:
                chunk.append(transform(item) if transform else item)
                if len(chunk) >= chunk_size:
                    if not put(chunk):
                        return  # consumer is gone, nothing left to do
                    chunk = []
            if chunk:
                put(chunk)
            put(done)
        except Exception as exc:
            put(exc)  # re-raised on the caller's thread below

    helper = threading.Thread(target=read_ahead, daemon=True)
    helper.start()
    try:
        while True:
            item = chunk_queue.get()
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
    next_start = [0.0]

    def run_one(key):
        with lock:
            now = time.monotonic()
            wait = max(0.0, next_start[0] - now)
            next_start[0] = now + wait + spacing_seconds
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
