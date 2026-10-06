"""Party aid, large beneficiaries, calls, strategic plans and catalogues
(dataset/sql/13, 14, 26, 27, 30, 31 and 32). Everything here is made up."""

import duckdb

from tests.dataset.conftest import ROOT, T1, make_sync_db, run_steps, version


def build(tmp_path, **tables):
    """Run every step but the export against a sync database holding `tables`."""
    rows = {
        name: [version(i, T1, None, True, None, p) for i, p in enumerate(payloads)]
        for name, payloads in tables.items()
    }
    sync_db = make_sync_db(tmp_path / "sync.duckdb", [], [], [], **rows)
    con = duckdb.connect()
    con.execute(f"ATTACH '{sync_db}' AS sync (READ_ONLY)")
    run_steps(con, {p.name for p in (ROOT / "dataset" / "sql").iterdir()} - {"95_export.sql"})
    return con


def party_award(key, beneficiario):
    return {
        "id": key,
        "codConcesion": f"SB{key}",
        "fechaConcesion": "2026-03-02",
        "beneficiario": beneficiario,
        "instrumento": "SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN ",
        "importe": 50000,
        "ayudaEquivalente": 50000,
        "urlBR": f"https://boletin.example/{key}.pdf",
        "tieneProyecto": False,
        "numeroConvocatoria": "800001",
        "idConvocatoria": 1,
        "convocatoria": "Subvenciones a partidos políticos 2026",
        "nivel1": "ESTADO",
        "nivel2": "MINISTERIO DE EJEMPLO",
        "nivel3": "SUBDIRECCIÓN DE EJEMPLO",
    }


def test_party_aid_publishes_legal_persons_without_the_bulletin_link(tmp_path):
    con = build(
        tmp_path,
        partidospoliticos_busqueda=[
            party_award(1, "G12345678 PARTIDO DE EJEMPLO"),
            party_award(2, "***1234** NOMBRE APELLIDO"),
        ],
    )
    assert con.execute(
        "SELECT id, nif, nombre, instrumento FROM publish.partidospoliticos"
    ).fetchall() == [
        (
            1,
            "G12345678",
            "PARTIDO DE EJEMPLO",
            "SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN",
        )
    ]
    columns = {
        c
        for (c,) in con.execute(
            "SELECT column_name FROM (DESCRIBE publish.partidospoliticos)"
        ).fetchall()
    }
    assert "urlBR" not in columns


def test_large_beneficiaries_keep_legal_persons_only(tmp_path):
    big = [
        {
            "idPersona": 1,
            "beneficiario": "B12345678 EMPRESA SL",
            "ejercicio": 2026,
            "ayudaETotal": 2500000.5,
        },
        {
            "idPersona": 2,
            "beneficiario": "***1234** NOMBRE APELLIDO",
            "ejercicio": 2026,
            "ayudaETotal": 900000,
        },
        {
            "idPersona": 3,
            "beneficiario": "E12345678 APELLIDO Y APELLIDO CB",
            "ejercicio": 2026,
            "ayudaETotal": 800000,
        },
    ]
    con = build(tmp_path, grandesbeneficiarios_busqueda=big)
    rows = con.execute(
        "SELECT nif, nombre, ejercicio, ayudaETotal FROM publish.grandesbeneficiarios"
    ).fetchall()
    assert [(n, m, e, float(a)) for n, m, e, a in rows] == [
        ("B12345678", "EMPRESA SL", 2026, 2500000.5)
    ]
    columns = {
        c
        for (c,) in con.execute(
            "SELECT column_name FROM (DESCRIBE publish.grandesbeneficiarios)"
        ).fetchall()
    }
    assert "idPersona" not in columns


def call(id_, title, **extra):
    return {
        "id": id_,
        "organo": {
            "nivel1": "AUTONOMICA",
            "nivel2": "COMUNIDAD DE EJEMPLO",
            "nivel3": "CONSEJERÍA DE EJEMPLO",
        },
        "codigoBDNS": str(900000 + id_),
        "fechaRecepcion": "2026-01-15",
        "instrumentos": [{"descripcion": "SUBVENCIÓN Y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN "}],
        "tipoConvocatoria": "Concurrencia competitiva - canónica",
        "presupuestoTotal": 100000,
        "mrr": False,
        "descripcion": title,
        "tiposBeneficiarios": [
            {"descripcion": "PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA"}
        ],
        "sectores": [{"codigo": "01.1", "descripcion": "Cultivos no perennes"}],
        "regiones": [{"descripcion": "ES11 - GALICIA"}],
        "urlBasesReguladoras": "https://boletin.example/bases.pdf",
        "fechaInicioSolicitud": "2026-02-01",
        "fechaFinSolicitud": "2026-03-01",
        "documentos": [{"id": 1, "nombreFic": "resolucion.pdf", "descripcion": "Resolución"}],
        "anuncios": [
            {
                "titulo": "Anuncio",
                "texto": "Texto del anuncio",
                "url": "https://boletin.example/a.pdf",
            }
        ],
        **extra,
    }


