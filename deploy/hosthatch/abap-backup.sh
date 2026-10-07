#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
# shellcheck source=abap-operations-lib.sh
source "$OPERATIONS_LIB"

operations_load_config

readonly STAGING_PARENT="/var/backups/abap"
readonly STAGING_DIRECTORY="$STAGING_PARENT/staging"
readonly EXPECTED_INVOICE_DIRECTORY="/var/lib/docker/volumes/abap-deploy_invoice_documents/_data"
readonly EXPECTED_ACTIVITY_DIRECTORY="/var/lib/docker/volumes/abap-deploy_activity_logs/_data"
readonly EXPECTED_DATABASE_DIRECTORY="/var/lib/docker/volumes/abap-deploy_database_data/_data"
readonly LOCK_FILE="/run/lock/abap-production-backup.lock"

backup_kind="automated"
if (( $# > 1 )); then
  operations_fail "Usage: abap-backup.sh [--release]"
  exit 1
elif (( $# == 1 )); then
  [[ "$1" == "--release" ]] || { operations_fail "Unknown argument: $1"; exit 1; }
  backup_kind="release"
fi

[[ "$EUID" -eq 0 ]] || { operations_fail "The production backup must run as root."; exit 1; }
[[ "$ABAP_INVOICE_DOCUMENTS_DIR" == "$EXPECTED_INVOICE_DIRECTORY" ]] || {
  operations_fail "The invoice backup source must be the authoritative abap-deploy volume."
  exit 1
}
[[ "$ABAP_ACTIVITY_LOGS_DIR" == "$EXPECTED_ACTIVITY_DIRECTORY" ]] || {
  operations_fail "The activity-log source must be the authoritative abap-deploy volume."
  exit 1
}
[[ "$ABAP_DATABASE_DATA_DIR" == "$EXPECTED_DATABASE_DIRECTORY" ]] || {
  operations_fail "The protected database-volume path is not the expected abap-deploy volume."
  exit 1
}
[[ "$ABAP_INVOICE_DOCUMENTS_DIR" != "$ABAP_DATABASE_DATA_DIR" ]] || {
  operations_fail "Refusing to treat the live PostgreSQL volume as a file-backup source."
  exit 1
}

for command_name in awk cp curl date df docker du find findmnt flock git head hostname install readlink restic rmdir sed sha256sum sort stat xargs; do
  operations_require_command "$command_name"
done

operations_configure_restic

staging_path_is_unmounted() {
  local approved_path="$1"
  local -a mount_targets=()
  # Inspect PID 1's host mount namespace so systemd's own ReadWritePaths bind
  # mounts inside this hardened service are not mistaken for host mounts.
  local mount_listing
  mount_listing="$(findmnt -N 1 -rn -o TARGET)" || {
    operations_fail "Host mount information could not be inspected safely."
    return 1
  }
  mapfile -t mount_targets <<<"$mount_listing"

  local mount_target
  for mount_target in "${mount_targets[@]}"; do
    if [[ "$mount_target" == "$approved_path" || "$mount_target" == "$approved_path/"* ]]; then
      operations_fail "Refusing staging access because a mount exists at or below $approved_path."
      return 1
    fi
  done
}

validate_staging_directory() {
  local path="$1"
  local expected_path="$2"
  local label="$3"

  [[ -d "$path" && ! -L "$path" ]] || \
    { operations_fail "$label must be a real directory: $expected_path"; return 1; }
  [[ "$(readlink -f -- "$path")" == "$expected_path" ]] || \
    { operations_fail "$label resolves outside its approved path."; return 1; }

  local owner_id
  local mode
  owner_id="$(stat -c '%u' -- "$path")"
  mode="$(stat -c '%a' -- "$path")"
  [[ "$owner_id" == 0 ]] || \
    { operations_fail "$label must be owned by root."; return 1; }
  (( (8#$mode & 8#077) == 0 )) || \
    { operations_fail "$label must not be group- or world-accessible."; return 1; }
  staging_path_is_unmounted "$expected_path"
}

if [[ -e "$STAGING_PARENT" || -L "$STAGING_PARENT" ]]; then
  validate_staging_directory "$STAGING_PARENT" "$STAGING_PARENT" "Staging parent"
else
  install -d -o root -g root -m 0700 "$STAGING_PARENT"
fi
validate_staging_directory "$STAGING_PARENT" "$STAGING_PARENT" "Staging parent"
install -d -o root -g root -m 0700 "$ABAP_RESTIC_CACHE_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || { operations_fail "Another ABAP backup or maintenance operation is running."; exit 1; }

backup_completed=false
snapshot_confirmed=false

safe_cleanup() {
  [[ "$STAGING_PARENT" == "/var/backups/abap" ]] || return 1
  [[ "$STAGING_DIRECTORY" == "/var/backups/abap/staging" ]] || return 1
  validate_staging_directory "$STAGING_PARENT" "/var/backups/abap" "Staging parent" || return 1
  if [[ -e "$STAGING_DIRECTORY" || -L "$STAGING_DIRECTORY" ]]; then
    validate_staging_directory \
      "$STAGING_DIRECTORY" "/var/backups/abap/staging" "Staging directory" || return 1
    find "$STAGING_DIRECTORY" -xdev -mindepth 1 -delete || return 1
    rmdir "$STAGING_DIRECTORY" || return 1
  fi
}

finish_backup() {
  local status=$?
  local cleanup_status=0
  if ! safe_cleanup; then
    cleanup_status=1
    printf 'CRITICAL: root-only plaintext staging could not be completely cleaned.\n' >&2
  fi
  if (( status == 0 && cleanup_status != 0 )); then
    status=1
  fi
  if (( status == 0 )) && [[ "$backup_completed" == true && "$snapshot_confirmed" == true ]]; then
    operations_heartbeat heartbeat_backup_url
  else
    operations_heartbeat heartbeat_backup_url /fail
  fi
  exit "$status"
}
trap finish_backup EXIT

safe_cleanup || { operations_fail "Existing plaintext staging could not be cleaned safely."; exit 1; }
install -d -o root -g root -m 0700 \
  "$STAGING_DIRECTORY" \
  "$STAGING_DIRECTORY/config" \
  "$STAGING_DIRECTORY/activity-logs"
validate_staging_directory \
  "$STAGING_DIRECTORY" "/var/backups/abap/staging" "Staging directory"

[[ -d "$ABAP_INVOICE_DOCUMENTS_DIR" ]] || {
  operations_fail "Invoice-document volume directory is unavailable."
  exit 1
}
[[ -d "$ABAP_ACTIVITY_LOGS_DIR" ]] || {
  operations_fail "Activity-log volume directory is unavailable."
  exit 1
}
[[ "$(readlink -f "$ABAP_INVOICE_DOCUMENTS_DIR")" == "$EXPECTED_INVOICE_DIRECTORY" ]] || {
  operations_fail "Invoice-document source resolves outside its approved volume path."
  exit 1
}
[[ "$(readlink -f "$ABAP_ACTIVITY_LOGS_DIR")" == "$EXPECTED_ACTIVITY_DIRECTORY" ]] || {
  operations_fail "Activity-log source resolves outside its approved volume path."
  exit 1
}
[[ -r "$ABAP_ENV_FILE" ]] || {
  operations_fail "Production environment file is unavailable."
  exit 1
}

readonly dump_file="$STAGING_DIRECTORY/database.dump"
activity_source_bytes="$(du -sb "$ABAP_ACTIVITY_LOGS_DIR" | awk '{print $1}')"
operations_require_uint activity_source_bytes "$activity_source_bytes"
readonly staging_reserve_bytes=10000000
permitted_staging_bytes="$(operations_permitted_staging_bytes "$STAGING_DIRECTORY")" || {
  operations_fail "PostgreSQL dump was not started because local backup capacity is unsafe."
  exit 1
}
operations_require_uint permitted_staging_bytes "$permitted_staging_bytes"
if (( activity_source_bytes + staging_reserve_bytes >= permitted_staging_bytes )); then
  operations_fail "Activity logs leave no safe room for a bounded PostgreSQL dump."
  exit 1
fi

# This local-capacity gate intentionally runs before any Restic command can
# populate its cache and before pg_dump can write plaintext staging data.
current_raw_bytes="$(operations_restic_raw_bytes)" || {
  operations_fail "Unable to measure the initialized Restic repository before backup."
  exit 1
}
if (( current_raw_bytes >= ABAP_RESTIC_CRITICAL_BYTES )); then
  operations_fail "Backup blocked: Restic referenced data is already at or above the 8.5 GB threshold."
  exit 1
fi
operations_report_restic_budget "$current_raw_bytes" || true

# Restic stats may populate its cache, so recompute the safe staging allowance
# immediately before pg_dump rather than relying on the earlier measurement.
permitted_staging_bytes="$(operations_permitted_staging_bytes "$STAGING_DIRECTORY")" || {
  operations_fail "PostgreSQL dump was not started because local capacity changed after the repository check."
  exit 1
}
operations_require_uint permitted_staging_bytes "$permitted_staging_bytes"
activity_source_bytes="$(du -sb "$ABAP_ACTIVITY_LOGS_DIR" | awk '{print $1}')"
operations_require_uint activity_source_bytes "$activity_source_bytes"
if (( activity_source_bytes + staging_reserve_bytes >= permitted_staging_bytes )); then
  operations_fail "Activity logs leave no safe room for a bounded PostgreSQL dump."
  exit 1
fi
readonly dump_limit_bytes=$((
  permitted_staging_bytes - activity_source_bytes - staging_reserve_bytes
))
readonly maximum_dump_bytes=$(( dump_limit_bytes + 1 ))

compose=(
  docker compose
  --env-file "$ABAP_ENV_FILE"
  -f "$ABAP_COMPOSE_BASE_FILE"
  -f "$ABAP_COMPOSE_OVERLAY_FILE"
)

set +e
"${compose[@]}" exec -T database \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  | head -c "$maximum_dump_bytes" > "$dump_file"
pipeline_status=("${PIPESTATUS[@]}")
set -e

dump_bytes="$(stat -c '%s' "$dump_file")"
if (( dump_bytes > dump_limit_bytes )); then
  operations_fail "PostgreSQL dump exceeded the configured plaintext staging limit."
  exit 1
fi
if (( pipeline_status[0] != 0 || pipeline_status[1] != 0 )); then
  operations_fail "PostgreSQL pg_dump did not complete successfully."
  exit 1
fi
(( dump_bytes > 0 )) || { operations_fail "PostgreSQL dump is empty."; exit 1; }

"${compose[@]}" exec -T database pg_restore --list < "$dump_file" >/dev/null || {
  operations_fail "pg_restore could not read the staged custom-format dump."
  exit 1
}

# Activity files are copied on a bounded, best-effort basis so Restic reads a
# stable staged copy instead of the application's long-lived log handle.
activity_source_bytes="$(du -sb "$ABAP_ACTIVITY_LOGS_DIR" | awk '{print $1}')"
operations_require_uint activity_source_bytes "$activity_source_bytes"
operations_require_local_headroom \
  "$STAGING_DIRECTORY" \
  "$(( activity_source_bytes + ABAP_RESTIC_CACHE_OVERHEAD_BYTES ))" \
  "Activity-log staging" || exit 1
cp -a -- "$ABAP_ACTIVITY_LOGS_DIR/." "$STAGING_DIRECTORY/activity-logs/"
install -m 0600 "$ABAP_ENV_FILE" "$STAGING_DIRECTORY/config/production.env"

copy_optional_config() {
  local source_path="$1"
  local destination_name="$2"
  if [[ -f "$source_path" ]]; then
    install -m 0600 "$source_path" "$STAGING_DIRECTORY/config/$destination_name"
  fi
}

copy_optional_config /etc/caddy/Caddyfile Caddyfile
copy_optional_config /etc/logrotate.d/abap-activity abap-activity-logrotate.conf
copy_optional_config /etc/docker/daemon.json docker-daemon.json
copy_optional_config /etc/abap/operations.conf operations.conf

for unit_name in \
  abap-backup.service abap-backup.timer \
  abap-backup-maintenance.service abap-backup-maintenance.timer \
  abap-backup-full-check.service abap-backup-full-check.timer \
  abap-operations-check.service abap-operations-check.timer; do
  copy_optional_config "/etc/systemd/system/$unit_name" "$unit_name"
done

captured_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
readonly captured_at
run_tag="run-$(date -u +'%Y%m%dT%H%M%SZ')"
readonly run_tag
git_commit="$(git -c safe.directory="$ABAP_APP_DIR" -C "$ABAP_APP_DIR" rev-parse HEAD)"
readonly git_commit
host_name="$(hostname -f 2>/dev/null || hostname)"
readonly host_name
postgres_version="$("${compose[@]}" exec -T database postgres --version)"
readonly postgres_version

service_image() {
  local service_name="$1"
  local container_id
  container_id="$("${compose[@]}" ps -a -q "$service_name" | head -n 1)"
  [[ -n "$container_id" ]] || { printf 'unavailable\n'; return; }
  docker inspect --format '{{.Config.Image}}' "$container_id"
}

database_image="$(service_image database)"
readonly database_image
web_image="$(service_image web)"
readonly web_image
worker_image="$(service_image worker)"
readonly worker_image
restic_version="$(restic version)"
readonly restic_version
docker_version="$(docker --version)"
readonly docker_version

{
  printf 'format=abap-production-backup-v1\n'
  printf 'captured_at_utc=%s\n' "$captured_at"
  printf 'restic_host=%s\n' "$ABAP_RESTIC_HOST"
  printf 'source_host=%s\n' "$host_name"
  printf 'git_commit=%s\n' "$git_commit"
  printf 'compose_project=abap-deploy\n'
  printf 'postgres_version=%s\n' "$postgres_version"
  printf 'database_image=%s\n' "$database_image"
  printf 'web_image=%s\n' "$web_image"
  printf 'worker_image=%s\n' "$worker_image"
  printf 'restic_version=%s\n' "$restic_version"
  printf 'docker_version=%s\n' "$docker_version"
  printf 'backup_kind=%s\n' "$backup_kind"
  printf 'postgresql_dump=database.dump\n'
  printf 'postgresql_dump_bytes=%s\n' "$dump_bytes"
  printf 'invoice_documents_source=%s\n' "$ABAP_INVOICE_DOCUMENTS_DIR"
  printf 'activity_logs_snapshot=activity-logs\n'
  printf 'configuration_snapshot=config\n'
  printf 'excluded_live_database_volume=%s\n' "$ABAP_DATABASE_DATA_DIR"
  printf 'excluded_paths=docker-images,docker-build-cache,container-layers,/app/exports,caddy-pki,unrelated-host-files\n'
  printf 'restore_rule=restore-only-to-isolated-resources\n'
} > "$STAGING_DIRECTORY/RECOVERY-MANIFEST.txt"

(
  cd "$STAGING_DIRECTORY"
  sha256sum database.dump RECOVERY-MANIFEST.txt > SHA256SUMS
  find config -type f ! -name production.env -print0 \
    | sort -z \
    | xargs -0 -r sha256sum >> SHA256SUMS
)

(
  cd "$ABAP_INVOICE_DOCUMENTS_DIR"
  find . -xdev -type f -print0 \
    | sort -z \
    | xargs -0 -r sha256sum
) > "$STAGING_DIRECTORY/INVOICE-DOCUMENTS.sha256"

staging_bytes="$(du -sb "$STAGING_DIRECTORY" | awk '{print $1}')"
invoice_bytes="$(du -sb "$ABAP_INVOICE_DOCUMENTS_DIR" | awk '{print $1}')"
operations_require_uint staging_bytes "$staging_bytes"
operations_require_uint invoice_bytes "$invoice_bytes"
if (( staging_bytes > permitted_staging_bytes )); then
  operations_fail "Plaintext staging exceeded the permitted local-capacity bound."
  exit 1
fi

operations_require_local_headroom \
  "$STAGING_DIRECTORY" \
  "$ABAP_RESTIC_CACHE_OVERHEAD_BYTES" \
  "Restic backup" || exit 1

projected_raw_bytes=$((
  current_raw_bytes + staging_bytes + invoice_bytes + ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES
))
printf 'RESTIC_PREFLIGHT_BYTES=current:%s source:%s overhead:%s projected:%s\n' \
  "$current_raw_bytes" \
  "$(( staging_bytes + invoice_bytes ))" \
  "$ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES" \
  "$projected_raw_bytes"
if (( projected_raw_bytes >= ABAP_RESTIC_CRITICAL_BYTES )); then
  operations_fail "Backup blocked before upload: conservative projection reaches the 8.5 GB threshold."
  exit 1
fi
if (( projected_raw_bytes >= ABAP_RESTIC_WARNING_BYTES )); then
  printf 'WARNING: conservative preflight projection reaches the 7 GB early-warning threshold.\n' >&2
fi

backup_tags=(--tag abap-production --tag "$backup_kind" --tag "$run_tag")

# This is the complete backup source list. Do not broaden it to /var/lib/docker,
# /opt, /etc, /, or the live PostgreSQL data directory.
restic backup \
  --host "$ABAP_RESTIC_HOST" \
  --one-file-system \
  "${backup_tags[@]}" \
  "$STAGING_DIRECTORY" \
  "$ABAP_INVOICE_DOCUMENTS_DIR"

snapshot_listing="$(restic snapshots --host "$ABAP_RESTIC_HOST" --tag "$run_tag" --compact)"
grep -Fq "$run_tag" <<<"$snapshot_listing" || {
  operations_fail "The new encrypted Restic snapshot could not be confirmed."
  exit 1
}
snapshot_confirmed=true

final_raw_bytes="$(operations_restic_raw_bytes)" || {
  operations_fail "The snapshot exists, but post-backup repository-size measurement failed."
  exit 1
}
budget_status=0
operations_report_restic_budget "$final_raw_bytes" || budget_status=$?
if (( budget_status != 0 )); then
  if (( budget_status == 10 )); then
    operations_fail "The snapshot is confirmed, but repository growth requires early action."
  else
    operations_fail "The snapshot is confirmed, but repository growth is critical."
  fi
  exit 2
fi

backup_completed=true
printf 'BACKUP_OK: encrypted Restic snapshot %s confirmed.\n' "$run_tag"
