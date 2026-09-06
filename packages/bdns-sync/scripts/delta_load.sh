#!/usr/bin/env bash
#
# Orchestration for bdns-sync. This script owns all cadence/scheduling
# knowledge -- bdns-sync itself is a pure parameterized tool with no config
# file and no idea what day it is. One crontab line calls this once a day:
#
#   0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/delta_load.sh
#
# Windows are nested, not independent: every window ends at yesterday
# (window_bounds in generic.py), so annual ⊃ monthly ⊃ weekly ⊃ daily on any
# given day. Running the widest window that applies today already covers
# every narrower one for free, so exactly one window runs per day, the
# widest that applies.
#
# The baseline is weekly, not daily: records can surface with a reg-date
# days in the past, and deletion detection only looks inside the window it
# runs with, so a 7-day lookback every day catches late arrivals and late
# removals that a 1-day window would miss until the next wide pass. Mondays
# widen to monthly, and three days a year (Jan/May/Sep 1st) to annual, for
# progressively deeper reconciliation.
#
# One failing entity must not cancel the other 21. They are independent
# syncs sharing nothing but the target, so aborting the whole day over one
# of them just widens the outage: seen live on 2 September 2026, when
# `sectores` (a 24-row catalog) hit the BigQuery daily quota and took the
# other 22 entities down with it, leaving 1 run that day instead of 23.
# So: no `set -e`. Failures are collected and reported at the end, and the
# script still exits non-zero so the job is marked failed and the alert
# fires. `-u` and `pipefail` stay; they catch bugs in this script itself.
set -uo pipefail

: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"

failed=()

run() {
  echo ">>> $*"
  if ! "$@"; then
    echo "!!! FAILED: $*" >&2
    failed+=("$*")
  fi
}

report_and_exit() {
  # Captured first: this must preserve the status we were exiting with,
  # or a run killed at the task timeout would report success just because
  # no individual entity had failed yet.
  local status=$?
  if [ ${#failed[@]} -gt 0 ]; then
    echo "=== ${#failed[@]} sync(s) failed ===" >&2
    printf '  %s\n' "${failed[@]}" >&2
    [ "$status" -eq 0 ] && status=1
  elif [ "$status" -eq 0 ]; then
    echo "=== all syncs succeeded ==="
  else
    echo "=== run terminated before finishing (status $status) ===" >&2
  fi
  exit "$status"
}

# Summarize on the way out however we leave, including a graceful kill:
# Cloud Run sends SIGTERM at the task timeout before SIGKILL, so the
# summary still gets written. An OOM kill is SIGKILL and cannot be
# trapped by anything, so that case prints nothing; the missing summary
# is itself the signal that the run was killed rather than finished.
# TERM/INT exit with the conventional status and let the EXIT trap do the
# reporting, so the summary is printed exactly once.
trap report_and_exit EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

# The engine's date handling rests on behavior measured against the live
# service, and the tests can only pin our model of it, not the service. Ask
# the real API once a day, before syncing anything. This aborts only when
# the API returns valid data contradicting an invariant; a blip or an empty
# probe day exits zero and the cadence proceeds.
echo "=== API contract check ==="
if ! bdns-sync check-api; then
  echo "!!! API contract check failed; syncing nothing today" >&2
  failed+=("bdns-sync check-api")
  exit 1
fi

# groups A/B/C/F/G -- full replace every run, no window concept
echo "=== full-replace catalogs ==="
run bdns-sync sync sectores
run bdns-sync sync actividades
run bdns-sync sync finalidades
run bdns-sync sync beneficiarios
run bdns-sync sync instrumentos
run bdns-sync sync objetivos
run bdns-sync sync organos
run bdns-sync sync organos_agrupacion
run bdns-sync sync regiones
run bdns-sync sync reglamentos
run bdns-sync sync sanciones_busqueda
run bdns-sync sync grandesbeneficiarios_anios
run bdns-sync sync grandesbeneficiarios_busqueda
run bdns-sync sync planesestrategicos_busqueda
run bdns-sync sync planesestrategicos
run bdns-sync sync planesestrategicos_vigencia

# group D + convocatorias -- reg-date incremental, cascading windows
run_window() {
  local window="$1"
  echo "=== windowed endpoints ($window) ==="
  run bdns-sync sync concesiones_busqueda --window "$window"
  run bdns-sync sync ayudasestado_busqueda --window "$window"
  run bdns-sync sync minimis_busqueda --window "$window"
  run bdns-sync sync partidospoliticos_busqueda --window "$window"
  run bdns-sync sync convocatorias_busqueda --window "$window"
  run bdns-sync sync convocatorias --window "$window"
}

case "$(date +%m-%d)" in
  01-01|05-01|09-01)
    run_window annual                      # three times a year
    ;;
  *)
    if [ "$(date +%u)" = 1 ]; then
      run_window monthly                   # Monday
    else
      run_window weekly                    # every other day
    fi
    ;;
esac
