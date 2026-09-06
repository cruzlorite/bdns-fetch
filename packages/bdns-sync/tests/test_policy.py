"""The refactor to `PayloadPolicy` must not change a single hash.

Every stored `_row_hash` was computed by the code as it stood before the
policy object existed. If moving the rules into it changes even one byte of
what `canonical_json` sees, the first run after upgrading re-versions all 23
tables: 41 million rows of history that record nothing but a refactor.

The hashes below were captured from the real fixture payloads with the
previous implementation, so they are evidence rather than a restatement of
what the code now does. They must never be regenerated to make a failing
test pass: a diff here means the change is not hash-neutral, and the
decision to accept it belongs in a release note, not in this file.
"""

import json
import pathlib

import pytest

from bdns.sync.policy import DEFAULT_POLICY, PayloadPolicy
from bdns.sync.syncers import (
    AYUDASESTADO_POLICY,
    CONCESIONES_POLICY,
    GRANDESBENEFICIARIOS_POLICY,
    MINIMIS_POLICY,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

POLICIES = {
    "sectores": DEFAULT_POLICY,
    "regiones": DEFAULT_POLICY,
    "organos": DEFAULT_POLICY,
    "concesiones_busqueda": CONCESIONES_POLICY,
    "ayudasestado_busqueda": AYUDASESTADO_POLICY,
    "minimis_busqueda": MINIMIS_POLICY,
    "grandesbeneficiarios_busqueda": GRANDESBENEFICIARIOS_POLICY,
    "convocatorias_busqueda": DEFAULT_POLICY,
    "planesestrategicos_busqueda": DEFAULT_POLICY,
}

GOLDEN_HASHES = {
    "sectores": [
        "bff1ca595b80421901e285892e07f9860a451a587915bfd68696f958fd901a2f",
        "b981e6d1dbef641cc6e0ea83e635b78b52d79ef6e92a099d82bd7c7c47ca32fe",
        "0f4c0bdc46b4665744997282c29085c5e0768fd761d0fb62cfec8f6b2b2b7f56"
    ],
    "regiones": [
        "5dec703760c6444496155bb74444229572b7771cbed2aec4bdd44cfe6ce61e22",
        "8f5c0eb58661ca56e48858cbd7ac441c309d7dbf316d376afd589b4b92dd2201"
    ],
    "organos": [
        "f296f14f45bfae80a2bf9410e37452d3b7f56bac6c36344447b72e74ebcd3521",
        "608c3da5da7be5b543bdb285a45b779f9658684c03ef39df2f01ca7e2877d21a"
    ],
    "concesiones_busqueda": [
        "209f434a1640405bea624cc927ab67eafdbb76b30494928b02bf26460eb3fb0a",
        "04630944a46ed8aa15ad2683741599bacd52eb0b5d0d3fba866377952d12972a",
        "f809a13aa10b1dedd44f8822173a2cf0ef13dc40ff3e1c996bcf246ca1f92ac4"
    ],
    "ayudasestado_busqueda": [
        "bc9e67e93c8bb5617a43ddec73fb960eb822f5d2f58165dfebc51617849a435c",
        "32eced44de4a5591abe7d76747a90e627d357b40fa8382ebbf3ccf8117cab525",
        "8114d5f5226d8a5d6ed7f10d95274956bb8f325d7a5d675b1d6766f32e000c02"
    ],
    "minimis_busqueda": [
        "f844c2cdcea26889c2b3c3196c69ca2c5c375987aaa5506d1bde7676d26a8caf",
        "3623421caadd478949b84223b9a8d359fa09ee0862649ba916a2be2256db35bb",
        "d5c507a4bed9c99810001f6e6b7e0b14b21ba1f76e75b0d77ba90c8939cad067"
    ],
    "grandesbeneficiarios_busqueda": [
        "08f8efe7a7a56a9f8699f2819db5b82e10303f429d28aff88883f9290f84a587",
        "4ec46316ef08f89d5db1f2de15ff223d0f15af79993d01316b3306a7e8b42a11",
        "5565a2e2b42894b25a16bfde1df95809c086d50bf0a28b6fed48968f87318218"
    ],
    "convocatorias_busqueda": [
        "7c56e68d57a7518b646059e38a08802b782e2df0118317a419ce2b0d95f193e7",
        "564276e456ddd01489f5fa2c814e62fa804946a814ede76e04f01756aa251e0e",
        "ffcdb611abc4da279b15cc145a94f9affa5ff44c54fb6db47b62de414f72c13c"
    ],
    "planesestrategicos_busqueda": [
        "c35e4315b634a0f5ebe23a102a4e9efd0e061e6a9af5bf3bbf89859c5c5159dd",
        "9a307b1960f88ec186986b70a76ce9b1a6803cc83cd32ed3e4eef2775984c1ef"
    ]
}

def payloads(name):
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    records = [r["payload"] if isinstance(r, dict) and "payload" in r else r for r in data]
    return [r for r in records if isinstance(r, dict)]


@pytest.mark.parametrize("entity", sorted(POLICIES))
def test_the_policy_reproduces_the_hashes_the_old_code_produced(entity):
    expected = GOLDEN_HASHES[entity]
    actual = [POLICIES[entity].prepare(p)[1] for p in payloads(entity)[: len(expected)]]
    assert actual == expected


@pytest.mark.parametrize("entity", sorted(POLICIES))
def test_the_default_policy_stores_the_record_untouched(entity):
    """Phase one adds no payload transform, so what is stored has to be
    the record as received, not a copy or a reordering of it.
    """
    for raw in payloads(entity)[:3]:
        stored, _ = POLICIES[entity].prepare(raw)
        assert stored is raw


def test_dropping_a_field_changes_both_what_is_stored_and_the_hash():
    """The invariant the module exists for: a different hash always means a
    different stored payload. Hashing the record as received would let the
    two disagree.
    """
    raw = {"id": 1, "nombre": "JOSE", "importe": 100}
    kept, kept_hash = DEFAULT_POLICY.prepare(raw)
    dropped, dropped_hash = PayloadPolicy(drop=("nombre",)).prepare(raw)

    assert "nombre" in kept and "nombre" not in dropped
    assert kept_hash != dropped_hash


def test_a_change_confined_to_a_dropped_field_is_not_a_change():
    """And the other direction: with the field gone from what is stored,
    two records differing only in it are the same record. Hashing the raw
    record would version the row and leave two byte-identical payloads
    behind, a change nobody could ever see.
    """
    policy = PayloadPolicy(drop=("nombre",))
    before, before_hash = policy.prepare({"id": 1, "nombre": "JOSE", "importe": 100})
    after, after_hash = policy.prepare({"id": 1, "nombre": "JOSÉ", "importe": 100})
    assert before == after
    assert before_hash == after_hash


def test_excluding_a_dropped_field_from_the_hash_is_redundant():
    """Documented in PayloadPolicy: `drop` already removes the field before
    anything is hashed, so naming it in `hash_exclude` too does nothing.
    """
    raw = {"id": 1, "nombre": "JOSE"}
    only_drop = PayloadPolicy(drop=("nombre",)).prepare(raw)[1]
    both = PayloadPolicy(drop=("nombre",), hash_exclude=("nombre",)).prepare(raw)[1]
    assert only_drop == both


def test_a_policy_may_not_drop_a_key_field():
    with pytest.raises(ValueError, match="Identity is not policy"):
        PayloadPolicy(drop=("id",)).check_identity(("id",), None)


def test_a_policy_may_not_drop_the_registration_date_field():
    with pytest.raises(ValueError, match="Identity is not policy"):
        PayloadPolicy(drop=("fechaAlta",)).check_identity(("id",), "fechaAlta")


def test_an_ordinary_policy_passes_the_identity_check():
    CONCESIONES_POLICY.check_identity(("id",), "fechaAlta")


def test_turning_off_canonical_arrays_makes_array_order_count_again():
    a = {"id": 1, "hijos": [{"id": 2}, {"id": 3}]}
    b = {"id": 1, "hijos": [{"id": 3}, {"id": 2}]}
    assert DEFAULT_POLICY.prepare(a)[1] == DEFAULT_POLICY.prepare(b)[1]

    raw_order = PayloadPolicy(canonical_arrays=False)
    assert raw_order.prepare(a)[1] != raw_order.prepare(b)[1]


def test_describe_is_canonical_and_order_independent():
    """Two equivalent policies must describe identically, or the string is
    useless for spotting that the rules changed between runs.
    """
    one = PayloadPolicy(drop=("b", "a"), hash_exclude=("d", "c"))
    two = PayloadPolicy(drop=("a", "b"), hash_exclude=("c", "d"))
    assert one.describe() == two.describe()
    assert "drop=['a', 'b']" in one.describe()
