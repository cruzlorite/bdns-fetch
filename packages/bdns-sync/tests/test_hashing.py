from bdns.sync.hashing import canonical_json, natural_key, row_hash


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
