from datetime import date

import pytest

from bdns.sync.entities import ENTITIES, full_entities, windowed_entities
from bdns.sync.orchestration import Step, backfill_plan, delta_plan, run_plan
from bdns.sync.sinks import SyncStats

WEDNESDAY = date(2026, 3, 11)


def test_delta_syncs_every_full_entity_then_every_windowed_one_with_the_cadence_window():
    steps = delta_plan(WEDNESDAY)
    assert [s.entity.name for s in steps] == list(ENTITIES)
    assert all(s.window is None for s in steps[: len(full_entities())])
    assert {s.window for s in steps[len(full_entities()) :]} == {"weekly"}


def test_delta_window_can_be_forced():
    assert {s.window for s in delta_plan(WEDNESDAY, "daily") if s.window} == {"daily"}


def test_backfill_loads_each_windowed_entity_year_by_year_from_its_history_start():
    steps = backfill_plan(WEDNESDAY, ["concesiones_busqueda"])
    assert [(s.since, s.until) for s in steps] == [
        (date(year, 1, 1), date(year, 12, 31)) for year in range(2020, 2026)
    ] + [(date(2026, 1, 1), None)]


def test_backfill_of_everything_starts_with_the_full_entities():
    steps = backfill_plan(WEDNESDAY)
    assert [s.entity for s in steps[: len(full_entities())]] == full_entities()
    assert {s.entity.name for s in steps} == set(ENTITIES)


def test_backfill_on_new_years_day_has_no_slice_for_the_year_just_started():
    steps = backfill_plan(date(2026, 1, 1), ["convocatorias"])
    assert steps[-1].until == date(2025, 12, 31)


def test_backfill_accepts_hyphenated_names_and_rejects_unknown_ones():
    assert backfill_plan(WEDNESDAY, ["sectores"])[0].entity.name == "sectores"
    assert backfill_plan(WEDNESDAY, ["minimis-busqueda"])
    with pytest.raises(KeyError):
        backfill_plan(WEDNESDAY, ["nope"])


def test_step_describes_its_concrete_dates():
    assert Step(ENTITIES["sectores"]).describe() == "sectores: complete state"
    step = Step(ENTITIES["minimis_busqueda"], window="daily")
    assert step.describe(WEDNESDAY) == "minimis_busqueda: daily [2026-03-10 .. 2026-03-10]"


class FlakySink:
    """Fails for one entity, succeeds for the rest."""

    def __init__(self, failing):
        self.failing = failing
        self.synced = []

    def sync_full(self, name, rows, key_fields, **kwargs):
        if name == self.failing:
            raise RuntimeError("quota exceeded")
        self.synced.append(name)
        return SyncStats(fetched=1, new=1)

    def sync_window(self, name, rows, key_fields, **kwargs):
        return self.sync_full(name, rows, key_fields)


class NoClient:
    def __getattr__(self, name):
        return lambda **kwargs: []


def test_one_failing_entity_does_not_stop_the_others():
    steps = [Step(e) for e in full_entities()[:3]]
    sink = FlakySink(failing=steps[1].entity.name)
    results = run_plan(steps, sink, NoClient())
    assert [r.ok for r in results] == [True, False, True]
    assert "quota exceeded" in results[1].error
    assert sink.synced == [steps[0].entity.name, steps[2].entity.name]
    assert results[0].stats == SyncStats(fetched=1, new=1)


def test_windowed_steps_run_too():
    steps = [Step(windowed_entities()[0], window="daily")]
    assert run_plan(steps, FlakySink(failing=None), NoClient())[0].ok
