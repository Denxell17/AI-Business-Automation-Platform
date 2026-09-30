#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_UNDER_TEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/oci_retry_always_free.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

fail_test() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local message="$3"
  [[ "$actual" == "$expected" ]] || fail_test "$message (expected $expected, got $actual)"
}

make_mocks() {
  local case_dir="$1"
  mkdir -p "$case_dir/bin"
  printf '0\n' > "$case_dir/list_count"
  printf '0\n' > "$case_dir/launch_count"
  printf '0\n' > "$case_dir/sleep_count"

  cat > "$case_dir/bin/oci" <<'MOCK_OCI'
#!/usr/bin/env bash
set -u
args="$*"
if [[ "$args" == *"iam availability-domain list"* ]]; then
  printf 'AP-SINGAPORE-1-AD-1\n'
elif [[ "$args" == *"network subnet get"* && "$args" == *'compartment-id'* ]]; then
  printf '%s\n' "$ABAP_OCI_COMPARTMENT_OCID"
elif [[ "$args" == *"network subnet get"* && "$args" == *'prohibit-public-ip-on-vnic'* ]]; then
  printf 'false\n'
elif [[ "$args" == *"compute image get"* ]]; then
  printf 'Canonical-Ubuntu-24.04-Minimal-aarch64-2026.09.01-0\n'
elif [[ "$args" == *"compute instance list"* ]]; then
  count="$(<"$MOCK_STATE_DIR/list_count")"
  count=$(( count + 1 ))
  printf '%s\n' "$count" > "$MOCK_STATE_DIR/list_count"
  if [[ ",${MOCK_EXISTING_ON_LIST:-}," == *",$count,"* ]]; then
    printf 'ocid1.instance.oc1.ap-singapore-1.existing\n'
  else
    printf 'null\n'
  fi
elif [[ "$args" == *"compute instance launch"* ]]; then
  count="$(<"$MOCK_STATE_DIR/launch_count")"
  count=$(( count + 1 ))
  printf '%s\n' "$count" > "$MOCK_STATE_DIR/launch_count"
  IFS=',' read -r -a outcomes <<< "$MOCK_LAUNCH_OUTCOMES"
  outcome="${outcomes[$(( count - 1 ))]:-unexpected}"
  case "$outcome" in
    capacity)
      printf 'ServiceError: OutOfHostCapacity\n' >&2
      exit 1
      ;;
    success)
      printf 'ocid1.instance.oc1.ap-singapore-1.created\n'
      ;;
    unexpected)
      printf 'ServiceError: NotAuthorizedOrNotFound\n' >&2
      exit 1
      ;;
  esac
else
  printf 'Unexpected mocked OCI call: %s\n' "$args" >&2
  exit 99
fi
MOCK_OCI

  cat > "$case_dir/bin/sleep" <<'MOCK_SLEEP'
#!/usr/bin/env bash
set -u
count="$(<"$MOCK_STATE_DIR/sleep_count")"
printf '%s\n' "$(( count + 1 ))" > "$MOCK_STATE_DIR/sleep_count"
if [[ -n "${MOCK_NOW_FILE:-}" ]]; then
  now="$(<"$MOCK_NOW_FILE")"
  printf '%s\n' "$(( now + ${MOCK_SLEEP_ADVANCE:-$1} ))" > "$MOCK_NOW_FILE"
fi
MOCK_SLEEP

  cat > "$case_dir/bin/date" <<'MOCK_DATE'
#!/usr/bin/env bash
set -u
if [[ "$*" == *" -d "* ]]; then
  printf '%s\n' "$MOCK_DEADLINE_EPOCH"
elif [[ "$*" == *"+%s"* ]]; then
  cat "$MOCK_NOW_FILE"
else
  printf '2026-10-01T00:00:00Z\n'
fi
MOCK_DATE

  chmod +x "$case_dir/bin/oci" "$case_dir/bin/sleep" "$case_dir/bin/date"
  printf 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOnly abap-test\n' > "$case_dir/test.pub"
}

