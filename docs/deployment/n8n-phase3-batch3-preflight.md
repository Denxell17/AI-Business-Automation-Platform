# n8n Phase 3 Batch 3: local hardening and production preflight

This batch remains local-only. It does not authorize production deployment,
credential rotation, or enabling any ABAP integration.

## Provider token and credential bootstrap

The scoped n8n-to-provider bearer token is supplied as a Docker secret file,
not an environment value. `ABAP_N8N_PROVIDER_TOKEN_FILE` contains only the
absolute host path to that file. The file itself must contain one random token
of at least 32 characters, optionally followed by one newline. Host ACLs must
make it readable only by the deployment account; the Compose secret mount is
read-only. The application also rejects symlinks, non-regular files, oversized
files, whitespace, and malformed token content. Permission bits are not checked
inside the container because Docker Desktop maps read-only Windows files to
permissive-looking Unix modes.

Only the one-shot credential bootstrap and the provider mount the secret
read-only at `/run/secrets/abap_n8n_provider_token`; the long-running n8n
container cannot read that file. During local startup, the bootstrap creates a
mode-0600 credential import file in a private, no-execute tmpfs, imports it into
n8n's encrypted credential store, and immediately removes the temporary file.
The bootstrap has no network and must finish before n8n starts.
The bootstrap script never reads the token from `process.env` and never prints
the token or generated credential JSON. Workflow exports contain only the
credential identifier.

For a production preflight, provision the file directly on the host with the
deployment account, restrict it to the account/container group that requires
it, and reference its absolute path from a protected deployment environment
file. Do not put the token value in Compose YAML, `.env`, shell history, CI
output, or an n8n workflow. Verify with `docker inspect` that the token is absent
from every container's `Config.Env`, and inspect the rendered Compose model
without displaying the secret file.

Credential bootstrap is idempotent for the fixed local demonstration
credential ID. Before production, export an **encrypted** n8n backup and verify
that this ID does not collide with an unrelated credential. The ABAP credential
and workflows must be owned by a dedicated ABAP project when the installed n8n
edition supports projects. On Community Edition, the sole administrator is the
security boundary: do not add untrusted editors or permit arbitrary Code-node
editing.

## Networking and resource envelope

The provider publishes no host port. It is attached to the normal application
network for PostgreSQL and to the internal `abap_n8n_private` bridge used by
n8n. n8n retains its normal network so existing portfolio workflows can keep
their current outbound access. Production Caddy must not route any hostname or
path to the provider.

The provider is constrained to 0.15 CPU, 256 MiB memory, and 64 processes. It
runs as the existing non-root UID, with a read-only root filesystem, all Linux
capabilities dropped, `no-new-privileges`, and only a 16 MiB private tmpfs.
PostgreSQL connection establishment is bounded to two seconds so an outage
fails before n8n's three-second provider request timeout and cannot acknowledge
an event that was not durably stored.
These limits are deliberately small relative to the measured HostHatch capacity
(2 vCPU, 7.8 GiB RAM, about 6.4 GiB available, 21 GB free disk). Observe CPU,
memory, restart count, callback latency, PostgreSQL connections, and disk growth
during a production canary before increasing them.

## Migration 010-012 review

- `010` is additive. Existing and future workflows remain opted out because
  `n8n_enabled` is non-null with default `FALSE`. Its partial completion index
  supports existing delivery-history retention. On a very large `workflows`
  table, confirm the PostgreSQL lock duration in a restored production copy.
- `011` is an additive, isolated durable event table. UUID uniqueness, body
  hash, state checks, leases, and callback identity preserve acceptance and
  replay guarantees. Its claim index matches the worker query.
- `012` adds non-null counters with safe defaults and checks that prevent an
  outcome from advancing beyond its owning lease attempt. Test the table scan
  and lock duration on a restored production-size database.

All three migrations are forward-compatible with integration disabled. The
safest rollback is application rollback while leaving the additive column,
table, and indexes in place. Dropping them destroys opt-in configuration,
idempotency records, and audit evidence, so destructive SQL rollback is not an
operational rollback and requires a separately approved retention/export plan.

The current event table has no automated purge. Before sustained production
volume, approve a retention period and add maintenance that deletes only old
terminal (`completed`/`dead`) rows in bounded batches. Never purge accepted or
processing rows. Until that exists, monitor table/index size; low-volume canary
use may proceed only with an explicit manual review threshold.

## Encrypted n8n backup and restore drill

Never use a decrypted credential export. Treat the n8n data volume and its
encryption key as two separate sensitive backup components.

Backup procedure for the production preflight:

1. Record the exact n8n image digest, Compose configuration checksum, volume
   name, database mode, and binary-data mode without printing secret values.
2. Pause workflow changes and stop only the n8n container for a consistent
   SQLite volume snapshot. Existing ABAP and course workflows must remain
   otherwise unchanged. If production n8n uses PostgreSQL, use a transactionally
   consistent database backup plus its configured binary-data storage.
3. Create an encrypted archive of the complete n8n data volume, including the
   SQLite database/config and any filesystem binary data. Store its checksum.
4. Back up `N8N_ENCRYPTION_KEY` separately through the existing encrypted
   backup path. Do not place it in the volume archive, command line, logs, or
   restore notes.
5. Restart the same container and verify health plus a read-only inventory of
   existing portfolio workflows.

Restore drill procedure:

1. Use an isolated Docker project, a new empty volume, no public ports, and the
   exact pinned n8n 2.42.3 image digest.
2. Restore the volume archive and supply the matching encryption key through a
   protected file mechanism. Never test with production callback endpoints or
   activate workflows.
3. Start the isolated container with outbound network access blocked where
   practical. Verify that n8n opens the database, encrypted credentials can be
   referenced without revealing them, and workflow/credential counts and IDs
   match the recorded inventory.
4. Delete only the disposable restore project after recording checksums and
   results. A backup is not accepted until this restore drill succeeds.

## Environment access and task runners

The ABAP exports contain no `$env` reference and work with
`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`; authentication is supplied by an n8n
HTTP Header Auth credential. Before changing this global setting on the shared
instance, export an encrypted backup and scan existing portfolio workflow JSON
for `$env`/environment-variable expressions. Any match is a compatibility
blocker until that workflow is migrated to an n8n credential or another
supported non-environment input. Do not weaken the ABAP setting to accommodate
new Code-node secret access.

n8n 2.42.3's internal JavaScript Code-node execution is sufficient for these
small parsing steps and passed the isolated integration run. The task-runner
warning does not require an upgrade or an external runner for this batch. Revisit
external task runners only if n8n documents the current mode as unsupported,
the shared instance begins executing untrusted code, or measured execution
isolation/resource behavior fails the production canary.

## Production preflight acceptance gates

- Encrypted backup and isolated restore drill pass with matching inventories.
- Provider token is absent from environment inspection, rendered configuration,
  logs, workflow exports, and n8n execution data.
- Provider has no published port or Caddy route; only n8n and required ABAP
  services can reach it on the private bridge.
- Existing portfolio workflows are inventoried unchanged and pass a read-only
  `$env` compatibility scan before the global block setting changes.
- Migrations 010-012 apply to a restored production-size PostgreSQL copy within
  the approved lock window, and the non-destructive rollback is rehearsed.
- A disabled canary confirms resource limits, callback recovery, audit history,
  replay protection, and integration default-OFF behavior.
- Retention ownership and a size/age threshold are approved before sustained
  event volume.
