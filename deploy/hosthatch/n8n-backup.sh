#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
readonly N8N_VOLUME_PATH="/var/lib/docker/volumes/n8n_n8n_data/_data"
readonly STAGING_PARENT="/var/backups/n8n"
readonly STAGING_DIRECTORY="$STAGING_PARENT/staging"
readonly SHARED_LOCK="/run/lock/abap-production-backup.lock"

[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
# shellcheck source=abap-operations-lib.sh
source "$OPERATIONS_LIB"
operations_load_config
operations_configure_restic
readonly N8N_RESTIC_HOST="${ABAP_RESTIC_HOST}-n8n"

[[ "$EUID" -eq 0 ]] || { operations_fail "The n8n backup must run as root."; exit 1; }
for command_name in docker flock install python3 readlink restic sha256sum stat; do
  operations_require_command "$command_name"
done
[[ -d "$N8N_VOLUME_PATH" && ! -L "$N8N_VOLUME_PATH" ]] || {
  operations_fail "The expected n8n data volume is unavailable."
  exit 1
}
[[ "$(readlink -f -- "$N8N_VOLUME_PATH")" == "$N8N_VOLUME_PATH" ]] || {
  operations_fail "The n8n data volume resolves outside its approved path."
  exit 1
}

mapfile -t n8n_containers < <(
  docker ps --filter label=com.docker.compose.service=n8n --format '{{.ID}}'
)
(( ${#n8n_containers[@]} == 1 )) || {
  operations_fail "Exactly one running Compose n8n service is required."
  exit 1
}
readonly n8n_container="${n8n_containers[0]}"

# Require the live environment key (when present) to match the key in the
# protected n8n config that is included in the volume snapshot. No key value is
# written or printed.
python3 -c '
import json, pathlib, sys
inspection = json.load(sys.stdin)[0]
config_path = pathlib.Path(sys.argv[1])
config = json.loads(config_path.read_text(encoding="utf-8"))
stored = config.get("encryptionKey")
if not isinstance(stored, str) or not stored:
    raise SystemExit("ERROR: n8n config has no usable encryption key.")
configured = None
for item in inspection.get("Config", {}).get("Env", []):
    if item.startswith("N8N_ENCRYPTION_KEY="):
        configured = item.split("=", 1)[1]
        break
if configured is not None and configured != stored:
    raise SystemExit("ERROR: live and stored n8n encryption keys do not match.")
' "$N8N_VOLUME_PATH/config" < <(docker inspect "$n8n_container")

install -d -o root -g root -m 0700 "$STAGING_PARENT" "$STAGING_DIRECTORY"
find "$STAGING_DIRECTORY" -xdev -mindepth 1 -delete
install -d -o root -g root -m 0700 "$ABAP_RESTIC_CACHE_DIR"
exec 9>"$SHARED_LOCK"
flock -n 9 || { operations_fail "An ABAP or n8n backup operation is running."; exit 1; }

backup_complete=false
container_stopped=false
run_tag="run-$(date -u +'%Y%m%dT%H%M%SZ')"

finish_backup() {
  local status=$?
  if [[ "$container_stopped" == true ]]; then
    if ! docker start "$n8n_container" >/dev/null; then
      printf 'CRITICAL: n8n could not be restarted.\n' >&2
      status=1
    fi
  fi
  find "$STAGING_DIRECTORY" -xdev -mindepth 1 -delete 2>/dev/null || status=1
  if (( status == 0 )) && [[ "$backup_complete" == true ]]; then
    operations_heartbeat heartbeat_n8n_backup_url
  else
    operations_heartbeat heartbeat_n8n_backup_url /fail
  fi
  exit "$status"
}
trap finish_backup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

current_raw_bytes="$(operations_restic_raw_bytes)"
(( current_raw_bytes < ABAP_RESTIC_CRITICAL_BYTES )) || {
  operations_fail "Restic storage is already at the critical threshold."
  exit 1
}

image_reference="$(docker inspect --format '{{.Config.Image}}' "$n8n_container")"
image_id="$(docker inspect --format '{{.Image}}' "$n8n_container")"
cat >"$STAGING_DIRECTORY/RECOVERY-MANIFEST.txt" <<EOF
format=abap-n8n-production-backup-v1
captured_at_utc=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
container_image=$image_reference
container_image_id=$image_id
volume=n8n_n8n_data
database=sqlite
restore_rule=restore-only-to-isolated-resources
EOF
sha256sum "$STAGING_DIRECTORY/RECOVERY-MANIFEST.txt" >"$STAGING_DIRECTORY/SHA256SUMS"

container_stopped=true
docker stop --time 30 "$n8n_container" >/dev/null

restic backup \
  --host "$N8N_RESTIC_HOST" \
  --one-file-system \
  --tag n8n-production \
  --tag automated \
  --tag "$run_tag" \
  "$N8N_VOLUME_PATH" \
  "$STAGING_DIRECTORY"

restic snapshots --host "$N8N_RESTIC_HOST" --tag "$run_tag" --json \
  | python3 -c '
import json, sys
snapshots = json.load(sys.stdin)
if len(snapshots) != 1:
    raise SystemExit(1)
tags = set(snapshots[0].get("tags") or [])
raise SystemExit(0 if {"n8n-production", sys.argv[1]} <= tags else 1)
' "$run_tag"

docker start "$n8n_container" >/dev/null
container_stopped=false
for _ in $(seq 1 30); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$n8n_container")"
  [[ "$state" == healthy || "$state" == running ]] && break
  [[ "$state" == unhealthy || "$state" == exited || "$state" == dead ]] && break
  sleep 2
done
[[ "$state" == healthy || "$state" == running ]] || {
  operations_fail "n8n did not return to the running state."
  exit 1
}

restic forget \
  --host "$N8N_RESTIC_HOST" \
  --tag n8n-production \
  --group-by host,paths \
  --keep-daily 14 \
  --keep-weekly 8 \
  --keep-monthly 12

final_raw_bytes="$(operations_restic_raw_bytes)"
operations_report_restic_budget "$final_raw_bytes"
backup_complete=true
printf 'N8N_BACKUP_OK: encrypted snapshot %s confirmed.\n' "$run_tag"
