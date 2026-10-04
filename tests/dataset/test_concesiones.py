"""Awards (dataset/sql/10_concesiones.sql), read straight from a bdns-sync database."""


def test_each_award_keeps_its_last_known_version(built):
    rows = built.execute(
        "SELECT id, importe, tipo_persona, retirada FROM concesiones ORDER BY id"
    ).fetchall()
    assert [(i, float(m), k, w) for i, m, k, w in rows] == [
        (1, 1200.0, "persona_juridica", False),
        # Withdrawn by the API: kept with its last content.
        (2, 500.0, "persona_fisica", True),
        # Last version closed before closing reasons existed: withdrawn too.
        (3, 80.0, "desconocido", True),
    ]


def test_columns_are_typed_and_text_is_untouched(built):
    fecha_concesion, instrumento, convocatoria = built.execute(
        "SELECT fecha_concesion, instrumento, convocatoria FROM concesiones WHERE id = 1"
    ).fetchone()
    assert str(fecha_concesion) == "2026-02-10"
    assert instrumento == "SUBVENCIÓN y ENTREGA DINERARIA SIN CONTRAPRESTACIÓN"
    assert convocatoria == "Ayudas á la cultura 2026"


def test_state_aid_and_de_minimis_are_classified_too(built):
    assert built.execute(
        "SELECT id_concesion, tipo_persona FROM ayudas_estado ORDER BY id_concesion"
    ).fetchall() == [(11, "persona_juridica"), (12, "persona_fisica")]
    assert built.execute(
        "SELECT id_concesion, tipo_persona FROM minimis ORDER BY id_concesion"
    ).fetchall() == [(21, "persona_juridica"), (22, "comunidad_o_sociedad_civil")]
