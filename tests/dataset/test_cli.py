"""The build as it is meant to run: dataset/build.sql through the DuckDB command line."""

import os
import re
import shutil
import subprocess

import pytest

from tests.dataset.conftest import ROOT, T1, award, make_sync_db, version

pytestmark = pytest.mark.skipif(
    shutil.which("duckdb") is None, reason="the DuckDB command line is not installed"
)


def run_build(sync_db, output, tmp_path):
    return subprocess.run(
        [
            "duckdb",
            str(tmp_path / "dataset.duckdb"),
            "-cmd",
            f"ATTACH '{sync_db}' AS sync (READ_ONLY); SET VARIABLE output_dir = '{output}'",
            "-f",
            "dataset/build.sql",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )


def test_the_build_writes_one_parquet_file_per_published_table(sync_db, output, tmp_path):
    result = run_build(sync_db, output, tmp_path)
    assert result.returncode == 0, result.stderr
    export = (ROOT / "dataset" / "sql" / "95_export.sql").read_text(encoding="utf-8")
    expected = sorted(f"{table}.parquet" for table in re.findall(r"COPY publish\.(\w+)", export))
    assert sorted(path.name for path in output.iterdir()) == expected
    # Results are not printed; only errors would be.
    assert result.stdout == ""


def test_a_failed_check_stops_the_build_before_anything_is_written(output, tmp_path):
    leaky = award(1, "B12345678 EMPRESA SL", 100, convocatoria="Ayuda nominativa a 12345678Z")
    sync_db = make_sync_db(
        tmp_path / "sync.duckdb", [version(1, T1, None, True, None, leaky)], [], []
    )
    result = run_build(sync_db, output, tmp_path)
    assert result.returncode != 0
    assert "personal tax ID" in result.stderr
    assert list(output.iterdir()) == []
