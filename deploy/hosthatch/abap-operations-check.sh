#!/usr/bin/env bash
set -Eeuo pipefail

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
# shellcheck source=abap-operations-lib.sh
source "$OPERATIONS_LIB"

operations_load_config
[[ "$EUID" -eq 0 ]] || { operations_fail "Operations checks must run as root."; exit 1; }

for command_name in awk curl date df docker find flock free openssl rm sed ss stat systemctl; do
  operations_require_command "$command_name"
done

warning_count=0
critical_count=0

record_warning() {
  warning_count=$(( warning_count + 1 ))
  printf 'WARNING: %s\n' "$*" >&2
}

record_critical() {
  critical_count=$(( critical_count + 1 ))
  printf 'CRITICAL: %s\n' "$*" >&2
}

finish_checks() {
  local status=$?
  if (( status == 0 )); then
    operations_heartbeat heartbeat_operations_url
  else
    operations_heartbeat heartbeat_operations_url /fail
  fi
  exit "$status"
}
trap finish_checks EXIT

exec 9>/run/lock/abap-production-operations-check.lock
flock -n 9 || { operations_fail "The previous operations check is still running."; exit 1; }

check_percent_threshold() {
  local label="$1"
  local percent="$2"
  local warning="$3"
  local critical="$4"
  if (( percent >= critical )); then
    record_critical "$label is ${percent}% (critical at ${critical}%)."
  elif (( percent >= warning )); then
    record_warning "$label is ${percent}% (warning at ${warning}%)."
  else
    printf 'OK: %s is %s%%.\n' "$label" "$percent"
  fi
}

declare -A checked_devices=()
for monitored_path in / "$ABAP_DOCKER_ROOT" /var/backups/abap; do
  if [[ ! -e "$monitored_path" ]]; then
    record_critical "Monitored path is unavailable: $monitored_path"
    continue
  fi
  device="$(df -P "$monitored_path" | awk 'NR==2 {print $1}')"
  [[ -n "${checked_devices[$device]:-}" ]] && continue
  checked_devices[$device]=1

  disk_percent="$(df -P "$monitored_path" | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
  inode_percent="$(df -Pi "$monitored_path" | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
  if [[ "$disk_percent" =~ ^[0-9]+$ ]]; then
    check_percent_threshold "Disk usage for $device" "$disk_percent" \
      "$ABAP_DISK_WARNING_PERCENT" "$ABAP_DISK_CRITICAL_PERCENT"
  else
    record_critical "Disk usage could not be parsed for $monitored_path."
  fi
  if [[ "$inode_percent" =~ ^[0-9]+$ ]]; then
    check_percent_threshold "Inode usage for $device" "$inode_percent" \
      "$ABAP_DISK_WARNING_PERCENT" "$ABAP_DISK_CRITICAL_PERCENT"
  else
    record_critical "Inode usage could not be parsed for $monitored_path."
  fi
done

if [[ -d /var/backups/abap/staging ]] && \
  [[ -n "$(find /var/backups/abap/staging -xdev -mindepth 1 -mmin +1440 -print -quit)" ]]; then
  record_critical "Plaintext backup staging contains data older than 24 hours."
else
  printf 'OK: no stale plaintext backup staging data was found.\n'
fi

swap_total="$(free -b | awk '$1 == "Swap:" {print $2}')"
swap_used="$(free -b | awk '$1 == "Swap:" {print $3}')"
if [[ "$swap_total" =~ ^[0-9]+$ && "$swap_used" =~ ^[0-9]+$ ]]; then
  if (( swap_total == 0 )); then
    swap_percent=0
  else
    swap_percent=$(( swap_used * 100 / swap_total ))
  fi

  swap_state_file="${RUNTIME_DIRECTORY:-/run/abap-operations}/swap-warning-runs"
  previous_runs=0
  [[ -f "$swap_state_file" ]] && previous_runs="$(<"$swap_state_file")"
  [[ "$previous_runs" =~ ^[0-9]+$ ]] || previous_runs=0

  if (( swap_percent >= ABAP_SWAP_CRITICAL_PERCENT )); then
    printf '%s\n' "$(( previous_runs + 1 ))" > "$swap_state_file"
    record_critical "Swap usage is ${swap_percent}%."
  elif (( swap_percent >= ABAP_SWAP_WARNING_PERCENT )); then
    current_runs=$(( previous_runs + 1 ))
    printf '%s\n' "$current_runs" > "$swap_state_file"
    if (( current_runs >= ABAP_SWAP_WARNING_RUNS )); then
      record_warning "Swap usage has remained at ${swap_percent}% for ${current_runs} checks."
    else
      printf 'OK: swap usage is %s%%; waiting for sustained-use threshold (%s/%s).\n' \
        "$swap_percent" "$current_runs" "$ABAP_SWAP_WARNING_RUNS"
    fi
  else
    printf '0\n' > "$swap_state_file"
    printf 'OK: swap usage is %s%%.\n' "$swap_percent"
  fi
else
  record_critical "Swap usage could not be parsed."
fi

for service_name in docker caddy; do
  if systemctl is-active --quiet "$service_name"; then
    printf 'OK: systemd service %s is active.\n' "$service_name"
  else
    record_critical "systemd service $service_name is not active."
  fi
done

for timer_name in \
  abap-backup.timer \
  abap-backup-maintenance.timer \
  abap-backup-full-check.timer \
  abap-operations-check.timer; do
  if systemctl is-enabled --quiet "$timer_name" && systemctl is-active --quiet "$timer_name"; then
    printf 'OK: systemd timer %s is enabled and active.\n' "$timer_name"
  else
    record_critical "systemd timer $timer_name is not enabled and active."
  fi
