#!/usr/bin/env bash
#
# Historical load, kept for anyone who calls this script. The history
# start of each entity now lives in the entity registry and the slicing in
# `bdns-sync backfill`; see docs/guides/backfill.md.
set -euo pipefail
: "${BDNS_SYNC_TARGET_URL:?set BDNS_SYNC_TARGET_URL to the target DB URL}"
exec bdns-sync backfill "$@"
