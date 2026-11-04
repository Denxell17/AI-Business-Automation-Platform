# Operator-executed production diagnostic results

Latest continuation: [targeted preflight](advanced-assistant-targeted-preflight.md).
Read-only unit phase status establishes backup command exit 0 and recovery post-command
exit 1; actual Restic is `/usr/local/bin/restic`. Revised consolidated diagnostic awaits
manual privileged execution; NO-GO remains.

Observed November 3, 2026 at 06:58:06 UTC. Owner executed the reviewed temporary script
with sudo on the VPS. Sanitized JSON extracted from the supplied terminal transcript
is retained at `output/server-preflight/operator-diagnostic-2026-11-03.json`; login
banner, IP addresses and shell transcript were not copied into that evidence file.
The assistant did not execute a privileged command or change production in this review.

**Readiness: NO-GO for deployment/activation.** Access to protected metadata succeeded,
but backup recovery, migration compatibility and release identity remain unresolved.

## Established evidence

- 11 containers observed: 9 running, 8 reporting healthy; one running n8n container
  has no configured health check. Two exited migration containers are present; their
  existence alone does not indicate migration failure (exit codes were not collected).
  All reported restart counts are zero.
- Two separate running web/database Compose projects exist. Their purpose and which
  serves production were not established by fingerprints. Do not remove either.
- Main ABAP backup succeeded November 3 at 02:15:49 UTC, with active daily timer.
  Full-check and maintenance services succeeded November 1; their timers are active.
- Separate n8n backup service remains failed (Result=exit-code, October 31), with an
  inactive timer and no next trigger. Main-process status is zero; that does not explain
  the unit failure. A post-command or other unit phase is a possibility, not a diagnosis.
- Backup credential files exist, root-owned, mode 0400, no symlinks. No values printed.
- Both web containers report public RAG enabled and general integrations disabled.
  Advanced-assistant activation/demo settings are unset; assistant allowlist empty;
  no OpenRouter key/key-file or validation-proof setting configured. This supports an
  unconfigured assistant, not proof that the new synthetic safeguards are deployed.
- The checked assistant key/proof paths returned not found or inaccessible. No secret
  installation occurred; these are still requirements for a separately approved release.
- Candidate image `sha256:d811c3f9388226f3b3356f82cf348beb9afde9d66ebf9dbbe136ed7d18fc64db`
  is absent from the returned VPS image inventory. The two running web image IDs differ
  from each other and from this candidate. That is expected before deployment, but the
  correct production target and compatible rollback image still must be identified.

## Unresolved gates and diagnostic limits

| Gate | Result and interpretation |
| --- | --- |
| n8n backup failure | FAIL/unresolved. Journal available, but none of the fixed error categories matched; this does not establish absence of errors or identify root cause. Need filtered status for all unit phases and categorized journal investigation. Do not start the backup or its post-command as a diagnostic. |
| Actual encrypted snapshots | BLOCKED. Both metadata queries failed. This is not evidence that snapshots are absent or backup credentials invalid. The diagnostic suppresses errors and pins `/usr/bin/restic`; executable availability and safe failure classification need checking before a backend diagnosis. |
| Installed backup source | Unverified. Empty hashes resulted from checking `.sh` names. Repository unit definitions use `/usr/local/sbin/abap-backup` and `/usr/local/sbin/n8n-backup`, without the suffix. Verify actual unit paths/source hashes read-only; do not execute them. |
| Migration ledger/016 | BLOCKED. Multiple web projects triggered the database-selection safeguard; no migration query ran. Identify the production web/database pair or report metadata separately for each project. All 16 listed hashes describe only the local candidate, not applied production migrations. |
| Workflow inventory | BLOCKED. Both checked n8n SQLite stores have active WAL; immutable main-file counts were correctly withheld. Need a consistent read-only inventory method, without checkpointing, exporting sensitive nodes, stopping n8n or executing workflows. |
| Encryption keys | A stored/environment match was reported, but the script overwrites this field for each instance. The final value cannot establish all n8n instances match; subsequent evidence must identify instances using non-sensitive container fingerprints. |
| Rollback | BLOCKED. Available image IDs alone do not prove which image/config serves production, compatibility of older images after additive migrations, backup recoverability or independent credential recovery. |

## Next authorized work

Continue read-only targeting and diagnostic refinement only. Identify the actual serving
web project from proxy/deployment metadata; inspect exact unit executable/post-command
statuses without printing command lines that might contain secrets; safely classify
snapshot query failures; verify snapshot age/scope and existing restore evidence. Then
review the production ledger/prerequisites for 016 and preserve the public-RAG release.
No new production upload or revised diagnostic execution has been performed in this review.

After those gates pass, present the exact pending migrations, running/candidate/rollback
images, snapshot ID, unchanged public-RAG/n8n configuration, synthetic-only guards,
credential/proof installation and refresh requirements for explicit release approval.
Do not repair backup services, enable timers, install secrets, migrate, deploy, restart
or activate as part of diagnosis. No production authorization is requested yet.
