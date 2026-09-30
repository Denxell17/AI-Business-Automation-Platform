#!/usr/bin/env bash
set -Eeuo pipefail

# Safely retry one ABAP Always Free compute launch from OCI Cloud Shell.
# This script never upgrades an account, creates networking, deletes resources,
# or falls back to a paid shape. It retries only Oracle host-capacity errors.

readonly REGION="ap-singapore-1"
readonly INSTANCE_NAME="abap-production-01"
readonly SHAPE="VM.Standard.A1.Flex"
readonly OCPUS="1"
readonly MEMORY_GB="6"
readonly DEFAULT_MAX_ATTEMPTS="12"
readonly DEFAULT_RETRY_SECONDS="3600"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

capacity_exhausted() {
  printf 'CAPACITY_UNAVAILABLE: %s\n' "$*" >&2
  exit 75
}

instance_exists() {
  printf 'INSTANCE_EXISTS: %s\n' "$*"
  exit 76
}

retry_window_expired() {
  printf 'RETRY_WINDOW_EXPIRED: %s\n' "$*"
  exit 77
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

require_ocid() {
  local variable_name="$1"
  local expected_prefix="$2"
  local value="${!variable_name:-}"
  [[ -n "$value" ]] || fail "$variable_name is required."
  [[ "$value" == "$expected_prefix"* ]] || fail "$variable_name does not look like the expected OCI OCID."
}

require_compartment_ocid() {
  local variable_name="$1"
  local value="${!variable_name:-}"
  [[ -n "$value" ]] || fail "$variable_name is required."
  [[ "$value" == ocid1.compartment.* || "$value" == ocid1.tenancy.* ]] || \
    fail "$variable_name must be a compartment OCID or the root tenancy OCID."
}

is_positive_integer() {
  [[ "$1" =~ ^[1-9][0-9]*$ ]]
}

require_command oci
require_compartment_ocid ABAP_OCI_COMPARTMENT_OCID
require_ocid ABAP_OCI_SUBNET_OCID "ocid1.subnet."
require_ocid ABAP_OCI_IMAGE_OCID "ocid1.image."

readonly PUBLIC_KEY_FILE="${ABAP_SSH_PUBLIC_KEY_FILE:-}"
[[ -n "$PUBLIC_KEY_FILE" ]] || fail "ABAP_SSH_PUBLIC_KEY_FILE is required."
[[ -f "$PUBLIC_KEY_FILE" ]] || fail "SSH public-key file does not exist: $PUBLIC_KEY_FILE"
grep -q -- 'PRIVATE KEY' "$PUBLIC_KEY_FILE" && fail "Refusing a private-key file. Provide the .pub public key only."
grep -Eq '^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521)) ' "$PUBLIC_KEY_FILE" || \
  fail "The SSH file does not contain a supported public key."

readonly MAX_ATTEMPTS="${ABAP_MAX_ATTEMPTS:-$DEFAULT_MAX_ATTEMPTS}"
readonly RETRY_SECONDS="${ABAP_RETRY_SECONDS:-$DEFAULT_RETRY_SECONDS}"
readonly RETRY_UNTIL_UTC="${ABAP_OCI_RETRY_UNTIL_UTC:-}"
is_positive_integer "$MAX_ATTEMPTS" || fail "ABAP_MAX_ATTEMPTS must be a positive integer."
is_positive_integer "$RETRY_SECONDS" || fail "ABAP_RETRY_SECONDS must be a positive integer."
(( MAX_ATTEMPTS <= 48 )) || fail "ABAP_MAX_ATTEMPTS cannot exceed 48."
(( RETRY_SECONDS >= 1800 )) || fail "ABAP_RETRY_SECONDS cannot be less than 1800 seconds."

retry_until_epoch=""
if [[ -n "$RETRY_UNTIL_UTC" ]]; then
  retry_until_epoch="$(date -u -d "$RETRY_UNTIL_UTC" +%s)" || \
    fail "ABAP_OCI_RETRY_UNTIL_UTC is not a valid UTC timestamp."
fi

check_retry_deadline() {
  [[ -n "$retry_until_epoch" ]] || return 0
  local now_epoch
  now_epoch="$(date -u +%s)"
  if (( now_epoch >= retry_until_epoch )); then
    retry_window_expired "The configured retry deadline has been reached."
  fi
}

printf 'Validating OCI target without creating resources...\n'

availability_domain="$(
  oci iam availability-domain list \
    --compartment-id "$ABAP_OCI_COMPARTMENT_OCID" \
    --region "$REGION" \
    --query 'data[?ends_with(name, `AP-SINGAPORE-1-AD-1`)].name | [0]' \
    --raw-output
)"
[[ -n "$availability_domain" && "$availability_domain" != "null" ]] || \
  fail "Singapore AD-1 was not found for this tenancy."

subnet_compartment="$(
  oci network subnet get \
    --subnet-id "$ABAP_OCI_SUBNET_OCID" \
    --region "$REGION" \
    --query 'data."compartment-id"' \
    --raw-output
)"
[[ "$subnet_compartment" == "$ABAP_OCI_COMPARTMENT_OCID" ]] || \
  fail "The subnet is not in the configured compartment."

public_ip_prohibited="$(
  oci network subnet get \
    --subnet-id "$ABAP_OCI_SUBNET_OCID" \
    --region "$REGION" \
    --query 'data."prohibit-public-ip-on-vnic"' \
    --raw-output
)"
[[ "$public_ip_prohibited" == "false" ]] || \
  fail "The selected subnet is not public. The script will not launch an unreachable server."

