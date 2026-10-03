# SPDX-License-Identifier: GPL-3.0-or-later

"""Concurrency helpers shared by the fetch and storage code.

Nothing here knows about the BDNS API or SQL. Callers pass plain
iterables and callables, which also keeps these functions easy to test.
"""

import concurrent.futures
import itertools
import queue
import threading
from collections.abc import Callable, Iterable, Iterator
from typing import Any

__all__ = ["bounded_map", "chunked", "prefetch"]


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
    """Yield the items of `iterable`, read ahead on a helper thread.

    While the caller processes one item, the helper is already producing
    the next. The queue holds at most two items, so a slow caller blocks
    the helper instead of growing memory.

    The caller keeps its own thread, which SQLite requires: a connection
    may only be used on the thread that opened it.

    Args:
        iterable: Source of items, consumed on the helper thread.

    Yields:
        The items of `iterable`, in order.

    Raises:
        Exception: Whatever `iterable` raised, re-raised on the caller's
            thread. The helper is unblocked and joined before this
            generator exits, including when the caller stops iterating
            early.
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


def bounded_map(
    keys: Iterable[Any],
    fn: Callable[[Any], Any],
    max_workers: int,
) -> Iterator[tuple[Any, Any]]:
    """Run `fn(key)` on a thread pool, yielding `(key, result)` as calls finish.

    At most `2 * max_workers` calls are submitted ahead of the consumer,
    so a large key set never piles results up in memory. Pacing requests
    is not this function's job: the BDNS client already spaces every
    request it sends, across threads.

    Args:
        keys: Work items. Pulled lazily.
        fn: Called once per key, on a worker thread.
        max_workers: Pool size.

    Yields:
        `(key, result)` pairs in completion order, not key order.

    Raises:
        Exception: Whatever `fn` raised, which stops the iteration.
    """
    keys_iter = iter(keys)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending = {
            executor.submit(lambda key=key: (key, fn(key)))
            for key in itertools.islice(keys_iter, max_workers * 2)
        }
        while pending:
            finished, pending = concurrent.futures.wait(
                pending, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for key in itertools.islice(keys_iter, len(finished)):
                pending.add(executor.submit(lambda key=key: (key, fn(key))))
            for future in finished:
                yield future.result()
