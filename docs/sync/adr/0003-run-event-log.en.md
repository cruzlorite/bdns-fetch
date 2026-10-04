# 0003. `_sync_runs` as an event log, not a status column

**Status:** accepted · **Date:** 2026-07-08 (predates the recorded history)

## Context

Looking at the target, you need to be able to tell whether a run finished
well.

The usual design is one row per run with a `status` column that moves
from `running` to `success` or `failed`.

That cannot record the case that matters most: **a process that dies
halfway**. A dead process does not update its own row, so the run stays
`running` forever, indistinguishable from one still going.

## Decision

`_sync_runs` is an append-only **event** log. A row, once written, is
never updated.

- A `started` event when the run begins, committed immediately and
  **outside the data transaction**.
- A terminal `success` or `failed` event when it ends.

A run's state is its latest event. A `started` with no terminal event
means the process died halfway.

Events go in short transactions of their own. Inside the data transaction
they would share its fate: on a transactional engine, a failed run would
roll back its own events and erase every failed run from the log.

## Consequences

- The log always tells the truth, even when the data rolled back.
- Two rows per run instead of one.
- There is a theoretical window where the data commits and the `success`
  event never gets written. Accepted: the `_sync_*` tables are
  informational, and the sync logic never reads them.
- The operating rule is the same on every engine: **no `success` event,
  run it again.**