def test_calls_keep_the_api_shape_and_leave_out_documents_and_announcements(tmp_path):
    con = build(tmp_path, convocatorias=[call(1, "Ayudas a la agricultura 2026")])
    row = con.execute(
        "SELECT codigoBDNS, organo, instrumentos, sectores, regiones, fechaInicioSolicitud "
        "FROM publish.convocatorias"
    ).fetchone()
    assert row[0] == "900001"
    # Objects and lists of objects keep the API's names and values.
    assert row[1] == {
        "nivel1": "AUTONOMICA",
        "nivel2": "COMUNIDAD DE EJEMPLO",
        "nivel3": "CONSEJERÍA DE EJEMPLO",
    }
    assert row[2] == [{"descripcion": "SUBVENCIÓN Y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN "}]
    assert row[3] == [{"codigo": "01.1", "descripcion": "Cultivos no perennes"}]
    assert row[4] == [{"descripcion": "ES11 - GALICIA"}]
    assert str(row[5]) == "2026-02-01"
    columns = {
        c
        for (c,) in con.execute(
            "SELECT column_name FROM (DESCRIBE publish.convocatorias)"
        ).fetchall()
    }
    assert not columns & {"documentos", "anuncios", "advertencia"}


def test_a_call_text_shaped_like_a_personal_id_is_published_empty(tmp_path):
    con = build(
        tmp_path,
        convocatorias=[
            call(
                2,
                "Subvención nominativa a 12345678Z",
                urlBasesReguladoras="https://boletin.example/12345678Z.pdf",
            )
        ],
    )
    # The checks passed (the build got here) and the texts are empty.
    assert con.execute(
        "SELECT descripcion, urlBasesReguladoras FROM publish.convocatorias"
    ).fetchone() == (None, None)


def test_strategic_plans_keep_their_scopes(tmp_path):
    plan = {
        "idPES": 7,
        "descripcion": "Plan estratégico de subvenciones 2026-2028",
        "descripcionCooficial": None,
        "tipoPlan": "Ministerial",
        "vigenciaDesde": 2026,
        "vigenciaHasta": 2028,
        "fechaAprobacion": "2025-12-20",
        "ambitos": ["Cultura", "Deporte"],
        "documentos": [{"id": 1}],
        "advertencia": "Aviso",
    }
    con = build(tmp_path, planesestrategicos=[plan])
    assert con.execute(
        "SELECT idPES, vigenciaDesde, vigenciaHasta, ambitos FROM publish.planesestrategicos"
    ).fetchone() == (7, 2026, 2028, ["Cultura", "Deporte"])


def test_catalogue_trees_become_one_row_per_node(tmp_path):
    organ = {
        "descripcion": "PROVINCIA DE EJEMPLO",
        "id": 27,
        "idAdmon": "L",
        "children": [
            {
                "descripcion": "VILLAEJEMPLO",
                "id": 717,
                "children": [{"descripcion": "AYUNTAMIENTO DE VILLAEJEMPLO", "id": 4081}],
            }
        ],
    }
    con = build(tmp_path, organos=[organ], instrumentos=[{"descripcion": "PRÉSTAMO", "id": 2}])
    rows = con.execute(
        "SELECT catalogo, id, descripcion, idPadre, nivel, idAdmon FROM publish.catalogos ORDER BY catalogo, nivel"
    ).fetchall()
    assert rows == [
        ("instrumentos", "2", "PRÉSTAMO", None, 1, None),
        ("organos", "27", "PROVINCIA DE EJEMPLO", None, 1, "L"),
        ("organos", "717", "VILLAEJEMPLO", "27", 2, "L"),
        ("organos", "4081", "AYUNTAMIENTO DE VILLAEJEMPLO", "717", 3, "L"),
    ]
