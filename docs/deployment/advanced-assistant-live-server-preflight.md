# Advanced Assistant: read-only server preflight

Follow-up: owner authenticated sudo in another session; automated SSH still requires
authentication. [Consolidated manual diagnostic](advanced-assistant-manual-preflight.md)
prepared and locally checked; not executed on production.

November 3, 2026. **NO-GO for deployment pending privileged verification.**
SSH succeeds as `dennis` on `abap-prod`. No production files, secrets, migrations,
containers, workflows or feature flags were changed. No production canary, inference,
business action, backup, restore or service restart was triggered.

## Results

| Gate | Result | Evidence |
| --- | --- | --- |
| SSH | PASS | Existing loaded identity connects; no credential printed |
| Origin availability | PASS | ABAP health 200/healthy, readiness 200/ready, login 200; n8n health 200/ok |
| Host capacity | PASS for observed capacity | 2 CPUs; load 0.10/0.36/0.44; 5,807 MiB RAM available of 7,941 MiB; 19 GiB disk free of 31 GiB; swap use 1 MiB |
| Main backup scheduling | PASS for service status only | ABAP backup succeeded November 3 at 02:15:49 UTC; next November 4 at 02:15 UTC |
| Main backup checks | PASS for service status only | Maintenance succeeded November 1 at 03:30:50 UTC; full check succeeded at 04:30:35 UTC |
| n8n backup health | FAIL / coverage unresolved | `n8n-backup.service` failed, Result=exit-code, state change October 31 at 03:37:19 UTC; timer loaded but inactive, no next trigger |
| Recovery readiness | BLOCKED | Protected snapshot inventory, backup scope, recovery credentials and restore evidence unreadable |
| Docker inventory / running release | BLOCKED | Docker socket permission denied; Docker daemon and Caddy systemd services active |
| Live ledger / migration 016 | BLOCKED | Database ledger/checksums and prerequisite schema cannot be inspected |
| n8n integration and workflows | BLOCKED beyond health | Workflow inventory, signed integration configuration, ownership and backup coverage require privileged access |
| Credential installation state | BLOCKED | `/etc/abap` root-only; proposed file existence unknown, not confirmed absent |
| Synthetic safeguards | PASS locally; live unverified | Fixed prompts/fixtures, isolated demo tables, confirmations and history; assistant workflow allowlist empty |
| Rollback readiness | BLOCKED | Plan prepared; actual running image/config, retrievable prior image and recovery snapshot ID unknown |

Systemd success is a signal, not proof of a recoverable encrypted snapshot. Establish
whether the failed n8n backup is obsolete and superseded by the main backup or indicates
a protection gap. Do not reset its state or run maintenance during read-only preflight.

The readable `/opt/abap/app` checkout lacks assistant modules and migrations 014–016.
Its Dockerfile, Compose and web application hashes differ from the local candidate.
It is not established as the live image source. Do not infer current deployment,
public-RAG state or migration state from this older checkout.

## Migration and credential requirements

Migration 016 adds only `assistant_demo_leads` and `assistant_demo_entries`, with fixed
value checks and foreign keys to `users` and `assistant_entries`. All 16 migrations
previously applied twice in disposable PostgreSQL. Live compatibility still requires
ledger/checksum and prerequisite-schema inspection. The startup runner applies all
pending migrations: approval must enumerate the complete list, not assume only 014–016.

Prepared web-only secret configuration, requiring separate installation approval:

- `ABAP_ASSISTANT_OPENROUTER_KEY_FILE=/run/secrets/advanced-assistant-openrouter-key`,
  sourced from `/etc/abap/credentials/advanced-assistant-openrouter-key`.
- `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE=/run/secrets/advanced-assistant-model-validation.json`,
  sourced from `/etc/abap/credentials/advanced-assistant-model-validation.json`.
- Raw `ABAP_ASSISTANT_OPENROUTER_KEY` empty; read-only mounts; no automatic host path
  creation. Proposed directory root:root 0700, files root:10001 0440, after verifying
  actual container UID/GID. Do not overwrite existing files without checking purpose.

Refresh the credential-bound 24-hour proof before release; earliest existing expiry is
November 4 at 05:36:25 UTC. Retain the $0 cap, explicit free model IDs, zero price
routing, no paid fallback and server usage limits. Credential recovery needs separate
provision because the documented backup source excludes the credential directory.
No credential was installed or uploaded.

## Release and rollback plan

Local candidate: `sha256:d811c3f9388226f3b3356f82cf348beb9afde9d66ebf9dbbe136ed7d18fc64db`.
Compare it against the actual running business/public-RAG release before selection.
Keep synthetic mode true, both activation flags false and assistant n8n allowlist empty.
The NVIDIA and Cohere free models remain restricted to synthetic/public scope;
confidential-data access is prohibited. Demo mode blocks workflow dispatch regardless
of the allowlist. Existing unrelated workflows must remain intact.

Before deployment approval:

1. Complete privileged read-only container/config/schema/ledger/workflow inspection.
2. Resolve n8n backup coverage; identify current encrypted snapshot, database/config/
   attachment/workflow coverage and restore proof. Verify recovery credential access
   without displaying credentials. A new recovery drill requires separate approval.
3. Record exact prior/candidate image digests, merged config, all pending migrations,
   backup ID, workflow inventory and rollback references. Exclude unrelated service changes.
4. Request explicit approval for the reviewed credential installation, migrations,
   limited service replacement and, separately if desired, restricted activation.

After approval only: create/verify the authorized release backup, install protected
key/proof, apply enumerated migrations and update approved services. Smoke disabled
configuration first. If activation is approved, check authenticated access/anonymous
denial, fixed EN/JA menu, both free models/manual switching, fixture-only tools,
rejection of free text/tampered inputs, confirmation/duplicate handling, isolated
history and usage errors. Verify business pages and public RAG with approved synthetic
probes and n8n inventory unchanged. Do not run Job Scraper or production canaries.
Staging graphical review of the new restricted menu remains pending.

Rollback: disable assistant/remote flags, restore verified prior web image/config,
then check business/public-RAG health. Keep additive demo tables and existing workflow/
outbox state. Do not restore the business database as routine feature rollback.

## Evidence and blocker

Sanitized evidence: `output/server-preflight/readable-audit.json`, `origin-health.json`,
`local-checkout-comparison.json`, `n8n-backup-state.txt`. No application code changed;
no new regression run was needed. Prior candidate evidence: 928 PostgreSQL snapshot
passes, 69 focused passes and 8 additional PostgreSQL boundary passes; counts overlap,
no failures/skips. No new cloud validation is claimed.

`sudo -n` requires authentication and the SSH user lacks Docker access. A securely
authenticated privileged read-only session is needed to finish. Never paste the sudo
password into chat or grant broad Docker/passwordless-sudo access for this task.
Another terminal's sudo cache may not apply to a separate SSH session. No deployment
authorization is requested until these gates pass.
