"""Multi-day scenarios for the two entities that fan out across more than
one table: grandesbeneficiarios (_anios catalog + _busqueda search, anios
swept dynamically from the catalog) and planesestrategicos (_busqueda
discovery + detail + vigencia, both looped over the full discovered set
every run).

`grandesbeneficiarios_anios` and `planesestrategicos_busqueda` themselves
are plain `sync_full_catalog` calls. Their full insert/touch/rewrite/
delete/new-arrival cycle is covered generically in
test_timeline_full_catalogs.py, so it's not repeated here. This file only
covers what's specific to the multi-table wiring: the dynamic anios sweep
and the discover-then-detail/vigencia fan-out.
"""

from copy import deepcopy

from sqlalchemy import create_engine

from bdns.sync.sinks.sql import SQLSink
from bdns.sync.syncers import (
    sync_grandesbeneficiarios_busqueda,
    sync_planesestrategicos,
    sync_planesestrategicos_vigencia,
)
from tests.fake_client import FakeBDNSClient
from tests.timeline_helpers import current_rows, last_sync_run, sync_errors_for

# --- grandesbeneficiarios ---------------------------------------------------


def test_grandesbeneficiarios_busqueda_day_by_day_timeline():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    baseline = deepcopy(client.grandesbeneficiarios_busqueda)

    # Day 1: initial full reconciliation across both discovered years
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert stats["inserted"] == len(baseline)
    assert client.calls_to("fetch_grandesbeneficiarios_busqueda") == [{"anios": [2022, 2023]}]

    # Day 2: no change, touch only
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert stats["touched"] == len(baseline)

    # Day 3: upstream corrects one beneficiary's total, a rewrite
    client.grandesbeneficiarios_busqueda[0]["ayudaETotal"] = 1.0
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert stats["updated"] == 1

    # Day 4: a beneficiary drops off the list entirely. Full
    # reconciliation must detect it as a deletion.
    client.grandesbeneficiarios_busqueda.pop()
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, "grandesbeneficiarios_busqueda")) == len(baseline) - 1

    # Day 5: a new year appears in the _anios catalog. The anios sweep must
    # pick it up dynamically, not from a hardcoded year list, and a
    # beneficiary registered under that year is a plain insert.
    client.grandesbeneficiarios_anios.append({"id": 2024, "descripcion": 2024})
    client.grandesbeneficiarios_busqueda.append(
        {"idPersona": 9999999, "beneficiario": "99900099 FUNDACION FICTICIA NUEVA", "ejercicio": 2024, "ayudaETotal": 1000}
    )
    stats = sync_grandesbeneficiarios_busqueda(SQLSink(engine), client)
    assert client.calls_to("fetch_grandesbeneficiarios_busqueda")[-1] == {"anios": [2022, 2023, 2024]}
    assert stats["inserted"] == 1


# --- planesestrategicos ------------------------------------------------------


def test_planesestrategicos_detail_day_by_day_timeline():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    ids = [row["id"] for row in client.planesestrategicos_busqueda]
    assert len(ids) == 2

    # Day 1: discover ids, fetch detail per id, tag idPES since the API
    # doesn't echo it back
    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["inserted"] == 2
    current = current_rows(engine, "planesestrategicos")
    assert {r["payload"]["idPES"] for r in current} == set(ids)

    # Day 2: no change, touch only
    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["touched"] == 2

    # Day 3: rewrite, one plan's detail changes
    first_id = str(ids[0])
    client.planesestrategicos_detail[first_id]["fechaAprobacion"] = "2027-01-01"
    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["updated"] == 1

    # Day 4: a plan disappears from discovery entirely. Full reconciliation
    # closes it out; discover-then-detail still reconciles against the
    # full discovered set every run, same as any other full catalog.
    client.planesestrategicos_busqueda = [
        row for row in client.planesestrategicos_busqueda if str(row["id"]) != first_id
    ]
    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["soft_deleted"] == 1
    assert len(current_rows(engine, "planesestrategicos")) == 1


def test_planesestrategicos_malformed_detail_is_skipped_not_crashed():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    ids = [row["id"] for row in client.planesestrategicos_busqueda]
    client.planesestrategicos_detail[str(ids[0])] = "<html>not json</html>"

    stats = sync_planesestrategicos(SQLSink(engine), client)
    assert stats["inserted"] == 1  # only the well-formed plan makes it in
    assert last_sync_run(engine, "planesestrategicos")["rows_skipped"] == 1
    [error] = sync_errors_for(engine, "planesestrategicos")
    assert error["context"] == f"planesestrategicos idPES={ids[0]}"
    assert error["content"] == "<html>not json</html>"


def test_planesestrategicos_vigencia_is_a_separate_reconciled_table():
    engine = create_engine("sqlite:///:memory:")
    client = FakeBDNSClient()
    ids = [row["id"] for row in client.planesestrategicos_busqueda]

    stats = sync_planesestrategicos_vigencia(SQLSink(engine), client)
    assert stats["inserted"] == len(ids)

    first_id = str(ids[0])
    client.planesestrategicos_vigencia[first_id]["vigHasta"].append({"id": 2099, "descripcion": 2099})
    stats = sync_planesestrategicos_vigencia(SQLSink(engine), client)
    assert stats["updated"] == 1
