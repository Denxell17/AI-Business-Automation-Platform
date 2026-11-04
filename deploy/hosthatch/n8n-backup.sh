#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

# Explicit selectors live in n8n_backup_state.py:
# standalone: com.docker.compose.project=n8n, com.docker.compose.service=n8n
# public RAG: project=abap-public-rag-production, service=public-rag-n8n
readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
readonly STATE_HELPER="${ABAP_N8N_STATE_HELPER:-/usr/local/lib/abap/n8n_backup_state.py}"
readonly STAGING_PARENT="/var/backups/n8n"
readonly RUN_PARENT="$STAGING_PARENT/runs"
[[ "$EUID" -eq 0 ]] || { printf 'ERROR: root is required.\n' >&2; exit 1; }
[[ -r "$OPERATIONS_LIB" && -r "$STATE_HELPER" ]] || { printf 'ERROR: backup dependencies unavailable.\n' >&2; exit 1; }
source "$OPERATIONS_LIB"
operations_load_config
operations_configure_restic
for command_name in docker flock install python3 restic stat du readlink; do
  operations_require_command "$command_name"
done
# Acquire the existing shared lock BEFORE staging or interacting with backup state.
exec 9>/run/lock/abap-production-backup.lock
flock -n 9 || { operations_fail "Another production backup operation is running."; exit 1; }
if [[ -e "$STAGING_PARENT" || -L "$STAGING_PARENT" ]]; then
  [[ -d "$STAGING_PARENT" && ! -L "$STAGING_PARENT" && "$(stat -c %u "$STAGING_PARENT")" == 0 && "$(stat -c %a "$STAGING_PARENT")" == 700 ]] || {
    operations_fail "Protected staging parent failed validation."; exit 1;
  }
else
  install -d -o root -g root -m 0700 "$STAGING_PARENT"
fi
[[ "$(readlink -f -- "$STAGING_PARENT")" == "$STAGING_PARENT" ]] || { operations_fail "Staging parent is not canonical."; exit 1; }
# The earlier one-off /staging capture stays protected and is never reused.
if [[ ! -e "$RUN_PARENT" && ! -L "$RUN_PARENT" ]]; then
  install -d -o root -g root -m 0700 "$RUN_PARENT"
fi
[[ -d "$RUN_PARENT" && ! -L "$RUN_PARENT" && "$(readlink -f -- "$RUN_PARENT")" == "$RUN_PARENT" &&
   "$(stat -c %u "$RUN_PARENT")" == 0 && "$(stat -c %a "$RUN_PARENT")" == 700 ]] || {
  operations_fail "Protected run parent failed validation."; exit 1;
}
readonly run_tag="run-$(python3 -I -c 'import uuid;print(uuid.uuid4().hex)')"
readonly STAGING_DIRECTORY="$RUN_PARENT/$run_tag"
python3 -I -B "$STATE_HELPER" check
current_raw_bytes="$(operations_restic_raw_bytes)"
(( current_raw_bytes < ABAP_RESTIC_CRITICAL_BYTES )) || { operations_fail "Repository storage threshold reached."; exit 1; }
permitted_bytes="$(operations_permitted_staging_bytes "$STAGING_PARENT")"
(( permitted_bytes >= 2097152 )) || { operations_fail "Insufficient protected staging headroom."; exit 1; }
python3 -I -B "$STATE_HELPER" create-run --bundle "$STAGING_DIRECTORY" --run-id "$run_tag"
backup_complete=false
finish() {
  local status=$?
  if (( status == 0 )) && [[ "$backup_complete" == true ]]; then
    python3 -I -B "$STATE_HELPER" cleanup --bundle "$STAGING_DIRECTORY" --run-id "$run_tag" || status=1
  fi
  if (( status == 0 )); then
    operations_heartbeat heartbeat_n8n_backup_url
  else
    printf 'ERROR: backup incomplete; any protected staging is retained for review.\n' >&2
    operations_heartbeat heartbeat_n8n_backup_url /fail
  fi
  exit "$status"
}
trap finish EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
# A strict per-instance cap preserves the combined existing staging budget.
per_instance_bytes=$(( (permitted_bytes - 1048576) / 2 ))
for target in standalone public-rag-production; do
  python3 -I -B "$STATE_HELPER" capture --target "$target" \
    --bundle "$STAGING_DIRECTORY/$target" --limit-bytes "$per_instance_bytes"
done
staged_bytes="$(du -sb "$STAGING_DIRECTORY" | awk '{print $1}')"
operations_require_uint staged_bytes "$staged_bytes"
operations_require_local_headroom "$STAGING_PARENT" "$staged_bytes" 'Encrypted backup'
projected_bytes=$(( current_raw_bytes + staged_bytes + ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES ))
(( projected_bytes < ABAP_RESTIC_CRITICAL_BYTES )) || { operations_fail "Repository growth threshold would be exceeded."; exit 1; }
for target in standalone public-rag-production; do
  if [[ "$target" == standalone ]]; then
    host="${ABAP_RESTIC_HOST}-n8n"
  else
    host="${ABAP_RESTIC_HOST}-n8n-public-rag-production"
  fi
  # Restic encryption/repository/credentials remain the established operations settings.
  restic backup --host "$host" --one-file-system --tag n8n-production \
    --tag "$target" --tag automated --tag "$run_tag" "$STAGING_DIRECTORY/$target" \
    >/dev/null 2>/dev/null || { operations_fail "Encrypted snapshot failed; existing snapshots untouched."; exit 1; }
  snapshot_id="$(restic snapshots --host "$host" --tag "$run_tag" --json 2>/dev/null | python3 -I -c '
import json,re,sys
rows=json.load(sys.stdin)
if len(rows)!=1 or not re.fullmatch("[0-9a-f]{64}",rows[0].get("id","")): raise SystemExit(1)
print(rows[0]["id"])
')"
  # Verify that database, persistent key configuration and recovery manifest were included.
  restic ls --json "$snapshot_id" 2>/dev/null | python3 -I -c '
import json,sys
prefix=sys.argv[1]
required={prefix+"/capture.json",prefix+"/data/database.sqlite",prefix+"/data/config",prefix+"/runtime.json"}
found=set()
for line in sys.stdin:
 item=json.loads(line)
 if item.get("type")=="file": found.add(item.get("path"))
if not required <= found: raise SystemExit(1)
' "$STAGING_DIRECTORY/$target"
  printf 'N8N_SNAPSHOT_VERIFIED: target=%s id=%s\n' "$target" "$snapshot_id"
done
# Deliberately no forget/prune: keep existing 14/8/12 policy recorded in captures.
# Retention application is a separate approved operation, never part of this repair run.
python3 -I -B "$STATE_HELPER" check
# Reuse the conservative pre-write growth bound under the shared backup lock.
# Avoid a second full-repository metadata scan after two successful snapshots.
operations_report_restic_budget "$projected_bytes"
backup_complete=true
printf 'N8N_BACKUP_OK: both production targets captured; no containers stopped or started.\n'
