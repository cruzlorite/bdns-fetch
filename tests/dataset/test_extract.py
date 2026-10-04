"""Extraction of each key's last known version from a bdns-sync table."""

import json
from datetime import UTC, date, datetime

import duckdb
import pytest
from sqlalchemy import MetaData, create_engine, insert
from sqlalchemy.dialects import postgresql

from bdns.dataset.extract import RAW_PREFIX, extract_table, latest_versions
from bdns.sync.sinks.sql.schema import build_sync_table

T1, T2, T3, T4 = (datetime(2026, month, 1, tzinfo=UTC) for month in (1, 3, 6, 9))


def version(key, valid_from, valid_to, current, reason, importe, reg_date=None):
    return {
        "_natural_key": json.dumps([key]),
        "_row_hash": f"{key}-{importe}",
        "_valid_from": valid_from,
        "_valid_to": valid_to,
        "_is_current": current,
        "_synced_at": valid_from,
        "_reg_date": reg_date,
        "payload": {"id": key, "importe": importe, "convocatoria": "Ayudas á la cultura"},
        "_created_run_id": None,
        "_closed_run_id": None,
        "_closed_reason": reason,
    }


@pytest.fixture
def source(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'sync.db'}")
    metadata = MetaData()
    table = build_sync_table("concesiones_busqueda", metadata)
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            insert(table),
            [
                # Corrected: the current version is the last known one.
                version(1, T1, T2, False, "superseded", 1000, date(2026, 1, 1)),
                version(1, T2, None, True, None, 1200, date(2026, 1, 1)),
                # Withdrawn: its last version was closed as removed.
                version(2, T1, T3, False, "removed", 500),
                # Versions written before closing reasons existed.
                version(3, T1, T2, False, None, 70),
                version(3, T2, T4, False, None, 80),
            ],
        )
    yield engine
    engine.dispose()


@pytest.fixture
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


def test_each_key_keeps_its_newest_version(source, con):
    assert extract_table(source, con, "concesiones_busqueda") == 3
    rows = con.execute(
        f"""SELECT payload->>'id', payload->>'importe', is_current, closed_reason, reg_date
            FROM {RAW_PREFIX}concesiones_busqueda ORDER BY 1"""
    ).fetchall()
    assert rows == [
        ("1", "1200", True, None, date(2026, 1, 1)),
        ("2", "500", False, "removed", None),
        ("3", "80", False, None, None),
    ]


def test_payload_arrives_as_json_untouched(source, con):
    extract_table(source, con, "concesiones_busqueda")
    (titulo,) = con.execute(
        f"SELECT payload->>'convocatoria' FROM {RAW_PREFIX}concesiones_busqueda LIMIT 1"
    ).fetchone()
    assert titulo == "Ayudas á la cultura"


def test_small_batches_give_the_same_result(source, con):
    assert extract_table(source, con, "concesiones_busqueda", batch_size=1) == 3
    assert con.execute(f"SELECT count(*) FROM {RAW_PREFIX}concesiones_busqueda").fetchone() == (3,)


def test_extracting_again_replaces_the_copy(source, con):
    extract_table(source, con, "concesiones_busqueda")
    extract_table(source, con, "concesiones_busqueda")
    assert con.execute(f"SELECT count(*) FROM {RAW_PREFIX}concesiones_busqueda").fetchone() == (3,)


def test_the_query_is_portable_sql():
    table = build_sync_table("concesiones_busqueda", MetaData())
    sql = str(latest_versions(table).compile(dialect=postgresql.dialect()))
    assert "row_number() OVER (PARTITION BY" in sql
