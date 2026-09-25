# Milestone 8: Safe OCI Always Free Retry

## Purpose

`scripts/oci_retry_always_free.sh` retries creation of one ABAP production VM
when Oracle returns the temporary `Out of host capacity` error. Run it directly
in OCI Cloud Shell or through the reviewed GitHub Actions workflow described
below. It does not create networking, upgrade the account, delete resources,
or switch to a paid shape.

The script is intentionally fixed to:

- region `ap-singapore-1`;
- instance name `abap-production-01`;
- shape `VM.Standard.A1.Flex`;
- 1 OCPU and 6 GB memory;
- Canonical Ubuntu 24.04 Minimal `aarch64`;
- a public subnet and one public IPv4 address;
- at most 48 attempts, with at least 30 minutes between attempts.

The default is safer: 12 attempts with one hour between attempts.

## Important limitation

The script cannot guarantee permanent availability. Oracle may reclaim idle
Always Free compute under its published idle-instance policy. Do not generate
artificial load to evade that policy. Use encrypted backups, monitoring, and
the tested recovery process so the service can be recreated if Oracle reclaims
the VM.

## One-time prerequisites

Before running the script, create the following through the OCI Console:

1. A VCN named `abap-production-vcn` in Singapore.
2. A regional public subnet named `abap-production-public-subnet`.
3. An internet gateway and a `0.0.0.0/0` route from that public subnet.
4. A security rule that permits SSH only from Dennis's current public IP.
5. The downloaded SSH public-key file (`.pub`). Keep the private key outside
   the repository and never upload it to Cloud Shell.

Do not create a second Oracle account, upgrade to Pay As You Go, or select a
different shape as a capacity workaround.

## Required values

Collect these non-secret OCIDs from the OCI Console:

- root compartment OCID;
- public subnet OCID;
- Canonical Ubuntu 24.04 Minimal `aarch64` image OCID.

OCIDs are identifiers, not passwords, but do not commit account-specific OCIDs
to the repository. Export them only in the active Cloud Shell session.

## Upload and validate

Upload these two files to OCI Cloud Shell:

- `scripts/oci_retry_always_free.sh`
- the SSH public-key `.pub` file

Make the script executable and export the session-only values:

```bash
chmod 700 oci_retry_always_free.sh
# A root compartment uses ocid1.tenancy...; a child uses ocid1.compartment...
export ABAP_OCI_COMPARTMENT_OCID='ocid1.tenancy...'
export ABAP_OCI_SUBNET_OCID='ocid1.subnet...'
export ABAP_OCI_IMAGE_OCID='ocid1.image...'
export ABAP_SSH_PUBLIC_KEY_FILE="$HOME/name-of-downloaded-key.pub"
```

First run validation mode. This performs read-only checks and creates nothing:

```bash
./oci_retry_always_free.sh
```

Read the complete plan. It must show Singapore, `VM.Standard.A1.Flex`, 1 OCPU,
6 GB memory, the Canonical Ubuntu 24.04 Minimal `aarch64` image, and a maximum
of 12 attempts.

## Explicitly authorize creation

Only after the validation output is correct:

```bash
export ABAP_CONFIRM_CREATE=YES
./oci_retry_always_free.sh | tee abap-oci-retry.log
```

The log does not contain the SSH private key. Keep the Cloud Shell session open
while the foreground script runs. If Cloud Shell disconnects, run validation
again before restarting; the duplicate-instance guard stops if an instance was
already created.

## Stop safely

Press `Ctrl+C` at any time. The script does not delete or terminate anything.
On the next run, it checks for an existing non-terminated instance with the
same name before attempting a launch.

## Expected outcomes

- **Success:** the script prints the instance OCID, reports `RUNNING`, and exits.
- **Capacity unavailable:** it waits one hour and retries, up to 12 times,
  then exits with status `75` so automation can distinguish capacity shortage
  from an unexpected failure.
- **Any other error:** it prints the error and exits without retrying.
- **Existing instance:** it refuses to launch a duplicate and exits.

After success, use the OCI Console to verify the instance, public IP, boot
volume, and Always Free usage before installing software.

## Optional GitHub Actions retry

`.github/workflows/oci-always-free-retry.yml` can make one safe launch attempt
per hour without keeping a laptop or Cloud Shell session connected. It is
disabled unless the repository variable `ABAP_OCI_RETRY_ENABLED` is exactly
`true`. Scheduled attempts also require `ABAP_OCI_RETRY_UNTIL_UTC`; set it to a
UTC timestamp no more than seven days in the future. After that timestamp,
scheduled runs exit before contacting OCI.

The workflow must use a dedicated OCI automation user and API-signing key. An
OCI API-signing key is not the SSH key used to access the VM. Revoke the API
key and disable the workflow after the instance is created.

Required GitHub Actions secrets:

- `OCI_TENANCY_OCID`
- `OCI_USER_OCID`
- `OCI_API_KEY_FINGERPRINT`
- `OCI_API_PRIVATE_KEY`
- `ABAP_OCI_COMPARTMENT_OCID`
- `ABAP_OCI_SUBNET_OCID`
- `ABAP_OCI_IMAGE_OCID`
- `ABAP_SSH_PUBLIC_KEY`

Before enabling the schedule, run the workflow manually with `create` set to
`false`. That path validates the same launch plan and creates nothing. Review
the output, then run one manual `create=true` attempt. Enable the hourly
schedule only after both manual paths behave as expected.

Every run checks for an existing non-terminated `abap-production-01` before
launching. Capacity exhaustion returns the dedicated status code `75`, which
the workflow treats as an expected no-capacity result. Any other error fails
the workflow immediately. The workflow never upgrades the OCI account,
changes networking, deletes resources, or selects another shape.
