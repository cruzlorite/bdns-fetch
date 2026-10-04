"""Run the dataset's SQL as `dataset/build.sql` does, against small bdns-sync databases.

The dataset is plain DuckDB SQL; these fixtures only run its files, in the
order build.sql reads them, so the tests exercise exactly what the DuckDB
command line runs.
"""

import json
import pathlib
from datetime import UTC, datetime

import duckdb
import pytest
from sqlalchemy import MetaData, create_engine, insert

from bdns.sync.sinks.sql.schema import build_sync_table

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD = ROOT / "dataset" / "build.sql"
T1, T2, T3, T4 = (datetime(2026, month, 1, tzinfo=UTC) for month in (1, 3, 6, 9))


def build_steps() -> list[pathlib.Path]:
    """Return the files build.sql reads, in its order."""
    lines = BUILD.read_text(encoding="utf-8").splitlines()
    return [ROOT / line.split(maxsplit=1)[1] for line in lines if line.startswith(".read ")]


def run_steps(con, names=None):
    """Run build.sql's steps, or only those whose file name is in `names`."""
    for step in build_steps():
        if names is None or step.name in names:
            con.execute(step.read_text(encoding="utf-8"))


def version(key, valid_from, valid_to, current, reason, payload):
    return {
        "_natural_key": json.dumps([key]),
        "_row_hash": f"{key}-{valid_from:%m}",
        "_valid_from": valid_from,
        "_valid_to": valid_to,
        "_is_current": current,
        "_synced_at": valid_from,
        "_reg_date": None,
        "payload": payload,
        "_created_run_id": None,
        "_closed_run_id": None,
        "_closed_reason": reason,
    }


def award(key, beneficiario, importe, **extra):
    """A made-up award payload, in the shape the API returns."""
    return {
        "id": key,
        "codConcesion": f"SB{key}",
        "fechaConcesion": "2026-02-10",
        "beneficiario": beneficiario,
        "importe": importe,
        "instrumento": "SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN ",
        "numeroConvocatoria": "900001",
        "convocatoria": "Ayudas á la cultura 2026",
        "nivel1": "AUTONOMICA",
        "nivel2": "COMUNIDAD DE EJEMPLO",
        "nivel3": "CONSEJERIA DE EJEMPLO",
        "idPersona": 1000 + key,
        "urlBR": f"https://boletin.example/{key}.pdf",
        **extra,
    }


def state_aid(key, beneficiario, importe):
    """A made-up state aid payload, in the shape the API returns."""
    return {
        "idConcesion": str(key),
        "codConcesion": f"PR{key}",
        "fechaConcesion": "2026-09-25",
        "beneficiario": beneficiario,
        "importe": str(importe),
        "ayudaEquivalente": str(importe / 2),
        "instrumento": "PRÉSTAMO",
        "region": "ES615 - Huelva",
        "idPersona": str(2000 + key),
        "ayudaEstado": "SA.000001",
        "urlAyudaEstado": "https://competition-cases.ec.europa.eu/cases/SA.000001",
    }


def de_minimis(key, beneficiario, equivalente):
    """A made-up de minimis payload, in the shape the API returns."""
    return {
        "idConcesion": str(key),
        "codigoConcesion": f"SB{key}",
        "fechaConcesion": "2026-09-29",
        "beneficiario": beneficiario,
        "ayudaEquivalente": str(equivalente),
        "sectorActividad": "47 - Comercio al por menor",
        "idPersona": str(3000 + key),
    }


def make_sync_db(path, concesiones, ayudas, minimis):
    """Write a bdns-sync database (DuckDB) with bdns-sync's real table schema."""
    engine = create_engine(f"duckdb:///{path}")
    metadata = MetaData()
    tables = {
        name: build_sync_table(name, metadata)
        for name in ("concesiones_busqueda", "ayudasestado_busqueda", "minimis_busqueda")
    }
    metadata.create_all(engine)
    with engine.begin() as conn:
        for name, rows in [
            ("concesiones_busqueda", concesiones),
            ("ayudasestado_busqueda", ayudas),
            ("minimis_busqueda", minimis),
        ]:
            if rows:
                conn.execute(insert(tables[name]), rows)
    engine.dispose()
    return path


@pytest.fixture
def sync_db(tmp_path):
    """A small bdns-sync database covering each kind of beneficiary and version."""
    return make_sync_db(
        tmp_path / "sync.duckdb",
        concesiones=[
            # Corrected: the current version is the last known one.
            version(1, T1, T2, False, "superseded", award(1, "B12345678 EMPRESA SL", 1000)),
            version(1, T2, None, True, None, award(1, "B12345678 EMPRESA SL", 1200)),
            # Withdrawn: its last version was closed as removed.
            version(2, T1, T3, False, "removed", award(2, "***1234** NOMBRE APELLIDO", 500)),
            # Versions written before closing reasons existed.
            version(3, T1, T2, False, None, award(3, "123456789012 FOREIGN LTD", 70)),
            version(3, T2, T4, False, None, award(3, "123456789012 FOREIGN LTD", 80)),
        ],
        ayudas=[
            version(11, T1, None, True, None, state_aid(11, "B12345678 - EMPRESA SL", 1000)),
            version(12, T1, None, True, None, state_aid(12, "***1234** NOMBRE APELLIDO", 300)),
        ],
        minimis=[
            version(21, T1, None, True, None, de_minimis(21, "G12345678 ASOCIACION", 900)),
            version(
                22, T1, None, True, None, de_minimis(22, "E12345678 APELLIDO Y APELLIDO CB", 400)
            ),
        ],
    )


@pytest.fixture
def output(tmp_path):
    """The folder the build writes the Parquet files to."""
    folder = tmp_path / "output"
    folder.mkdir()
    return folder


@pytest.fixture
def built(sync_db, output):
    """A DuckDB connection after running the whole build against `sync_db`."""
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    con.execute(f"SET VARIABLE output_dir = '{output}'")
    run_steps(con)
    yield con
    con.close()


@pytest.fixture
def macros():
    """A DuckDB connection with only the macros defined."""
    con = duckdb.connect()
    run_steps(con, {"01_beneficiarios.sql", "02_privacy.sql"})
    yield con
    con.close()
