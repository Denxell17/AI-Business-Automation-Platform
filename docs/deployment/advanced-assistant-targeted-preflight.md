# Targeted production preflight continuation

Latest: [operator-executed targeted results](advanced-assistant-targeted-results.md).
Production project/ledger, failure cause, repository access and RAG workflow counts
are now established. Backup freshness/production RAG coverage and current rollback
recovery remain blockers; pending-execution statements below are historical.

November 3, 2026. **NO-GO pending protected verification.** This continues the
[operator results](advanced-assistant-operator-results.md), without repeating the
completed application/provider regressions. No production service, timer, configuration,
database, secret or workflow was modified. Only the authorized temporary diagnostic
upload was added; privileged execution remains with the operator.

## Newly established production evidence

Existing SSH works; `sudo -n` still requires authentication. No password requested/stored.
Read-only, nonprivileged targeted checks ran at 07:07:51 UTC. Sanitized output:
`output/server-preflight/targeted-public-results.json`.

| Check | Result | Evidence |
| --- | --- | --- |
| n8n unit failure phase | **FAIL identified** | `/usr/local/sbin/n8n-backup` exited 0; `ExecStopPost=/usr/local/sbin/n8n-ensure-running` exited 1. Unit failure is attributable to the post-command, not a nonzero main-command exit. Detailed post-command cause still requires its protected source/logs. |
| Correct executable paths | **PASS** | Restic is `/usr/local/bin/restic`; backup executables are `/usr/local/sbin/abap-backup`, `/usr/local/sbin/n8n-backup`, `/usr/local/sbin/n8n-ensure-running` and `/usr/local/sbin/abap-backup-maintenance`, without `.sh`. |
| Earlier snapshot failure | **Diagnostic defect confirmed** | Earlier script pinned nonexistent `/usr/bin/restic`. Those failures did not establish repository failure or missing snapshots. Revised inspection uses the installed executable. |
| Main backup retention source | **PASS for policy identification** | Readable installed maintenance source specifies daily 14, weekly 8, monthly 12 and retained release tag. Snapshot retention and n8n coverage still need protected inspection. |
| n8n schedule | **FAIL/unresolved** | n8n backup timer is disabled, as previously observed inactive/no next run. No scheduling change made. |
| Alternative n8n protection | **BLOCKED** | Main ABAP backup source has no reference to the standard n8n volume; this alone cannot exclude another mechanism. Need current source coverage and repository inventory across snapshot hosts. |
| Production project/database | **BLOCKED** | Previous inventory contains two web/database projects. No project was guessed and no ledger queried. |
| Migration 016 | **BLOCKED on live state** | Local additive implementation already tested; pending production migrations and prerequisite keys/types remain unknown. |
| Active n8n workflow/key inventory | **BLOCKED pending manual run** | Previous WAL reads withheld. Revised diagnostic returns per-instance purpose/key assertions and RAM-only committed workflow counts. |
| Rollback/recovery | **BLOCKED** | Must map current serving image, prior images, config sets, snapshot scope/age and existing restore evidence. |

The local `n8n-ensure-running` source demands exactly one container with the n8n service
label and does not filter its Compose project. Previous production inventory includes
two containers with that label. This is a concrete candidate explanation for the
post-command failure, **not yet a verified match to installed protected source/logs**.
Do not run that helper: it can start a container. Do not run backup/maintenance scripts
as diagnostics; they can stop services, write backups and prune snapshots.

## Consolidated reviewed manual diagnostic

Source: `scripts/advanced_assistant_targeted_preflight.py`; selected existing helper
definitions are bundled in `output/server-preflight/advanced-assistant-targeted-preflight.sh`.
Unused legacy diagnostic entry points are excluded. Uploaded file:
`/tmp/abap-assistant-preflight.8ugFEzKi/advanced-assistant-targeted-preflight.sh`.
Existing private directory 0700; new script 0600. Uploaded/local SHA-256 verified equal:
`307c772701703ccbe6b4f916c450aec643a23f2b8f56b5151e07485dfa3c0658`.
Evidence: `output/server-preflight/targeted-reviewed-upload.json`.

The operator should execute the uploaded file using sudo and the system shell in the
VPS terminal, then return the sanitized JSON. It has **not** been run with privileges
by the assistant. No sudo bypass, password collection or privilege change is proposed.

Protected checks in that single script:

1. Inspect installed backup source hashes, retention policies and filtered failure
   indicators; inspect post-command status without printing command arguments.
2. List existing snapshots with correct Restic binary and `--no-lock --no-cache`.
   Credentials stay in child environment, HTTPS S3 backend only. Report safe error
   categories, snapshot counts/age/IDs/release tags and exact current-volume source
   inclusion across hosts. Never run backup, forget, prune, check, restore or a heartbeat.