image_name="$(
  oci compute image get \
    --image-id "$ABAP_OCI_IMAGE_OCID" \
    --region "$REGION" \
    --query 'data."display-name"' \
    --raw-output
)"
[[ "$image_name" == Canonical-Ubuntu-24.04-Minimal-aarch64-* ]] || \
  fail "Image must be Canonical Ubuntu 24.04 Minimal aarch64; got: $image_name"

existing_instance_id="$(
  oci compute instance list \
    --compartment-id "$ABAP_OCI_COMPARTMENT_OCID" \
    --display-name "$INSTANCE_NAME" \
    --region "$REGION" \
    --all \
    --query 'data[?"lifecycle-state"!=`TERMINATED`].id | [0]' \
    --raw-output
)"
if [[ -n "$existing_instance_id" && "$existing_instance_id" != "null" ]]; then
  instance_exists "A non-terminated instance named $INSTANCE_NAME already exists: $existing_instance_id"
fi

printf '\nValidated launch plan:\n'
printf '  Region:       %s\n' "$REGION"
printf '  AD:           %s\n' "$availability_domain"
printf '  Name:         %s\n' "$INSTANCE_NAME"
printf '  Shape:        %s (Always Free shape)\n' "$SHAPE"
printf '  Resources:    %s OCPU, %s GB memory\n' "$OCPUS" "$MEMORY_GB"
printf '  Image:        %s\n' "$image_name"
printf '  Public IP:    enabled\n'
printf '  Max attempts: %s\n' "$MAX_ATTEMPTS"
printf '  Retry delay:  %s seconds\n\n' "$RETRY_SECONDS"

if [[ "${ABAP_CONFIRM_CREATE:-NO}" != "YES" ]]; then
  printf 'VALIDATION ONLY: no resource was created.\n'
  printf 'Set ABAP_CONFIRM_CREATE=YES only after reviewing the plan.\n'
  exit 0
fi

shape_config="{\"ocpus\":$OCPUS,\"memoryInGBs\":$MEMORY_GB}"
instance_options='{"areLegacyImdsEndpointsDisabled":true}'
freeform_tags='{"managed-by":"abap-safe-retry","environment":"production"}'

for (( attempt = 1; attempt <= MAX_ATTEMPTS; attempt++ )); do
  # The scheduled deadline is checked at the start of every iteration, including
  # immediately after a retry sleep, before any launch request can be issued.
  check_retry_deadline

  printf '[%s] Launch attempt %d of %d...\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$attempt" "$MAX_ATTEMPTS"

  # Recheck immediately before every write so a prior/manual success can never
  # result in a duplicate instance.
  existing_instance_id="$(
    oci compute instance list \
      --compartment-id "$ABAP_OCI_COMPARTMENT_OCID" \
      --display-name "$INSTANCE_NAME" \
      --region "$REGION" \
      --all \
      --query 'data[?"lifecycle-state"!=`TERMINATED`].id | [0]' \
      --raw-output
  )"
  if [[ -n "$existing_instance_id" && "$existing_instance_id" != "null" ]]; then
    instance_exists "Stopping to prevent a duplicate; instance now exists: $existing_instance_id"
  fi

  # Recheck after the read-only instance lookup so a deadline reached during
  # that request cannot be followed by a launch.
  check_retry_deadline

  error_file="$(mktemp)"
  if instance_id="$(
    oci compute instance launch \
      --availability-domain "$availability_domain" \
      --compartment-id "$ABAP_OCI_COMPARTMENT_OCID" \
      --display-name "$INSTANCE_NAME" \
      --image-id "$ABAP_OCI_IMAGE_OCID" \
      --shape "$SHAPE" \
      --shape-config "$shape_config" \
      --subnet-id "$ABAP_OCI_SUBNET_OCID" \
      --assign-public-ip true \
      --assign-private-dns-record true \
      --ssh-authorized-keys-file "$PUBLIC_KEY_FILE" \
      --instance-options "$instance_options" \
      --freeform-tags "$freeform_tags" \
      --region "$REGION" \
      --no-retry \
      --wait-for-state RUNNING \
      --max-wait-seconds 1800 \
      --query 'data.id' \
      --raw-output 2>"$error_file"
  )"; then
    rm -f "$error_file"
    printf '\nSUCCESS: the instance is running.\n'
    printf 'Instance OCID: %s\n' "$instance_id"
    printf 'The script has stopped and will not create another instance.\n'
    exit 0
  fi

  error_text="$(<"$error_file")"
  rm -f "$error_file"

  if ! grep -Eqi 'out of host capacity|OutOfHostCapacity|InsufficientHostCapacity' <<<"$error_text"; then
    printf '%s\n' "$error_text" >&2
    fail "Unexpected OCI error. No retry was attempted."
  fi

  printf 'Oracle reports temporary A1 host-capacity exhaustion.\n'
  if (( attempt == MAX_ATTEMPTS )); then
    capacity_exhausted "Capacity remained unavailable after $MAX_ATTEMPTS attempts. No instance was created."
  fi

  check_retry_deadline
  if [[ -n "$retry_until_epoch" ]]; then
    now_epoch="$(date -u +%s)"
    remaining_seconds=$(( retry_until_epoch - now_epoch ))
    if (( remaining_seconds <= RETRY_SECONDS )); then
      retry_window_expired "Only $remaining_seconds seconds remain; there is not enough time for another retry interval."
    fi
  fi

  printf 'Waiting %s seconds before the next permitted attempt...\n' "$RETRY_SECONDS"
  sleep "$RETRY_SECONDS"
  check_retry_deadline
done
