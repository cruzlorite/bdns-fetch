"""Shared fixtures.

The engine under test is chosen by `BDNS_SYNC_TEST_URL`, defaulting to
in-memory SQLite so the suite stays a plain `pytest` with no services
running. Point it at a real server to run the same tests against another
engine:

    BDNS_SYNC_TEST_URL=postgresql+psycopg2://bdns:bdns@localhost:5432/bdns pytest

Only the tests that touch SQL directly use these fixtures. The timeline
scenario tests exercise syncer wiring, which is dialect-independent, and
stay on SQLite so the suite runs fast without a server.
"""

import os
import uuid

import pytest
from sqlalchemy import MetaData, create_engine

DEFAULT_TEST_URL = "sqlite:///:memory:"


def test_url() -> str:
    return os.environ.get("BDNS_SYNC_TEST_URL", DEFAULT_TEST_URL)


@pytest.fixture
def engine():
    """Engine for the target under test, disposed at the end of the test."""
    eng = create_engine(test_url())
    yield eng
    eng.dispose()


@pytest.fixture
def table_name() -> str:
    """A table name unique to this test.

    In-memory SQLite gets a fresh database per engine, but a real server
    is shared across the whole run, so tables would collide and leak state
    between tests without this.
    """
    return f"things_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def metadata():
    return MetaData()
