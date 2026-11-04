# Consolidated privileged read-only diagnostic

Latest: [operator-executed results](advanced-assistant-operator-results.md). Owner ran
the reviewed script on the VPS; privileged metadata was returned. NO-GO remains due
to unresolved backup failure, failed snapshot queries and withheld ambiguous/WAL reads.
The upload-not-executed statements below describe the earlier handoff state.

November 3, 2026. Recheck after owner ran `sudo -v`: separate automated SSH session
still returns `sudo: a password is required`. No privileged production audit was run.
Deployment remains **NO-GO** pending evidence described in
[the live preflight](advanced-assistant-live-server-preflight.md).

## Review and execution

Review `scripts/advanced_assistant_readonly_preflight.py`. Its single, self-contained
shell wrapper is `output/server-preflight/advanced-assistant-readonly-preflight.sh`.
At the owner's explicit request, the reviewed wrapper was uploaded without execution
to `/tmp/abap-assistant-preflight.8ugFEzKi/advanced-assistant-readonly-preflight.sh`.
Directory mode 0700; script mode 0600; both owned by the existing SSH user `dennis`.
Execute only after operator approval, using sudo and the system shell. The wrapper
invokes isolated Python with bytecode disabled; it does not run sudo itself or write
diagnostic output to a production file. Passwords belong only in the VPS terminal.

Local and uploaded SHA-256 match:
`ec6c86062f9e1b6f5159af4c6ffd6155158a761414ad3d571770cd8e932db672`.
Evidence: `output/server-preflight/reviewed-upload.json`. The script has NOT been
executed. Only the authorized temporary directory/upload and their permissions changed.

Do not add `bash -x`, shell tracing, Docker raw inspection output or journal dumps.
The script emits sanitized JSON suitable for returning for review. It deliberately
suppresses raw errors; a BLOCKED field does not establish absence of that resource.

## Included checks

- ABAP/n8n backup and integrity-check service/timer states.
- Private inspection of the latest 200 n8n backup journal entries, returning only
  fixed failure categories; no log messages or customer information.
- Installed backup-script hashes at the expected sbin paths and protected credential
  ownership/modes/existence, never values or hashes of credentials.
- Docker image IDs, service roles, status/health and restart counts; no raw environment,
  endpoints, bind sources, container names or workflow payloads.
- Whitelisted feature flags and configuration-presence booleans.
- Uniquely identified database in the running web service's Docker project: known
  migration names and selected schema column metadata (unknown migration count only),
  using SELECTs inside an explicit read-only transaction with timeouts. No business rows.
  Includes all 16 candidate migration hashes for later comparison; these hashes do not
  establish equality with applied production migrations.
- n8n workflow/active counts and inventory fingerprint, not names, IDs, nodes or data.
  Reads the immutable SQLite main file to avoid writing sidecars. If nonempty WAL
  exists or a change is detected during the read, counts are withheld as BLOCKED;
  no checkpoint/backup command is run. Otherwise counts remain best-effort metadata.
- Stored/environment n8n encryption-key presence/equality booleans, never key values.
- Latest Restic snapshot metadata for ABAP and n8n hosts, using `--no-lock --no-cache`.
  Only the established HTTPS S3 backend is supported. Backend credentials are passed
  privately in a clean child environment; no snapshot content,
  repository URL, remote files, restore, integrity scan, retention or backup operation.

The program never sources shell configuration or executes deployment/backup scripts.
Only simple literal operations-config assignments are parsed; dynamic configuration
may leave a check BLOCKED. Normal operating-system/database audit logs of read access
may still be generated. Root privileges are required for the protected reads.

## Verification and unresolved gates

Thorough follow-up review fixed inherited child environment/PATH/Docker-context risks,
unrelated database selection, raw metadata pass-through and stale SQLite WAL counts.
External backup helper backends are rejected. Root configuration/backup credentials
must pass ownership/mode checks; shell configuration is never executed. Database reads
have default and explicit transaction read-only controls, timeouts, fixed socket and
no shell/application startup. Python runs isolated from the temporary script directory.

Thirteen mocked local security/correctness tests passed, including secret/error
redaction, SQL protections, database ambiguity, invalid connection strings, child
environment isolation, timeout suppression, untrusted/dynamic configuration, Restic
read-only flags/backend restrictions and active-WAL rejection. Python syntax and local
and remote shell syntax passed. Remote shell parsing did not execute the diagnostic.
No successful privileged live diagnostic execution is claimed. No application code
or production service was changed; only the authorized temporary upload was made.

Previously observed n8n backup failure/inactive timer is unresolved. Main ABAP backup
service success does not prove n8n coverage. Need actual snapshot age/scope, failure
cause, and existing restore evidence before backup/recovery PASS. No repair is authorized.

Returned diagnostics still require review: exact running release versus candidate,
full ledger/prerequisite compatibility, per-workflow authorization and signing/callback
configuration, active WAL inventory if provisional, protected secret mount suitability,
recoverable prior image/config and credential recovery. Snapshot listing is not a
restore test; image presence is not a proven rollback. Synthetic-only restriction,
fresh model proof and default-off flags remain mandatory. Deployment/activation,
secret installation, migrations, repairs and recovery drills need separate approval.
