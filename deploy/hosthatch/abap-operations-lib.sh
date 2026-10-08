#!/usr/bin/env bash
set -Eeuo pipefail

ABAP_OPERATIONS_CONFIG_DEFAULT="/etc/abap/operations.conf"

operations_fail() {
  printf 'ERROR: %s\n' "$*" >&2
  return 1
}

operations_require_command() {
  command -v "$1" >/dev/null 2>&1 || operations_fail "Required command not found: $1"
}

operations_require_uint() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[0-9]+$ ]] || operations_fail "$name must be an unsigned integer."
}

operations_require_trusted_root_file() {
  local file_path="$1"
  local label="$2"

  [[ -f "$file_path" && ! -L "$file_path" ]] || {
    operations_fail "$label must be a regular file, not a symlink: $file_path"
    return 1
  }

  local owner_id
  local mode
  owner_id="$(stat -c '%u' -- "$file_path")"
  mode="$(stat -c '%a' -- "$file_path")"
  [[ "$owner_id" == 0 ]] || {
    operations_fail "$label must be owned by root."
    return 1
  }
  (( (8#$mode & 8#077) == 0 )) || {
    operations_fail "$label must not be group- or world-accessible."
    return 1
  }
}

operations_load_config() {
  local config_file="${ABAP_OPERATIONS_CONFIG:-$ABAP_OPERATIONS_CONFIG_DEFAULT}"
  [[ -r "$config_file" ]] || operations_fail "Operations configuration is not readable: $config_file"
  operations_require_trusted_root_file \
    "$config_file" "Operations configuration" || return 1

  # The production copy is root-owned and mode 0600. It is configuration, not
  # user input, so sourcing it preserves simple shell-compatible assignments.
  # shellcheck source=/dev/null
  source "$config_file"

  : "${ABAP_APP_DIR:?Set ABAP_APP_DIR in the operations configuration}"
  : "${ABAP_ENV_FILE:?Set ABAP_ENV_FILE in the operations configuration}"
  : "${ABAP_COMPOSE_BASE_FILE:?Set ABAP_COMPOSE_BASE_FILE in the operations configuration}"
  : "${ABAP_COMPOSE_OVERLAY_FILE:?Set ABAP_COMPOSE_OVERLAY_FILE in the operations configuration}"
  : "${ABAP_RESTIC_REPOSITORY:?Set ABAP_RESTIC_REPOSITORY in the operations configuration}"
  : "${ABAP_RESTIC_HOST:?Set ABAP_RESTIC_HOST in the operations configuration}"
  : "${ABAP_INVOICE_DOCUMENTS_DIR:?Set ABAP_INVOICE_DOCUMENTS_DIR in the operations configuration}"
  : "${ABAP_ACTIVITY_LOGS_DIR:?Set ABAP_ACTIVITY_LOGS_DIR in the operations configuration}"
  : "${ABAP_DATABASE_DATA_DIR:?Set ABAP_DATABASE_DATA_DIR in the operations configuration}"
  : "${ABAP_DOCKER_ROOT:?Set ABAP_DOCKER_ROOT in the operations configuration}"
  : "${ABAP_TLS_HOST:?Set ABAP_TLS_HOST in the operations configuration}"

  ABAP_RESTIC_CACHE_DIR="${ABAP_RESTIC_CACHE_DIR:-/var/cache/abap-restic}"
  ABAP_RESTIC_WARNING_BYTES="${ABAP_RESTIC_WARNING_BYTES:-7000000000}"
  ABAP_RESTIC_CRITICAL_BYTES="${ABAP_RESTIC_CRITICAL_BYTES:-8500000000}"
  ABAP_RESTIC_FREE_TIER_BYTES="${ABAP_RESTIC_FREE_TIER_BYTES:-10000000000}"
  ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES="${ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES:-100000000}"
  ABAP_STAGING_MAX_BYTES="${ABAP_STAGING_MAX_BYTES:-2000000000}"
  ABAP_LOCAL_FREE_RESERVE_BYTES="${ABAP_LOCAL_FREE_RESERVE_BYTES:-3000000000}"
  ABAP_RESTIC_CACHE_OVERHEAD_BYTES="${ABAP_RESTIC_CACHE_OVERHEAD_BYTES:-500000000}"
  ABAP_DISK_WARNING_PERCENT="${ABAP_DISK_WARNING_PERCENT:-75}"
  ABAP_DISK_CRITICAL_PERCENT="${ABAP_DISK_CRITICAL_PERCENT:-85}"
  ABAP_TLS_WARNING_DAYS="${ABAP_TLS_WARNING_DAYS:-21}"
  ABAP_TLS_CRITICAL_DAYS="${ABAP_TLS_CRITICAL_DAYS:-7}"
  ABAP_SWAP_WARNING_PERCENT="${ABAP_SWAP_WARNING_PERCENT:-10}"
  ABAP_SWAP_CRITICAL_PERCENT="${ABAP_SWAP_CRITICAL_PERCENT:-50}"
  ABAP_SWAP_WARNING_RUNS="${ABAP_SWAP_WARNING_RUNS:-3}"

  local numeric_name
  for numeric_name in \
    ABAP_RESTIC_WARNING_BYTES \
    ABAP_RESTIC_CRITICAL_BYTES \
    ABAP_RESTIC_FREE_TIER_BYTES \
    ABAP_RESTIC_PREFLIGHT_OVERHEAD_BYTES \
    ABAP_STAGING_MAX_BYTES \
    ABAP_LOCAL_FREE_RESERVE_BYTES \
    ABAP_RESTIC_CACHE_OVERHEAD_BYTES \
    ABAP_DISK_WARNING_PERCENT \
    ABAP_DISK_CRITICAL_PERCENT \
    ABAP_TLS_WARNING_DAYS \
    ABAP_TLS_CRITICAL_DAYS \
    ABAP_SWAP_WARNING_PERCENT \
    ABAP_SWAP_CRITICAL_PERCENT \
    ABAP_SWAP_WARNING_RUNS; do
    operations_require_uint "$numeric_name" "${!numeric_name}"
  done

  (( ABAP_RESTIC_WARNING_BYTES < ABAP_RESTIC_CRITICAL_BYTES )) || \
    operations_fail "The Restic warning threshold must be below the critical threshold."
  (( ABAP_RESTIC_CRITICAL_BYTES < ABAP_RESTIC_FREE_TIER_BYTES )) || \
    operations_fail "The Restic critical threshold must be below the free-tier ceiling."
  (( ABAP_DISK_WARNING_PERCENT < ABAP_DISK_CRITICAL_PERCENT )) || \
    operations_fail "The disk warning threshold must be below the critical threshold."
  (( ABAP_TLS_CRITICAL_DAYS < ABAP_TLS_WARNING_DAYS )) || \
    operations_fail "The TLS critical threshold must be below the warning threshold."
}

operations_filesystem_capacity() {
  local path="$1"
  local capacity
  capacity="$(df -P -B1 -- "$path" | awk 'NR == 2 {gsub(/%/, "", $5); print $4, $5}')" || {
    operations_fail "Filesystem capacity could not be read for $path."
    return 1
  }

  local available_bytes
  local used_percent
  read -r available_bytes used_percent <<<"$capacity"
  operations_require_uint available_bytes "${available_bytes:-}" || return 1
  operations_require_uint used_percent "${used_percent:-}" || return 1
  printf '%s %s\n' "$available_bytes" "$used_percent"
}

operations_permitted_staging_bytes() {
  local path="$1"
  local capacity
  capacity="$(operations_filesystem_capacity "$path")" || return 1

  local available_bytes
  local used_percent
  read -r available_bytes used_percent <<<"$capacity"
  if (( used_percent >= ABAP_DISK_CRITICAL_PERCENT )); then
    operations_fail "Backup blocked: staging filesystem is ${used_percent}% used."
    return 1
  fi

  local protected_bytes=$((
    ABAP_LOCAL_FREE_RESERVE_BYTES + ABAP_RESTIC_CACHE_OVERHEAD_BYTES
  ))
  if (( available_bytes <= protected_bytes )); then
    operations_fail "Backup blocked: staging filesystem cannot preserve the local free-space and Restic-cache reserves."
    return 1
  fi

  local safely_writable_bytes=$(( available_bytes - protected_bytes ))
  if (( safely_writable_bytes < ABAP_STAGING_MAX_BYTES )); then
    printf '%s\n' "$safely_writable_bytes"
  else
    printf '%s\n' "$ABAP_STAGING_MAX_BYTES"
  fi
}

operations_require_local_headroom() {
  local path="$1"
  local pending_bytes="$2"
  local label="$3"
  operations_require_uint pending_bytes "$pending_bytes" || return 1

  local capacity
  capacity="$(operations_filesystem_capacity "$path")" || return 1
  local available_bytes
  local used_percent
  read -r available_bytes used_percent <<<"$capacity"
  if (( used_percent >= ABAP_DISK_CRITICAL_PERCENT )); then
    operations_fail "$label blocked: staging filesystem is ${used_percent}% used."
    return 1
  fi

  local required_bytes=$(( ABAP_LOCAL_FREE_RESERVE_BYTES + pending_bytes ))
  if (( available_bytes < required_bytes )); then
    operations_fail "$label blocked: insufficient local capacity while preserving the minimum free-space reserve."
    return 1
  fi
}

operations_credentials_directory() {
  printf '%s\n' "${CREDENTIALS_DIRECTORY:-${ABAP_CREDENTIALS_DIRECTORY:-/etc/abap/credentials}}"
}

operations_credential_path() {
  local credential_name="$1"
  local credentials_directory
  credentials_directory="$(operations_credentials_directory)"
  printf '%s/%s\n' "$credentials_directory" "$credential_name"
}

operations_require_credential() {
  local credential_path
  credential_path="$(operations_credential_path "$1")"
  [[ -f "$credential_path" && -r "$credential_path" && ! -L "$credential_path" ]] || {
    operations_fail "Required credential is unavailable or is a symlink: $1"
    return 1
  }

  local owner_id
  local mode
  owner_id="$(stat -c '%u' -- "$credential_path")"
  mode="$(stat -c '%a' -- "$credential_path")"
  [[ "$owner_id" == 0 ]] || {
    operations_fail "Credential $1 must be owned by root."
    return 1
  }
  (( (8#$mode & 8#077) == 0 )) || {
    operations_fail "Credential $1 must not be group- or world-accessible."
    return 1
  }
}

operations_read_credential() {
  local credential_name="$1"
  local credential_path
  operations_require_credential "$credential_name" || return 1
  credential_path="$(operations_credential_path "$credential_name")"

  local -a credential_lines=()
  mapfile -t credential_lines < "$credential_path"
  (( ${#credential_lines[@]} == 1 )) || {
    operations_fail "Credential $credential_name must contain exactly one line."
    return 1
  }
  local value="${credential_lines[0]}"
  [[ -n "$value" ]] || {
    operations_fail "Credential $credential_name is empty."
    return 1
  }
  [[ "$value" != *$'\r'* ]] || {
    operations_fail "Credential $credential_name contains an invalid newline."
    return 1
  }
  printf '%s' "$value"
}

operations_configure_restic() {
  operations_require_credential restic_password || return 1
  export RESTIC_PASSWORD_FILE
  RESTIC_PASSWORD_FILE="$(operations_credential_path restic_password)"
  export RESTIC_REPOSITORY="$ABAP_RESTIC_REPOSITORY"
  export RESTIC_CACHE_DIR="$ABAP_RESTIC_CACHE_DIR"
  export AWS_ACCESS_KEY_ID
  AWS_ACCESS_KEY_ID="$(operations_read_credential b2_key_id)"
  export AWS_SECRET_ACCESS_KEY
  AWS_SECRET_ACCESS_KEY="$(operations_read_credential b2_application_key)"
}

operations_heartbeat() {
  local credential_name="$1"
  local suffix="${2:-}"
  local credential_path
  credential_path="$(operations_credential_path "$credential_name")"

  if [[ ! -f "$credential_path" ]]; then
    printf 'WARNING: heartbeat credential is unavailable: %s\n' "$credential_name" >&2
    return 0
  fi

  local heartbeat_url
  heartbeat_url="$(operations_read_credential "$credential_name")" || return 0
  local heartbeat_pattern='^https://(incidents|uptime)\.betterstack\.com/[A-Za-z0-9._~:/?%+=&-]+$'
  if [[ ! "$heartbeat_url" =~ $heartbeat_pattern ]]; then
    printf 'WARNING: refusing an invalid Better Stack heartbeat URL.\n' >&2
    return 0
  fi
  [[ "$suffix" == "" || "$suffix" == "/fail" ]] || return 0

  # Supply the secret URL through curl configuration on stdin so it is never
  # exposed in the process command line or printed to the journal.
  if ! {
    printf 'url = "%s%s"\n' "$heartbeat_url" "$suffix"
    printf 'fail\nsilent\nshow-error\nmax-time = 15\n'
  } | curl --config - >/dev/null 2>/dev/null; then
    printf 'WARNING: Better Stack heartbeat delivery failed.\n' >&2
  fi
}

operations_restic_raw_bytes() {
  local stats_json
  stats_json="$(restic stats --mode raw-data --json)" || return 1

  local raw_bytes
  raw_bytes="$(sed -n 's/.*"total_size"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' <<<"$stats_json")"
  [[ "$raw_bytes" =~ ^[0-9]+$ ]] || operations_fail "Restic did not return a usable raw-data size."
  printf '%s\n' "$raw_bytes"
}

operations_report_restic_budget() {
  local raw_bytes="$1"
  operations_require_uint raw_bytes "$raw_bytes"

  printf 'RESTIC_REFERENCED_BYTES=%s warning=%s critical=%s free_tier=%s\n' \
    "$raw_bytes" \
    "$ABAP_RESTIC_WARNING_BYTES" \
    "$ABAP_RESTIC_CRITICAL_BYTES" \
    "$ABAP_RESTIC_FREE_TIER_BYTES"

  if (( raw_bytes >= ABAP_RESTIC_CRITICAL_BYTES )); then
    printf 'CRITICAL: Restic referenced data is at or above the 8.5 GB safety threshold.\n' >&2
    return 20
  fi
  if (( raw_bytes >= ABAP_RESTIC_WARNING_BYTES )); then
    printf 'WARNING: Restic referenced data is at or above the 7 GB early-warning threshold.\n' >&2
    return 10
  fi
  return 0
}