3. Identify production only when live Caddy proxy metadata for the configured ABAP
   hostname agrees with the configured production database-volume source and Compose
   project. No private routes/endpoints printed. Conflicting/missing evidence blocks SQL.
4. Query only that database's migration names/schema assertions in an explicit read-only
   transaction with default read-only mode/timeouts. Verify single-column prerequisite
   keys/types for 016. Unknown migration names are counted, not printed. Pending 014 may
   supply missing assistant table prerequisites; no migration or startup runner invoked.
5. Identify n8n instances, including differently named services, using image/service/
   environment metadata. Associate them with proxy routes, ABAP RAG/business targets
   and installed backup volume. Report encryption-key assertions separately per instance.
6. Read capped SQLite/WAL bytes with file reads only; check stable file metadata and WAL
   salts/checksums; include only committed frames in a RAM image. Open SQLite only on
   `:memory:` and return counts/fingerprint, never workflow names, nodes or credentials.
   No live SQLite connection, SHM access, checkpoint or source-file write. Bound source
   bytes to 32 MiB (main file 16 MiB), query rows to 10,000 and processing to 10 seconds;
   changing, unsupported or oversized snapshots remain BLOCKED.
7. Inspect available rollback image tags, release-record image IDs, config-file presence
   and existing journal restore-success markers. Never execute or extract artifacts.

The SQLite snapshot method follows the [SQLite WAL format](https://www.sqlite.org/fileformat.html#wal_format)
and [RAM deserialization contract](https://www.sqlite.org/c3ref/deserialize.html).
Only RAM header bytes are adapted for deserialization. No database contents or key
values are returned. Snapshot source inclusion is not proof of recoverable contents;
absence of a journal success marker is not proof no recovery drill occurred.

## Diagnostic verification

**11 new targeted tests passed, zero failures/skips**, using synthetic fixtures in a
network-isolated local candidate container with a read-only root filesystem, private
temporary memory filesystem and resource limits. Tests cover correct proxy/volume
selection amid multiple projects, conflicting authority, default/transaction read-only
SQL, metadata redaction, correct Restic path/read-only flags, committed WAL inventory,
uncommitted tail exclusion, stale generation handling, corrupt checksum rejection,
deadline handling and byte-for-byte unchanged synthetic DB/WAL/SHM files. Log:
`output/server-preflight/targeted-tests.log`. Existing application/provider tests were
not repeated. Final bundled Python and local/remote shell syntax checks passed.
Shell parsing did not execute the privileged diagnostic.

## Exact remaining release requirements

- Obtain the targeted protected output and establish the authoritative production
  project, database, web/database/n8n image IDs and unchanged public-RAG topology.
- Confirm installed post-command failure cause and current n8n backup coverage/RPO.
  If coverage is inadequate, approve a separate scoped repair and verify it before
  assistant release; no timer enable/restart/repair is currently authorized.
- Confirm repository accessibility, retained current snapshots covering actual ABAP
  database/config/documents and relevant n8n volumes/config/encryption recovery material;
  identify applicable existing recovery proof. Any new drill requires separate approval.
- Review complete pending ledger list, schema prerequisites/conflicts and source
  compatibility, including 014/015/016 as applicable. Record current/prior image and
  config rollback references. Do not infer applied checksums from filename-only ledger.
- Preserve synthetic/public-only scope. Install no secret now. Future approved setup
  uses web-only read-only key/proof mounts from `/etc/abap/credentials`, setting
  `ABAP_ASSISTANT_OPENROUTER_KEY_FILE=/run/secrets/advanced-assistant-openrouter-key` and
  `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE=/run/secrets/advanced-assistant-model-validation.json`.
  Keep raw key env empty, verify actual app UID/GID before permissions, and provide
  independent credential recovery. Refresh 24-hour credential-bound free-model proof.
- Keep `ABAP_ASSISTANT_DEMO_ONLY=true`, assistant workflow allowlist empty and both
  activation/remote-approval flags false until explicit controlled release approval.
  Preserve the two validated free model IDs, $0 key cap, server limits, zero-price
  routing and no paid fallback. Existing workflows/Job Scraper remain untouched.
- Before approval, present exact image/config delta, backup/recovery reference, complete
  migration list and smoke/rollback criteria; include restricted-menu staging visual
  check. Approval must separately cover secrets, migrations, deployment and activation.

Routine rollback disables the assistant and restores the verified previous web image/
configuration, preserving additive tables and unrelated workflow state. Do not perform
a production database restore as routine feature rollback.
