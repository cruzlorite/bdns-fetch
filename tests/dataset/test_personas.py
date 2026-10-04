"""Natural-person aggregates (dataset/sql/30_personas.sql): statistical
disclosure control, case by case. Everyone here is made up."""

import duckdb
import pytest

from tests.dataset.conftest import ROOT, T1, award, make_sync_db, run_steps, version


def people(call, count, start, importe=100, year="2026"):
    """Awards from `count` different natural persons in one call."""
    return [
        award(
            start + n,
            f"***{start + n:04d}** NOMBRE",
            importe,
            numeroConvocatoria=call,
            convocatoria=f"Convocatoria {call}",
            fechaConcesion=f"{year}-05-10",
            idPersona=start + n,
        )
        for n in range(count)
    ]


@pytest.fixture
def con(tmp_path):
    awards = [
        *people("A", 12, 100),
        # The first person in A gets a second award: still one beneficiary.
        award(
            999,
            "***0100** NOMBRE",
            100,
            numeroConvocatoria="A",
            convocatoria="Convocatoria A",
            fechaConcesion="2026-06-01",
            idPersona=100,
        ),
        # A company in A: published record by record, never counted here.
        award(
            998, "B12345678 EMPRESA SL", 5000, numeroConvocatoria="A", convocatoria="Convocatoria A"
        ),
        *people("B", 6, 200),
        *people("C", 6, 300),
        # 2025: one cell, suppressed because one person dominates.
        *people("D", 14, 400, year="2025"),
        *people("D", 1, 450, importe=10_000, year="2025"),
        # A title shaped like a tax ID.
        *[dict(a, convocatoria="Ayudas a 12345678Z") for a in people("E", 10, 500)],
    ]
    sync_db = make_sync_db(
        tmp_path / "sync.duckdb",
        [version(a["id"], T1, None, True, None, a) for a in awards],
        [],
        [],
    )
    connection = duckdb.connect()
    connection.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    run_steps(
        connection,
        {n for n in (p.name for p in (ROOT / "dataset" / "sql").iterdir()) if n != "95_export.sql"},
    )
    yield connection
    connection.close()


def rows(con):
    return {
        (anio, convocatoria_id, resto): (concesiones, beneficiarios, float(importe))
        for anio, convocatoria_id, resto, concesiones, beneficiarios, importe in con.execute(
            "SELECT anio, numero_convocatoria, resto, concesiones, beneficiarios, importe_total "
            "FROM publicar.concesiones_personas"
        ).fetchall()
    }


def test_a_large_cell_is_published_counting_each_person_once(con):
    # 13 awards to 12 people; the company stays out.
    assert rows(con)[(2026, "A", False)] == (13, 12, 1300.0)


def test_small_cells_are_suppressed_and_gathered_into_a_rest_row(con):
    published = rows(con)
    assert (2026, "B", False) not in published and (2026, "C", False) not in published
    # B and C together: 12 people, two cells, so the rest row can be published.
    assert published[(2026, None, True)] == (12, 12, 1200.0)


def test_a_dominated_cell_is_suppressed_and_a_lone_rest_is_not_published(con):
    published = rows(con)
    assert (2025, "D", False) not in published
    # D is 2025's only suppressed cell: its rest would be D itself.
    assert (2025, None, True) not in published


def test_a_title_shaped_like_a_tax_id_is_blanked(con):
    (convocatoria,) = con.execute(
        "SELECT convocatoria FROM publicar.concesiones_personas WHERE numero_convocatoria = 'E'"
    ).fetchone()
    assert convocatoria is None


def test_the_checks_stop_a_cell_below_the_minimum(con):
    con.execute(
        "INSERT INTO publicar.concesiones_personas (anio, numero_convocatoria, beneficiarios, resto) "
        "VALUES (2026, 'Z', 3, false)"
    )
    with pytest.raises(duckdb.InvalidInputException, match="below 10 beneficiaries"):
        con.execute((ROOT / "dataset" / "sql" / "90_checks.sql").read_text(encoding="utf-8"))


def test_the_checks_stop_an_identifying_column(con):
    con.execute("ALTER TABLE publicar.concesiones_personas ADD COLUMN id_persona BIGINT")
    with pytest.raises(duckdb.InvalidInputException, match="identifying columns: id_persona"):
        con.execute((ROOT / "dataset" / "sql" / "90_checks.sql").read_text(encoding="utf-8"))
