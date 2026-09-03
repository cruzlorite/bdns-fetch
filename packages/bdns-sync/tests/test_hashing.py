from bdns.sync.hashing import canonical_json, natural_key, row_hash, sorted_delimited_list


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_canonical_json_excludes_fields():
    assert canonical_json({"a": 1, "b": 2}, exclude_fields=["b"]) == canonical_json({"a": 1})


def test_canonical_json_is_list_order_independent():
    """Regression: `regiones` returned the same tree `children` in a
    different element order across two live calls, with nothing actually
    changed, and produced a spurious SCD2 version.
    """
    a = {"children": [{"id": 1, "descripcion": "X"}, {"id": 2, "descripcion": "Y"}]}
    b = {"children": [{"id": 2, "descripcion": "Y"}, {"id": 1, "descripcion": "X"}]}
    assert canonical_json(a) == canonical_json(b)


def test_canonical_json_list_order_independence_is_recursive():
    a = {"tree": [{"children": [{"id": 1}, {"id": 2}]}, {"children": [{"id": 3}]}]}
    b = {"tree": [{"children": [{"id": 3}]}, {"children": [{"id": 2}, {"id": 1}]}]}
    assert canonical_json(a) == canonical_json(b)


def test_canonical_json_still_detects_a_real_value_change_inside_a_list():
    a = {"children": [{"id": 1, "descripcion": "X"}]}
    b = {"children": [{"id": 1, "descripcion": "CHANGED"}]}
    assert canonical_json(a) != canonical_json(b)


def test_row_hash_stable_for_equivalent_payloads():
    assert row_hash({"a": 1, "b": 2}) == row_hash({"b": 2, "a": 1})


def test_row_hash_changes_on_value_change():
    assert row_hash({"a": 1}) != row_hash({"a": 2})


def test_natural_key_simple():
    assert natural_key({"id": 42}, ("id",)) == "[42]"


def test_natural_key_composite_is_order_stable():
    payload = {"ambito": "M", "id": 7}
    assert natural_key(payload, ("ambito", "id")) == '["M",7]'


def test_delimited_list_order_does_not_change_the_hash():
    """minimis returns `sectorActividad` with the same sectors in a different
    order between calls (see section 9 of docs/bdns-api-behavior.md).
    """
    a = {"id": 1, "sectorActividad": "52.3 - Intermediacion; 52.2 - Auxiliares"}
    b = {"id": 1, "sectorActividad": "52.2 - Auxiliares; 52.3 - Intermediacion"}
    lists = {"sectorActividad": ";"}
    assert row_hash(a) != row_hash(b)
    assert row_hash(a, None, lists) == row_hash(b, None, lists)


def test_delimited_list_ignores_spacing_around_the_separator():
    a = {"s": "b;a"}
    b = {"s": "a ; b"}
    assert row_hash(a, None, {"s": ";"}) == row_hash(b, None, {"s": ";"})


def test_a_real_change_in_a_delimited_list_still_changes_the_hash():
    a = {"s": "52.2 - Auxiliares; 52.3 - Intermediacion"}
    b = {"s": "52.2 - Auxiliares; 52.9 - Otra cosa"}
    lists = {"s": ";"}
    assert row_hash(a, None, lists) != row_hash(b, None, lists)


def test_only_declared_fields_are_treated_as_lists():
    """Auto-detection would be wrong: a comma in free text is not a list."""
    a = {"descripcion": "Ayudas a pymes, autonomos y cooperativas"}
    b = {"descripcion": "autonomos, Ayudas a pymes y cooperativas"}
    assert row_hash(a) != row_hash(b)
    assert row_hash(a, None, {"otro_campo": ","}) != row_hash(b, None, {"otro_campo": ","})


def test_sorted_delimited_list_is_deterministic():
    assert sorted_delimited_list("c;a;b", ";") == sorted_delimited_list("b;c;a", ";") == "a;b;c"
