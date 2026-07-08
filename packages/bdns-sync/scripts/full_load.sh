#!/usr/bin/env bash
#
# One-time bootstrap of a fresh target: every full-replace catalog, then
# the deep historical backfill of the reg-date incremental endpoints.
# bdns-sync itself is a pure primitive with no idea how far back each
# endpoint's data goes, so -- like delta_load.sh owns the cadence -- this
# script owns the earliest dates. It calls `bdns-sync sync <entity> --since
# <date>`, which syncs [since, yesterday] chunked into 7-day pieces (the same
# machinery the daily/weekly/monthly/annual windows use).
#
#   BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/full_load.sh
#
# Run once to bootstrap a fresh target, then let delta_load.sh keep it
# current. It's safe to re-run: SCD2 is idempotent, an already-synced record
# is just touched, not duplicated.
#
# The per-entity SINCE dates below are floors, not exact firsts: the API
# only retains a bounded history (measured live, see README "Carga histórica
# / Historical load"), and querying earlier just returns empty weeks cheaply.
# A single conservative floor (2013-01-01, roughly when the portal started)
# would also work; per-entity floors just avoid a pile of empty calls for the
# short-retention endpoints. Widen any SINCE if you want to be extra safe.
set -euo pipefail

: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"

echo "=== full-replace catalogs ==="
for entity in $(bdns-sync list --kind full); do
  echo ">>> $entity"
  bdns-sync sync "$entity"
done

echo "=== historical backfills ==="
# entity                       earliest reg-date worth requesting (see README)
backfill() { echo ">>> backfill $1 --since $2"; bdns-sync sync "$1" --since "$2"; }

backfill concesiones_busqueda        2020-01-01   # ~4y retention
backfill partidospoliticos_busqueda  2020-01-01   # tracks concesiones
backfill ayudasestado_busqueda       2015-01-01   # ~10y retention
backfill minimis_busqueda            2015-01-01   # ~10y retention
backfill convocatorias_busqueda      2013-01-01   # back to portal start
backfill convocatorias               2013-01-01   # back to portal start
