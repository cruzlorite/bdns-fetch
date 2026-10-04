# 0014. The cadence lives in the CLI, as tested code

**Status:** accepted · **Date:** 2026-10-03

## Context

A production setup needs the same thing every day: check that the API
has not changed, sync the full entities and the windowed ones with the
window that day calls for (weekly by default, monthly on Mondays, annual
three days a year), carry on when one entity fails, and finish with an
exit code that fires the alert. A historical load needs to walk each
entity year by year from the start of its history.

That logic, in a shell script, is tested by nobody: the rule for which
window applies on a day, the list of entities and the failure handling
are only verified in production. And it forces a list of entities to be
kept outside the code.

A configuration file does not fit either: the cadence is not something
each installation should reinvent, but a consequence of how the API
behaves (records arriving days late, deletions only detectable inside the
window).

## Decision

`bdns-sync delta` and `bdns-sync backfill` build a plan from the entity
registry ([`orchestration`][bdns.sync.orchestration]) and run it,
isolating failures. The cadence rule is
[`cadence_window`][bdns.sync.windows.cadence_window]. Both commands take
`--dry-run`, which prints the plan with its concrete dates. `sync` still
exists for a single entity.

The scripts stay as one-line wrappers, so crontabs calling them keep
working.

## Consequences

- The cadence and the failure isolation are tested.
- Scheduling the tool is one line: `bdns-sync delta` daily.
- The tool knows what day it is. Anyone needing another cadence forces
  the window with `--window` or composes calls to `sync`.
