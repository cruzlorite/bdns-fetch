"""Adapter selection. The behavior of each adapter is covered by running
the SQL tests against that engine (see tests/sync/conftest.py); this only pins
which adapter a URL resolves to, which is pure mapping and needs no server.
"""

import sys
import types
import warnings
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.exc import NoSuchModuleError

from bdns.sync.sinks.sql import schema
from bdns.sync.sinks.sql.dialects import (
    BigQueryAdapter,
    DialectAdapter,
    PostgresAdapter,
    get_adapter,
    staging_json_rows,
)
from bdns.sync.sinks.sql.schema import build_staging_table


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


# --- BigQuery load-job payload -------------------------------------------
#
# `insert_rows` bypasses SQLAlchemy entirely and hand-builds what lands in
# the table, against the real production target. The row building is
# `staging_json_rows`, tested directly here; the few lines around it are
# covered by the fake-client test at the end.


def test_staging_json_rows_serializes_the_payload_as_json_text():
    metadata = MetaData()
    staging = build_staging_table("things", metadata)
    [row] = staging_json_rows(
        staging, [{"_natural_key": "[1]", "_row_hash": "a" * 64, "payload": {"id": 1, "v": "x"}}]
    )
    assert row["payload"] == '{"id": 1, "v": "x"}'
    assert row["_natural_key"] == "[1]"
    assert row["_row_hash"] == "a" * 64


def test_staging_json_rows_keeps_non_ascii_unescaped():
    """The payload column serializes with ensure_ascii=False. Escaping
    would still be valid JSON but would change every hash of every
    Spanish record against the ordinary INSERT path.
    """
    metadata = MetaData()
    staging = build_staging_table("things", metadata)
    [row] = staging_json_rows(
        staging, [{"_natural_key": "[1]", "_row_hash": "b" * 64, "payload": {"v": "ASOCIACIÓN"}}]
    )
    assert "ASOCIACIÓN" in row["payload"]


def test_staging_json_rows_sends_reg_date_as_an_iso_string():
    metadata = MetaData()
    staging = build_staging_table("things", metadata)
    [row] = staging_json_rows(
        staging,
        [
            {
                "_natural_key": "[1]",
                "_row_hash": "c" * 64,
                "payload": {},
                "_reg_date": date(2026, 9, 1),
            }
        ],
    )
    assert row["_reg_date"] == "2026-09-01"


def test_staging_json_rows_omits_reg_date_for_entities_without_one():
    """Full-replace catalogs stage no `_reg_date`. The key must be absent,
    not present as null, and never carry a stale value from another row.
    """
    metadata = MetaData()
    staging = build_staging_table("things", metadata)
    rows = staging_json_rows(
        staging,
        [
            {
                "_natural_key": "[1]",
                "_row_hash": "d" * 64,
                "payload": {},
                "_reg_date": date(2026, 9, 1),
            },
            {"_natural_key": "[2]", "_row_hash": "e" * 64, "payload": {}},
        ],
    )
    assert rows[0]["_reg_date"] == "2026-09-01"
    assert "_reg_date" not in rows[1]
    assert set(rows[1]) == {"_natural_key", "_row_hash", "payload"}


def test_bigquery_insert_rows_blocks_on_the_load_job(monkeypatch):
    """The `.result()` call is load-bearing, not incidental: BigQuery caps
    table update operations at a low fixed rate, and submitting load jobs
    without waiting trips a hard 429. Dropping it would look harmless and
    only fail against the real service, under load.
    """
    calls = {}

    class FakeLoadJob:
        def result(self):
            calls["waited"] = True

    class FakeClient:
        project = "proj"

        def load_table_from_json(self, json_rows, table_ref):
            calls["rows"] = json_rows
            calls["table_ref"] = table_ref
            return FakeLoadJob()

    class FakeTableRef:
        def __init__(self, dataset):
            self.dataset = dataset

        def table(self, name):
            return f"{self.dataset}.{name}"

    fake_bigquery = types.ModuleType("google.cloud.bigquery")
    fake_bigquery.DatasetReference = lambda project, dataset: FakeTableRef(f"{project}.{dataset}")
    fake_cloud = types.ModuleType("google.cloud")
    fake_cloud.bigquery = fake_bigquery
    fake_google = types.ModuleType("google")
    fake_google.cloud = fake_cloud
    for name, module in [
        ("google", fake_google),
        ("google.cloud", fake_cloud),
        ("google.cloud.bigquery", fake_bigquery),
    ]:
        monkeypatch.setitem(sys.modules, name, module)

    metadata = MetaData()
    staging = build_staging_table("things", metadata)

    class FakeConn:
        connection = SimpleNamespace(driver_connection=SimpleNamespace(_client=FakeClient()))
        engine = SimpleNamespace(url=SimpleNamespace(database="dataset"))

    BigQueryAdapter().insert_rows(
        FakeConn(), staging, [{"_natural_key": "[1]", "_row_hash": "f" * 64, "payload": {"id": 1}}]
    )

    assert calls["waited"] is True
    assert calls["table_ref"] == "proj.dataset._staging_things"
    assert calls["rows"] == [{"_natural_key": "[1]", "_row_hash": "f" * 64, "payload": '{"id": 1}'}]


def test_tables_cluster_on_bigquery_when_its_dialect_is_installed():
    pytest.importorskip("sqlalchemy_bigquery")
    schema._bigquery_dialect_installed.cache_clear()
    table = schema.build_sync_table("sectores", MetaData())
    assert table.kwargs["bigquery_clustering_fields"] == ["_natural_key", "_is_current"]


def test_tables_build_without_warnings_when_bigquery_is_not_installed(monkeypatch):
    # Without the bigquery extra, a dialect-namespaced option SQLAlchemy
    # cannot validate warns on every table built, i.e. on every run.
    def missing(name):
        raise NoSuchModuleError(name)

    monkeypatch.setattr(schema.registry, "load", missing)
    schema._bigquery_dialect_installed.cache_clear()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            sync_table = schema.build_sync_table("sectores", MetaData())
            staging = schema.build_staging_table("sectores", MetaData())
    finally:
        schema._bigquery_dialect_installed.cache_clear()
    assert "bigquery_clustering_fields" not in sync_table.kwargs
    assert "bigquery_clustering_fields" not in staging.kwargs
