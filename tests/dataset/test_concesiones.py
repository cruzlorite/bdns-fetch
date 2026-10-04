"""Awards (dataset/sql/10_concesiones.sql), read straight from a bdns-sync database."""

import os
import shutil
import subprocess

import pytest

from tests.dataset.conftest import ROOT


def test_each_award_keeps_its_last_known_version(built):
    rows = built.execute(
        "SELECT id, importe, tipo_beneficiario, retirada FROM concesiones ORDER BY id"
    ).fetchall()
    assert [(i, float(m), k, r) for i, m, k, r in rows] == [
        (1, 1200.0, "legal_person", False),
        # Withdrawn by the API: kept with its last content.
        (2, 500.0, "natural_person", True),
        # Last version closed before closing reasons existed: withdrawn too.
        (3, 80.0, "unknown", True),
    ]


def test_columns_are_typed_and_text_is_untouched(built):
    fecha, anio, instrumento, convocatoria = built.execute(
        "SELECT fecha_concesion, anio, instrumento, convocatoria FROM concesiones WHERE id = 1"
    ).fetchone()
    assert (str(fecha), anio) == ("2026-02-10", 2026)
    assert instrumento == "SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN"
    assert convocatoria == "Ayudas á la cultura 2026"


@pytest.mark.skipif(
    shutil.which("duckdb") is None, reason="the DuckDB command line is not installed"
)
def test_the_duckdb_command_line_runs_the_build(sync_db, tmp_path):
    result = subprocess.run(
        [
            "duckdb",
            str(tmp_path / "dataset.duckdb"),
            "-cmd",
            f"ATTACH '{sync_db}' AS sync (READ_ONLY)",
            "-f",
            "dataset/build.sql",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr
