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
set -euo pipefail

: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"

# groups A/B/C/F/G -- full replace every run, no window concept
bdns-sync sync sectores
bdns-sync sync actividades
bdns-sync sync finalidades
bdns-sync sync beneficiarios
bdns-sync sync instrumentos
bdns-sync sync objetivos
bdns-sync sync convocatorias_ultimas
bdns-sync sync organos
bdns-sync sync organos_agrupacion
bdns-sync sync regiones
bdns-sync sync reglamentos
bdns-sync sync sanciones_busqueda
bdns-sync sync grandesbeneficiarios_anios
bdns-sync sync grandesbeneficiarios_busqueda
bdns-sync sync planesestrategicos_busqueda
bdns-sync sync planesestrategicos
bdns-sync sync planesestrategicos_vigencia

# group D + convocatorias -- reg-date incremental, cascading windows
run_window() {
  local window="$1"
  bdns-sync sync concesiones_busqueda --window "$window"
  bdns-sync sync ayudasestado_busqueda --window "$window"
  bdns-sync sync minimis_busqueda --window "$window"
  bdns-sync sync partidospoliticos_busqueda --window "$window"
  bdns-sync sync convocatorias_busqueda --window "$window"
  bdns-sync sync convocatorias --window "$window"
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
