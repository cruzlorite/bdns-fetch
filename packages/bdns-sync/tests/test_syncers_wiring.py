"""Cheap smoke test across every registered sync function: catches typos in
endpoint names, broken imports, or a sync function not actually being
callable, without needing one dedicated test per one-liner wrapper.
"""

from bdns.sync.syncers import FULL_SYNCERS, SEARCH_SYNCERS


def test_full_syncers_cover_every_expected_table():
    assert len(FULL_SYNCERS) == 17
    for name, fn in FULL_SYNCERS.items():
        assert isinstance(name, str) and name
        assert callable(fn)


def test_search_syncers_cover_every_expected_table():
    assert len(SEARCH_SYNCERS) == 6
    assert "convocatorias" in SEARCH_SYNCERS
    for name, fn in SEARCH_SYNCERS.items():
        assert isinstance(name, str) and name
        assert callable(fn)


def test_no_endpoint_name_collisions_across_full_and_search():
    assert set(FULL_SYNCERS) & set(SEARCH_SYNCERS) == set()