done

compose=(
  docker compose
  --env-file "$ABAP_ENV_FILE"
  -f "$ABAP_COMPOSE_BASE_FILE"
  -f "$ABAP_COMPOSE_OVERLAY_FILE"
)

container_id_for() {
  "${compose[@]}" ps -a -q "$1" | head -n 1
}

check_healthy_container() {
  local service_name="$1"
  local container_id
  container_id="$(container_id_for "$service_name")"
  if [[ -z "$container_id" ]]; then
    record_critical "Compose service $service_name has no container."
    return
  fi

  local state
  local health
  state="$(docker inspect --format '{{.State.Status}}' "$container_id")"
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id")"
  if [[ "$state" == running && "$health" == healthy ]]; then
    printf 'OK: Compose service %s is running and healthy.\n' "$service_name"
  else
    record_critical "Compose service $service_name state=$state health=$health."
  fi
}

for service_name in database web worker; do
  check_healthy_container "$service_name"
done

migrate_id="$(container_id_for migrate)"
if [[ -z "$migrate_id" ]]; then
  record_critical "Compose migration container is unavailable."
else
  migrate_state="$(docker inspect --format '{{.State.Status}}' "$migrate_id")"
  migrate_exit="$(docker inspect --format '{{.State.ExitCode}}' "$migrate_id")"
  if [[ "$migrate_state" == exited && "$migrate_exit" == 0 ]]; then
    printf 'OK: migration container exited successfully.\n'
  else
    record_critical "Migration container state=$migrate_state exit=$migrate_exit."
  fi
fi

if curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/health >/dev/null; then
  printf 'OK: local /health passed.\n'
else
  record_critical "Local /health failed."
fi
if curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/ready >/dev/null; then
  printf 'OK: local /ready passed.\n'
else
  record_critical "Local /ready failed."
fi

database_id="$(container_id_for database)"
web_id="$(container_id_for web)"
if [[ -n "$database_id" ]]; then
  database_bindings="$(docker inspect --format '{{range $port, $bindings := .NetworkSettings.Ports}}{{range $bindings}}{{$port}}={{.HostIp}}:{{.HostPort}}{{"\n"}}{{end}}{{end}}' "$database_id")"
  [[ -z "$database_bindings" ]] || record_critical "PostgreSQL has a published host port."
fi
if [[ -n "$web_id" ]]; then
  web_bindings="$(docker inspect --format '{{range $port, $bindings := .NetworkSettings.Ports}}{{range $bindings}}{{$port}}={{.HostIp}}:{{.HostPort}}{{"\n"}}{{end}}{{end}}' "$web_id")"
  if [[ "$web_bindings" == "8000/tcp=127.0.0.1:8000" ]]; then
    printf 'OK: ABAP web port remains loopback-only.\n'
  else
    record_critical "ABAP web binding is not exactly 127.0.0.1:8000."
  fi
fi

if ss -H -ltn | awk '$4 ~ /:5432$/ {found=1} END {exit !found}'; then
  record_critical "A host TCP listener exists on PostgreSQL port 5432."
else
  printf 'OK: no host TCP listener exists on port 5432.\n'
fi
public_8000="$(ss -H -ltn | awk '$4 ~ /:8000$/ && $4 != "127.0.0.1:8000" {print $4}')"
if [[ -n "$public_8000" ]]; then
  record_critical "A non-loopback host listener exists on ABAP port 8000."
else
  printf 'OK: no non-loopback listener exists on port 8000.\n'
fi

check_tls_endpoint() {
  local label="$1"
  local connect_target="$2"
  local certificate_file
  certificate_file="${RUNTIME_DIRECTORY:-/run/abap-operations}/${label}.pem"

  if ! openssl s_client \
    -connect "$connect_target" \
    -servername "$ABAP_TLS_HOST" \
    -verify_hostname "$ABAP_TLS_HOST" \
    -verify_return_error \
    </dev/null 2>/dev/null \
    | openssl x509 -outform PEM > "$certificate_file"; then
    rm -f -- "$certificate_file"
    record_critical "$label TLS certificate could not be retrieved and validated."
    return
  fi

  local critical_seconds=$(( ABAP_TLS_CRITICAL_DAYS * 86400 ))
  local warning_seconds=$(( ABAP_TLS_WARNING_DAYS * 86400 ))
  if ! openssl x509 -in "$certificate_file" -noout -checkend "$critical_seconds" >/dev/null; then
    record_critical "$label TLS certificate expires in less than ${ABAP_TLS_CRITICAL_DAYS} days."
  elif ! openssl x509 -in "$certificate_file" -noout -checkend "$warning_seconds" >/dev/null; then
    record_warning "$label TLS certificate expires in less than ${ABAP_TLS_WARNING_DAYS} days."
  else
    expiry="$(openssl x509 -in "$certificate_file" -noout -enddate | sed 's/^notAfter=//')"
    printf 'OK: %s TLS certificate expires %s.\n' "$label" "$expiry"
  fi
  rm -f -- "$certificate_file"
}

check_tls_endpoint public "$ABAP_TLS_HOST:443"
check_tls_endpoint origin "127.0.0.1:443"

if (( critical_count > 0 )); then
  printf 'OPERATIONS_CRITICAL: critical=%s warning=%s\n' "$critical_count" "$warning_count" >&2
  exit 1
fi
if (( warning_count > 0 )); then
  printf 'OPERATIONS_WARNING: warning=%s\n' "$warning_count" >&2
  exit 2
fi

printf 'OPERATIONS_OK: all local production checks passed.\n'
