#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly REPOSITORY_ROOT
# shellcheck source=../../deploy/hosthatch/abap-operations-lib.sh
source "$REPOSITORY_ROOT/deploy/hosthatch/abap-operations-lib.sh"

ABAP_RESTIC_WARNING_BYTES=7000000000
ABAP_RESTIC_CRITICAL_BYTES=8500000000
ABAP_RESTIC_FREE_TIER_BYTES=10000000000
ABAP_STAGING_MAX_BYTES=2000000000
ABAP_LOCAL_FREE_RESERVE_BYTES=3000000000
ABAP_RESTIC_CACHE_OVERHEAD_BYTES=500000000
ABAP_DISK_CRITICAL_PERCENT=85

fail_test() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_budget_status() {
  local expected="$1"
  local bytes="$2"
  local status

  set +e
  operations_report_restic_budget "$bytes" >/dev/null 2>&1
  status=$?
  set -e

  [[ "$status" == "$expected" ]] || \
    fail_test "budget status for $bytes (expected $expected, got $status)"
}

assert_budget_status 0 6999999999
assert_budget_status 10 7000000000
assert_budget_status 10 8499999999
assert_budget_status 20 8500000000
assert_budget_status 20 10000000000

mock_available_bytes=10000000000
mock_used_percent=50
df() {
  printf 'Filesystem 1-blocks Used Available Capacity Mounted on\n'
  printf '/dev/mock 20000000000 10000000000 %s %s%% /mock\n' \
    "$mock_available_bytes" "$mock_used_percent"
}

permitted="$(operations_permitted_staging_bytes /mock)"
[[ "$permitted" == 2000000000 ]] || \
  fail_test "configured staging ceiling was not enforced"

mock_available_bytes=4000000000
permitted="$(operations_permitted_staging_bytes /mock)"
[[ "$permitted" == 500000000 ]] || \
  fail_test "staging allowance did not shrink to safe local capacity"

mock_available_bytes=3500000000
if operations_permitted_staging_bytes /mock >/dev/null 2>&1; then
  fail_test "staging was allowed without preserving local and cache reserves"
fi

mock_available_bytes=10000000000
mock_used_percent=85
if operations_permitted_staging_bytes /mock >/dev/null 2>&1; then
  fail_test "staging was allowed at the critical disk threshold"
fi

mock_used_percent=50
mock_available_bytes=3600000000
if operations_require_local_headroom /mock 700000000 test-copy >/dev/null 2>&1; then
  fail_test "copy was allowed without preserving local free space"
fi

mock_available_bytes=4200000000
operations_require_local_headroom /mock 700000000 test-copy || \
  fail_test "safe copy headroom was rejected"

set +e
operations_require_uint test_value '8.5GB' >/dev/null 2>&1
invalid_status=$?
set -e
[[ "$invalid_status" == 1 ]] || fail_test 'invalid unsigned integer was accepted'

credential_test_directory="$(mktemp -d)"
readonly credential_test_directory
trap 'rm -rf -- "$credential_test_directory"' EXIT
CREDENTIALS_DIRECTORY="$credential_test_directory"

# Credential ownership and modes are mocked here so these content-validation
# tests behave consistently when run by a non-root developer or CI account.
stat() {
  case "${2:-}" in
    '%u') printf '0\n' ;;
    '%a') printf '600\n' ;;
    *) command stat "$@" ;;
  esac
}

: > "$credential_test_directory/empty"
if operations_read_credential empty >/dev/null 2>&1; then
  fail_test 'empty credential was accepted'
fi
operations_heartbeat empty >/dev/null 2>&1 || \
  fail_test 'invalid optional heartbeat credential caused a hard failure'
operations_heartbeat missing-heartbeat >/dev/null 2>&1 || \
  fail_test 'missing optional heartbeat credential caused a hard failure'

printf 'first-line\nsecond-line\n' > "$credential_test_directory/multiline"
if operations_read_credential multiline >/dev/null 2>&1; then
  fail_test 'multiline credential was accepted'
fi

printf 'value-with-carriage-return\r\n' > "$credential_test_directory/carriage-return"
if operations_read_credential carriage-return >/dev/null 2>&1; then
  fail_test 'credential containing a carriage return was accepted'
fi

printf 'valid-credential-value\n' > "$credential_test_directory/valid"
credential_value="$(operations_read_credential valid)" || \
  fail_test 'valid credential was rejected'
[[ "$credential_value" == 'valid-credential-value' ]] || \
  fail_test 'valid credential value was not returned exactly'

printf 'PASS: HostHatch operations thresholds and credentials\n'