run_case() {
  local name="$1"
  local outcomes="$2"
  local existing_on_list="${3:-}"
  local deadline_epoch="${4:-}"
  local now_epoch="${5:-1000}"
  local sleep_advance="${6:-1800}"
  local case_dir="$test_root/$name"
  make_mocks "$case_dir"
  printf '%s\n' "$now_epoch" > "$case_dir/now"

  set +e
  PATH="$case_dir/bin:$PATH" \
    MOCK_STATE_DIR="$case_dir" \
    MOCK_LAUNCH_OUTCOMES="$outcomes" \
    MOCK_EXISTING_ON_LIST="$existing_on_list" \
    MOCK_DEADLINE_EPOCH="$deadline_epoch" \
    MOCK_NOW_FILE="$case_dir/now" \
    MOCK_SLEEP_ADVANCE="$sleep_advance" \
    ABAP_OCI_COMPARTMENT_OCID='ocid1.compartment.oc1..test' \
    ABAP_OCI_SUBNET_OCID='ocid1.subnet.oc1.ap-singapore-1.test' \
    ABAP_OCI_IMAGE_OCID='ocid1.image.oc1.ap-singapore-1.test' \
    ABAP_SSH_PUBLIC_KEY_FILE="$case_dir/test.pub" \
    ABAP_MAX_ATTEMPTS=3 \
    ABAP_RETRY_SECONDS=1800 \
    ABAP_OCI_RETRY_UNTIL_UTC="${deadline_epoch:+2026-10-01T00:00:00Z}" \
    ABAP_CONFIRM_CREATE=YES \
    bash "$SCRIPT_UNDER_TEST" > "$case_dir/output" 2>&1
  CASE_STATUS=$?
  set -e
  CASE_LAUNCHES="$(<"$case_dir/launch_count")"
  CASE_SLEEPS="$(<"$case_dir/sleep_count")"
  CASE_OUTPUT="$case_dir/output"
}

run_case capacity_exhausted 'capacity,capacity,capacity'
assert_equals 75 "$CASE_STATUS" 'capacity exhaustion status'
assert_equals 3 "$CASE_LAUNCHES" 'capacity exhaustion launch count'
assert_equals 2 "$CASE_SLEEPS" 'capacity exhaustion sleep count'

run_case eventual_success 'capacity,success'
assert_equals 0 "$CASE_STATUS" 'eventual success status'
assert_equals 2 "$CASE_LAUNCHES" 'eventual success launch count'
assert_equals 1 "$CASE_SLEEPS" 'eventual success sleep count'
grep -q 'SUCCESS: the instance is running' "$CASE_OUTPUT" || fail_test 'success output missing'

# List calls 1 and 2 are the initial and first-attempt checks; call 3 is the
# check immediately before the second launch.
run_case existing_between_attempts 'capacity,success' '3'
assert_equals 76 "$CASE_STATUS" 'existing-instance status'
assert_equals 1 "$CASE_LAUNCHES" 'existing-instance launch count'
assert_equals 1 "$CASE_SLEEPS" 'existing-instance sleep count'

# The mocked clock advances past the deadline during the first sleep. The
# post-sleep deadline check must exit before a second launch.
run_case deadline_during_sleep 'capacity,success' '' 3000 1000 2100
assert_equals 77 "$CASE_STATUS" 'deadline-expired status'
assert_equals 1 "$CASE_LAUNCHES" 'deadline-expired launch count'
assert_equals 1 "$CASE_SLEEPS" 'deadline-expired sleep count'

# There is less than one complete interval left, so no sleep is permitted.
run_case insufficient_time 'capacity,success' '' 2800 1000
assert_equals 77 "$CASE_STATUS" 'insufficient-time status'
assert_equals 1 "$CASE_LAUNCHES" 'insufficient-time launch count'
assert_equals 0 "$CASE_SLEEPS" 'insufficient-time sleep count'

run_case unexpected_error 'unexpected'
assert_equals 1 "$CASE_STATUS" 'unexpected-error status'
assert_equals 1 "$CASE_LAUNCHES" 'unexpected-error launch count'
assert_equals 0 "$CASE_SLEEPS" 'unexpected-error sleep count'

printf 'PASS: OCI retry safety behavior\n'
