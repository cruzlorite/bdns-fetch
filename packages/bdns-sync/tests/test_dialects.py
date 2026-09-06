"""Adapter selection. The behavior of each adapter is covered by running
the SQL tests against that engine (see tests/conftest.py); this only pins
which adapter a URL resolves to, which is pure mapping and needs no server.
"""

from sqlalchemy import create_engine

from bdns.sync.sinks.sql.dialects import (
    BigQueryAdapter,
    DialectAdapter,
    PostgresAdapter,
    get_adapter,
)


def test_sqlite_falls_back_to_the_portable_adapter():
    """An engine with no adapter of its own gets the portable defaults,
    `DELETE` for clearing staging included. Only an engine that has been
    checked against a real server earns an override.
    """
    adapter = get_adapter(create_engine("sqlite:///:memory:"))
    assert type(adapter) is DialectAdapter


def test_duckdb_falls_back_to_the_portable_adapter():
    adapter = get_adapter(create_engine("duckdb:///:memory:"))
    assert type(adapter) is DialectAdapter


def test_postgres_gets_its_own_adapter():
    adapter = get_adapter(create_engine("postgresql+psycopg2://u:p@localhost/db"))
    assert isinstance(adapter, PostgresAdapter)


def test_staging_chunk_size_is_raised_only_for_bigquery():
    assert DialectAdapter().staging_chunk_size(5000) == 5000
    assert BigQueryAdapter().staging_chunk_size(5000) == 50_000
