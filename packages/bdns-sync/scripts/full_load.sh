#!/usr/bin/env bash
#
# One-time bootstrap of a fresh target: every full-replace catalog, then
# the deep historical backfill of the reg-date incremental endpoints.
# bdns-sync itself is a pure primitive with no idea how far back each
# endpoint's data goes, so -- like delta_load.sh owns the cadence -- this
# script owns the earliest dates.
#
#   BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/full_load.sh
#
# Backfills are sliced into one-year pieces (--since/--until) on purpose:
# each slice commits its own SCD2 diff, so a crash loses at most the slice
# in flight, never the whole multi-hour backfill. There is no resume-within-
# a-run; recovery is simply re-running from the failed slice down. Re-running
# anything is safe: SCD2 is idempotent, an already-synced record is just
# touched, not duplicated.
#
# The per-entity start years are floors, not exact firsts: the API only
# retains a bounded history (measured live, see README "Carga histórica /
# Historical load"), and querying earlier just returns empty weeks cheaply.
# A single conservative floor (2013, roughly when the portal started) would
# also work; per-entity floors just avoid a pile of empty calls for the
# short-retention endpoints. Widen any start if you want to be extra safe.
set -euo pipefail

: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"

run() { echo ">>> $*"; "$@"; }

echo "=== full-replace catalogs ==="
run bdns-sync sync sectores
run bdns-sync sync actividades
run bdns-sync sync finalidades
run bdns-sync sync beneficiarios
run bdns-sync sync instrumentos
run bdns-sync sync objetivos
run bdns-sync sync convocatorias_ultimas
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

echo "=== historical backfills (one-year slices) ==="
# backfill <entity> <start-year>: one run per year from start-year through
# last year, then an open-ended run for the current year (ends yesterday).
backfill() {
  local entity="$1" year="$2" current
  current="$(date +%Y)"
  while [ "$year" -lt "$current" ]; do
    run bdns-sync sync "$entity" --since "$year-01-01" --until "$year-12-31"
    year=$((year + 1))
  done
  run bdns-sync sync "$entity" --since "$current-01-01"
}

# entity                       earliest reg-date worth requesting (see README)
backfill concesiones_busqueda        2020   # ~4y retention
backfill partidospoliticos_busqueda  2020   # tracks concesiones
backfill ayudasestado_busqueda       2015   # ~10y retention
backfill minimis_busqueda            2015   # ~10y retention
backfill convocatorias_busqueda      2013   # back to portal start
backfill convocatorias               2013   # back to portal start
