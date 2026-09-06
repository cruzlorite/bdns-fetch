"""The concurrency helpers in `bdns.sync.pipeline`.

These are worth testing directly rather than through a sync, because
their failure mode is silent. If `prefetch` dropped an item, nothing
would raise: the batch would simply be short, the run would report the
shorter count as `rows_fetched`, and on an entity with window-scoped
deletion detection the missing rows would be closed as real withdrawals.
A `success` event over quietly corrupted data is the worst outcome this
codebase can produce, so the properties that prevent it are pinned here.
"""

import threading
import time

import pytest

from bdns.sync.pipeline import chunked, prefetch, rate_limited_map

# --- chunked ---------------------------------------------------------------


def test_chunked_groups_into_full_chunks_and_a_short_last_one():
    assert list(chunked(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]


def test_chunked_exact_multiple_has_no_empty_trailing_chunk():
    assert list(chunked(range(6), 3)) == [[0, 1, 2], [3, 4, 5]]


def test_chunked_empty_input_yields_nothing():
    assert list(chunked([], 3)) == []


def test_chunked_is_lazy():
    """Staging reads millions of rows through this; it must not materialize
    the whole source before yielding the first chunk.
    """
    consumed = []

    def source():
        for i in range(100):
            consumed.append(i)
            yield i

    first = next(chunked(source(), 5))
    assert first == [0, 1, 2, 3, 4]
    assert len(consumed) < 100


# --- prefetch --------------------------------------------------------------


def test_prefetch_yields_every_item_in_order():
    assert list(prefetch(range(500))) == list(range(500))


def test_prefetch_of_an_empty_iterable_yields_nothing():
    assert list(prefetch([])) == []


def test_prefetch_runs_the_producer_on_another_thread():
    """The point of the helper thread: the consumer keeps its own thread,
    because a SQLite connection may not leave the thread that created it.
    """
    producer_threads = []

    def source():
        for i in range(5):
            producer_threads.append(threading.get_ident())
            yield i

    list(prefetch(source()))
    assert producer_threads
    assert threading.get_ident() not in producer_threads


def test_prefetch_reraises_a_producer_exception_on_the_consumer_thread():
    def exploding():
        yield 1
        raise ValueError("producer exploded")

    seen = []
    with pytest.raises(ValueError, match="producer exploded"):
        for item in prefetch(exploding()):
            seen.append(item)
    assert seen == [1]  # everything before the failure still came through


def test_prefetch_applies_backpressure_and_stops_when_the_consumer_leaves():
    """The queue holds at most two items, so a consumer that stops early
    must not leave the producer racing ahead through the whole source.
    The test finishing at all is half the assertion: the generator's
    cleanup joins the helper thread, so a helper stuck on a full queue
    would hang here.
    """
    produced = 0

    def endless():
        nonlocal produced
        while True:
            produced += 1
            yield produced

    gen = prefetch(endless())
    assert [next(gen), next(gen)] == [1, 2]
    gen.close()

    # Bounded queue (2) + one item in flight + the two consumed, with a
    # little slack for the helper being mid-put when close() landed.
    assert produced <= 10


# --- rate_limited_map ------------------------------------------------------


def test_rate_limited_map_returns_every_key_exactly_once():
    keys = list(range(50))
    pairs = list(rate_limited_map(keys, lambda k: k * 2, 0.0, 4))
    assert sorted(pairs) == [(k, k * 2) for k in keys]


def test_rate_limited_map_spaces_call_starts():
    """Request starts are spaced because the BDNS server rejects bursts
    even when the average rate is legal. Asserted as a floor on total
    elapsed time: without spacing this finishes in about zero.
    """
    keys = list(range(10))
    spacing = 0.02
    started = time.monotonic()
    list(rate_limited_map(keys, lambda k: k, spacing, max_workers=8))
    elapsed = time.monotonic() - started
    assert elapsed >= (len(keys) - 1) * spacing


def test_rate_limited_map_propagates_an_exception_from_the_worker():
    def boom(key):
        if key == 3:
            raise RuntimeError("detail fetch failed")
        return key

    with pytest.raises(RuntimeError, match="detail fetch failed"):
        list(rate_limited_map(range(20), boom, 0.0, 4))


def test_rate_limited_map_does_not_submit_the_whole_key_set_upfront():
    """convocatorias hands this hundreds of thousands of codes. Submitting
    them all would pile every result up in memory before the consumer sees
    the first one.
    """
    calls = []
    gen = rate_limited_map(range(500), lambda k: calls.append(k) or k, 0.0, 4)
    try:
        next(gen)
        assert len(calls) < 100
    finally:
        gen.close()
