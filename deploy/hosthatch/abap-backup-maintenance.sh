#!/usr/bin/env bash
set -Eeuo pipefail

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
# shellcheck source=abap-operations-lib.sh
source "$OPERATIONS_LIB"

operations_load_config
[[ "$EUID" -eq 0 ]] || { operations_fail "Backup maintenance must run as root."; exit 1; }

mode="${1:-weekly}"
[[ "$mode" == weekly || "$mode" == full-check || "$mode" == retention-dry-run ]] || {
  operations_fail "Usage: abap-backup-maintenance.sh [weekly|full-check|retention-dry-run]"
  exit 1
}

for command_name in curl flock install restic sed stat; do
  operations_require_command "$command_name"
done
operations_configure_restic
install -d -o root -g root -m 0700 "$ABAP_RESTIC_CACHE_DIR"

exec 9>/run/lock/abap-production-backup.lock
flock -n 9 || { operations_fail "Another ABAP backup or maintenance operation is running."; exit 1; }

maintenance_completed=false
heartbeat_credential=heartbeat_maintenance_url
[[ "$mode" == full-check ]] && heartbeat_credential=heartbeat_full_check_url
[[ "$mode" == retention-dry-run ]] && heartbeat_credential=""

finish_maintenance() {
  local status=$?
  if [[ -z "$heartbeat_credential" ]]; then
    :
  elif (( status == 0 )) && [[ "$maintenance_completed" == true ]]; then
    operations_heartbeat "$heartbeat_credential"
  else
    operations_heartbeat "$heartbeat_credential" /fail
  fi
  exit "$status"
}
trap finish_maintenance EXIT

retention_policy=(
  --host "$ABAP_RESTIC_HOST"
  --tag abap-production
  --group-by host,paths
  --keep-daily 14
  --keep-weekly 8
  --keep-monthly 12
  --keep-tag release
)

if [[ "$mode" == weekly ]]; then
  restic forget \
    "${retention_policy[@]}" \
    --prune
  restic check
elif [[ "$mode" == retention-dry-run ]]; then
  restic forget "${retention_policy[@]}" --dry-run
else
  restic check --read-data
fi

raw_bytes="$(operations_restic_raw_bytes)" || {
  operations_fail "Repository maintenance succeeded, but size measurement failed."
  exit 1
}
if ! operations_report_restic_budget "$raw_bytes"; then
  operations_fail "Repository maintenance completed, but storage growth requires attention."
  exit 2
fi

maintenance_completed=true
printf 'MAINTENANCE_OK: mode=%s\n' "$mode"
