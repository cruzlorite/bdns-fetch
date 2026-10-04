"""Smoke test across the entity registry: names, kinds and wiring."""

import pytest

from bdns.sync.entities import ENTITIES, full_entities, get_entity, windowed_entities


def test_registry_holds_every_synced_entity():
    assert len(full_entities()) == 16
    assert len(windowed_entities()) == 6
    assert len(ENTITIES) == 22


def test_every_entity_is_consistent():
    for name, entity in ENTITIES.items():
        assert entity.name == name
        assert entity.kind in ("full", "windowed")
        assert entity.key_fields and callable(entity.rows)
        entity.policy.check_identity(entity.key_fields, entity.reg_date_field)
        if entity.kind == "windowed":
            assert entity.history_start is not None
        else:
            assert entity.reg_date_field is None and entity.history_start is None


def test_lookup_accepts_hyphens_and_rejects_unknown_names():
    assert get_entity("concesiones-busqueda") is ENTITIES["concesiones_busqueda"]
    with pytest.raises(KeyError):
        get_entity("nope")
