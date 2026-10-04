# SPDX-License-Identifier: MIT

"""Plans of many syncs: the daily delta and the historical backfill.

A plan is a list of [`Step`][bdns.sync.orchestration.Step]s, each one
sync of one entity, built from the entity registry. Building the plan is
separate from running it, so `--dry-run` prints exactly what a run would
do, and the cadence rules are ordinary tested Python rather than a shell
script nothing tested
([ADR 0007](../../adr/0007-cadence-in-the-cli.md)).

Running a plan isolates failures: one entity failing does not stop the
others. They are independent syncs sharing only the target, and stopping
the day over one of them only widens the outage.
"""

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from bdns.fetch import BDNSClient
from bdns.sync.entities import Entity, full_entities, get_entity, sync_entity, windowed_entities
from bdns.sync.sinks import Sink, SyncStats
from bdns.sync.windows import cadence_window, resolve_when

__all__ = ["Step", "StepResult", "backfill_plan", "delta_plan", "run_plan"]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class Step:
    """One sync of one entity.

    Attributes:
        entity: What to sync.
        window: Named window, for a windowed entity.
        since: First day of an explicit range, for a windowed entity.
        until: Last day of that range; None means yesterday.
    """

    entity: Entity
    window: str | None = None
    since: date | None = None
    until: date | None = None

    def describe(self, today: date | None = None) -> str:
        """One line saying what this step syncs, with its concrete dates."""
        if self.entity.kind == "full":
            return f"{self.entity.name}: complete state"
        start, end, run_type = resolve_when(self.window, self.since, self.until, today)
        return f"{self.entity.name}: {run_type} [{start} .. {end}]"


@dataclass(frozen=True)
class StepResult:
    """The outcome of one step.

    Attributes:
        step: The step.
        stats: What the run did, if it succeeded.
        error: Why it failed, if it did.
    """

    step: Step
    stats: SyncStats | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Whether the step succeeded."""
        return self.error is None


def delta_plan(today: date, window: str | None = None) -> list[Step]:
    """Build the daily run: every full entity, then every windowed one.

    Args:
        today: The day the run happens.
        window: Window for the windowed entities. Defaults to the one the
            cadence picks for `today`
            ([`cadence_window`][bdns.sync.windows.cadence_window]).

    Returns:
        The steps, in sync order.
    """
    window = window or cadence_window(today)
    return [Step(e) for e in full_entities()] + [
        Step(e, window=window) for e in windowed_entities()
    ]


def backfill_plan(today: date, names: Sequence[str] | None = None) -> list[Step]:
    """Build a historical load: full entities, then each windowed one year by year.

    A windowed entity is loaded from its `history_start` in one-year
    slices, so a failure costs one year rather than the whole history, and
    each slice is a run of its own in the log. The last slice ends
    yesterday.

    Args:
        today: The day the run happens.
        names: Limit the plan to these entities. Defaults to all.

    Returns:
        The steps, in sync order.

    Raises:
        KeyError: If a name is not an entity.
    """
    wanted = {get_entity(name).name for name in names} if names else None
    steps = [Step(e) for e in full_entities() if wanted is None or e.name in wanted]
    for entity in windowed_entities():
        if wanted is not None and entity.name not in wanted:
            continue
        first_year = (entity.history_start or today).year
        for year in range(first_year, today.year):
            steps.append(Step(entity, since=date(year, 1, 1), until=date(year, 12, 31)))
        if date(today.year, 1, 1) <= today - timedelta(days=1):
            steps.append(Step(entity, since=date(today.year, 1, 1)))
    return steps


def run_plan(steps: Iterable[Step], sink: Sink, client: BDNSClient) -> list[StepResult]:
    """Run every step, carrying on past failures.

    Args:
        steps: The plan.
        sink: Where the rows are applied.
        client: The BDNS API client.

    Returns:
        One result per step, in order. The failed runs are also recorded
        as `failed` in `_sync_runs` by the sink.
    """
    results = []
    for step in steps:
        logger.info(">>> %s", step.describe())
        try:
            stats = sync_entity(
                step.entity, sink, client, step.window, since=step.since, until=step.until
            )
        except Exception as exc:  # one entity's failure must not stop the others
            logger.error("!!! %s failed: %s", step.entity.name, exc)
            results.append(StepResult(step, error=f"{type(exc).__name__}: {exc}"))
        else:
            results.append(StepResult(step, stats=stats))
    return results
