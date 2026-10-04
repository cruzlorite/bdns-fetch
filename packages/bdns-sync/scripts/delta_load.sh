#!/usr/bin/env bash
#
# Daily sync, kept for crontabs and images that call this script. The
# cadence and the failure handling now live in `bdns-sync delta`, where
# they are tested; see docs/guides/scheduling.md.
#
#   0 2 * * * BDNS_SYNC_TARGET_URL=bigquery://project/dataset /path/to/scripts/delta_load.sh
set -euo pipefail
: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"
exec bdns-sync delta "$@"
