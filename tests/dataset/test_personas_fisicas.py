"""The per-call summaries of awards to natural persons (dataset/sql/05_summaries.sql,
with 21, 23 and 25_*_personas_fisicas.sql): statistical disclosure control, case by
case. Everyone here is made up."""

from datetime import date, timedelta

import duckdb
import pytest

from tests.dataset.conftest import (
    ROOT,
    T1,
    award,
    de_minimis,
    make_sync_db,
    run_steps,
    state_aid,
    version,
)

CHECKS = ROOT / "dataset" / "sql" / "90_checks.sql"


def people(call, count, start, importe=100, day=date(2026, 5, 10), **extra):
    """Awards from `count` different natural persons in one call.

    `importe` and `day` may be functions of the person's position, to spread
    amounts and dates.
    """
    return [
        award(
            start + n,
            f"***{start + n:04d}** NOMBRE",
            importe(n) if callable(importe) else importe,
            numeroConvocatoria=call,
            convocatoria=f"Convocatoria {call}",
            fechaConcesion=str(day(n) if callable(day) else day),
            idPersona=start + n,
            **extra,
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
        # Two calls too small to publish, in 2026.
        *people("B", 6, 200),
        *people("C", 6, 300),
        # 2025: a large call, suppressed because one person holds most of it.
        *people("D", 14, 400, day=date(2025, 5, 10)),
        *people("D", 1, 450, importe=10_000, day=date(2025, 5, 10)),
        # A title shaped like a tax ID.
        *[dict(a, convocatoria="Ayudas a 12345678Z") for a in people("E", 10, 500)],
        # Enough people for the tails: 100 to 2,500 euros, one day apart.
        *people(
            "F",
            25,
            600,
            importe=lambda n: 100 * (n + 1),
            day=lambda n: date(2026, 3, 1) + timedelta(days=n),
        ),
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


def row(con, call):
    """The published row of a call, as a dict, or None."""
    result = con.execute(
        "SELECT * FROM publish.concesiones_personas_fisicas WHERE numeroConvocatoria IS NOT DISTINCT FROM ?",
        [call],
    )
    names = [d[0] for d in result.description]
    found = result.fetchall()
    return dict(zip(names, found[0], strict=True)) if found else None


def rest(con, ejercicio):
    """The published rest row of a year, as a dict, or None."""
    result = con.execute(
        "SELECT * FROM publish.concesiones_personas_fisicas WHERE esResto AND ejercicio = ?",
        [ejercicio],
    )
    names = [d[0] for d in result.description]
    found = result.fetchall()
    return dict(zip(names, found[0], strict=True)) if found else None


def test_a_large_call_is_published_counting_each_person_once(con):
    a = row(con, "A")
    # 13 awards to 12 people; the company stays out.
    assert (a["concesiones"], a["beneficiarios"], float(a["importeTotal"])) == (13, 12, 1300.0)
    assert (a["esResto"], a["ejercicio"]) == (False, None)
    assert a["convocatoria"] == "Convocatoria A"


def test_below_twenty_people_the_tails_are_left_out(con):
    a = row(con, "A")
    assert [
        a[c] for c in ("importeP10", "importeP90", "fechaConcesionP10", "fechaConcesionP90")
    ] == [None] * 4
    assert float(a["importeMediana"]) == 100.0
    assert a["fechaConcesionMediana"] == date(2026, 5, 10)


def test_from_twenty_people_the_tails_are_published(con):
    f = row(con, "F")
    amounts = [
        float(f[c])
        for c in ("importeP10", "importeP25", "importeMediana", "importeP75", "importeP90")
    ]
    # Interpolated between the awards: 25 amounts from 100 to 2,500.
    assert amounts == [340.0, 700.0, 1300.0, 1900.0, 2260.0]
    assert float(f["importeMedia"]) == 1300.0
    # Rounded to the cent, like every amount.
    assert float(f["importeDesviacion"]) == 735.98
    dates = [
        f[c]
        for c in (
            "fechaConcesionP10",
            "fechaConcesionP25",
            "fechaConcesionMediana",
            "fechaConcesionP75",
            "fechaConcesionP90",
        )
    ]
    # Real award dates, one day apart from 1 March.
    assert dates == sorted(dates)
    assert all(date(2026, 3, 1) <= d <= date(2026, 3, 25) for d in dates)


def test_the_smallest_and_largest_values_are_never_published(con):
    f = row(con, "F")
    values = set(f.values())
    assert not values & {100, 2500, date(2026, 3, 1), date(2026, 3, 25)}


def test_small_calls_are_suppressed_and_gathered_into_a_rest_row(con):
    assert row(con, "B") is None and row(con, "C") is None
    # B and C together: 12 people in two calls, so the rest row may be published.
    resto = rest(con, 2026)
    assert (resto["concesiones"], resto["beneficiarios"], float(resto["importeTotal"])) == (
        12,
        12,
        1200.0,
    )
    # Nothing in a rest row says which calls it gathers.
    assert [resto[c] for c in ("numeroConvocatoria", "convocatoria", "nivel3", "instrumento")] == [
        None
    ] * 4


def test_a_dominated_call_is_suppressed_and_a_lone_rest_is_not_published(con):
    assert row(con, "D") is None
    # D is 2025's only suppressed call: its rest would be D itself.
    assert rest(con, 2025) is None


def test_a_title_shaped_like_a_tax_id_is_blanked(con):
    e = row(con, "E")
    assert e["beneficiarios"] == 10
    assert e["convocatoria"] is None


def test_the_checks_stop_a_row_below_the_minimum(con):
    con.execute(
        "INSERT INTO publish.concesiones_personas_fisicas (numeroConvocatoria, beneficiarios, esResto) "
        "VALUES ('Z', 3, false)"
    )
    with pytest.raises(duckdb.InvalidInputException, match="below 10 beneficiaries"):
        con.execute(CHECKS.read_text(encoding="utf-8"))


def test_the_checks_stop_tails_below_twenty_people(con):
    con.execute(
        "UPDATE publish.concesiones_personas_fisicas SET importeP90 = 999 WHERE numeroConvocatoria = 'A'"
    )
    with pytest.raises(duckdb.InvalidInputException, match="10th or 90th percentiles below 20"):
        con.execute(CHECKS.read_text(encoding="utf-8"))


def test_the_checks_stop_an_identifying_column(con):
    con.execute("ALTER TABLE publish.concesiones_personas_fisicas ADD COLUMN idPersona BIGINT")
    with pytest.raises(duckdb.InvalidInputException, match="identifying columns: idPersona"):
        con.execute(CHECKS.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("first_organ", "second_organ", "published"),
    [
        # Most of the call's awards come from one body: that one.
        ((7, "ORGANO B"), (5, "ORGANO A"), "ORGANO B"),
        # A tie: the first in alphabetical order, every time.
        ((6, "ORGANO B"), (6, "ORGANO A"), "ORGANO A"),
    ],
)
def test_a_call_with_several_bodies_shows_the_main_one(
    tmp_path, first_organ, second_organ, published
):
    (n_first, organ_first), (n_second, organ_second) = first_organ, second_organ
    awards = [
        *people("G", n_first, 700, nivel3=organ_first),
        *people("G", n_second, 800, nivel3=organ_second),
    ]
    sync_db = make_sync_db(
        tmp_path / "sync.duckdb",
        [version(a["id"], T1, None, True, None, a) for a in awards],
        [],
        [],
    )
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    run_steps(
        con,
        {n for n in (p.name for p in (ROOT / "dataset" / "sql").iterdir()) if n != "95_export.sql"},
    )
    assert con.execute(
        "SELECT nivel3 FROM publish.concesiones_personas_fisicas WHERE numeroConvocatoria = 'G'"
    ).fetchone() == (published,)


def build_without_export(tmp_path, concesiones=(), ayudas=(), minimis=()):
    sync_db = make_sync_db(
        tmp_path / "sync.duckdb",
        *[
            [version(i, T1, None, True, None, r) for i, r in enumerate(rows)]
            for rows in (concesiones, ayudas, minimis)
        ],
    )
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    run_steps(
        con,
        {n for n in (p.name for p in (ROOT / "dataset" / "sql").iterdir()) if n != "95_export.sql"},
    )
    return con


def self_employed(make, call, count, start, amount, **extra):
    """State aid or de minimis aid to `count` self-employed people in one call."""
    return [
        dict(
            make(start + n, f"***{start + n:04d}** NOMBRE", amount),
            numeroConvocatoria=call,
            convocante="ESTADO MINISTERIO DE EJEMPLO",
            idPersona=str(start + n),
            **extra,
        )
        for n in range(count)
    ]


def test_state_aid_summarises_both_amounts(tmp_path):
    con = build_without_export(tmp_path, ayudas=self_employed(state_aid, "S1", 12, 100, 1000))
    total, equivalente, convocante, beneficiarios = con.execute(
        "SELECT importeTotal, ayudaEquivalenteTotal, convocante, beneficiarios "
        "FROM publish.ayudasestado_personas_fisicas"
    ).fetchone()
    # state_aid() sets the gross grant equivalent to half the amount.
    assert (float(total), float(equivalente), beneficiarios) == (12000.0, 6000.0, 12)
    assert convocante == "ESTADO MINISTERIO DE EJEMPLO"


def test_one_person_holding_most_of_either_amount_suppresses_the_call(tmp_path):
    # Equal amounts, but one person holds most of the gross grant equivalent.
    rows = self_employed(state_aid, "S2", 12, 200, 1000)
    rows[0]["ayudaEquivalente"] = "100000"
    con = build_without_export(tmp_path, ayudas=rows)
    assert con.execute("SELECT count(*) FROM publish.ayudasestado_personas_fisicas").fetchone() == (
        0,
    )


def test_de_minimis_summarises_only_its_gross_grant_equivalent(tmp_path):
    con = build_without_export(tmp_path, minimis=self_employed(de_minimis, "M1", 11, 300, 900))
    columns = {
        name
        for (name,) in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'publish' AND table_name = 'minimis_personas_fisicas'"
        ).fetchall()
    }
    assert "ayudaEquivalenteTotal" in columns and not any(c.startswith("importe") for c in columns)
    assert con.execute(
        "SELECT beneficiarios, ayudaEquivalenteTotal FROM publish.minimis_personas_fisicas"
    ).fetchone() == (11, 9900)
