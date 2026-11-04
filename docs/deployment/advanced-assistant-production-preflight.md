> Latest: [live read-only server preflight](advanced-assistant-live-server-preflight.md). SSH works; sudo authentication blocks protected checks. Separate n8n backup service reports failed. NO-GO remains; no production changes. Restricted [synthetic/public-only scope](advanced-assistant-synthetic-release.md) remains mandatory. Historical findings below predate successful SSH access.

# Advanced Assistant production preflight — HOLD

Date: November 3, 2026. Authorization: **non-destructive preflight only**.
No deployment, activation, production migration, server credential upload, workflow
change, service reload/restart or production canary was performed.

**Readiness: NO-GO.** The earlier conditional recommendation based on inference tests
is superseded by this data-policy review and the blocked live-host checks.

## Check results

| Item | Result | Evidence / remaining requirement |
| --- | --- | --- |
| Two cloud models and $0 key inference | Prior PASS retained | Real EN/JA/protocol/switching, eight zero-cost calls; no new business records sent |
| NVIDIA free endpoint business-data policy | **FAIL for confidential/personal data** | Explicit provider restriction; synthetic/public-only use is a separate scope decision |
| Cohere free endpoint policy | **NOT CLEARED** | Applicable OpenRouter-specific retention/training coverage not established |
| Production SSH | **BLOCKED** | Server accepts configured public key; encrypted private key needs local unlock; agent stopped |
| Secure server credential installation | **BLOCKED** | Disabled local mount proposal prepared, nothing uploaded/installed |
| Migration 014 local verification | **PASS** | Additive source reviewed and hashed; previously live-tested PostgreSQL baseline retained |
| Actual production migration state | **BLOCKED** | No production SQL connection; 014/015 applied/pending state unknown |
| Proposed assistant workflow allowlist | **DENY ALL** | Empty allowlist; actual production inventory/ownership review blocked |
| Current encrypted backups/restore evidence | **BLOCKED** | Live snapshot/timer/results cannot be inspected without SSH |
| Existing origin health | **UNVERIFIED** | Both hostnames' /health and /ready returned HTTP 403; not evidence of origin failure |
| Local overlay validation | **PASS** | Credential/evidence read-only mounts, missing-path creation disabled, assistant/remote flags false |
| Local focused contract checks | **24 passed**, no failures/skips | Migration contracts and cloud-registry safety tests |

## Provider data-policy findings

The public endpoint catalog currently maps
`nvidia/nemotron-3.5-lightning:free` to NVIDIA, and
`cohere/north-mini-code:free` to Cohere. Both still advertise zero prompt/completion
prices. This is pricing evidence, not approval to send private records.

NVIDIA's free model page warns against confidential or personal information and says
use is logged for security and product improvement. Therefore I cannot clear the current
private CRM/employee/invoice tool results or potentially confidential user prompts for
that endpoint. Existing minimization and a consent checkbox do not remove the provider's
restriction. [NVIDIA free endpoint notice](https://openrouter.ai/nvidia/nemotron-3.5-lightning:free)

Cohere's policy describes collection/use of trial/research inputs and outputs and warns
against personal information in those contexts. Its enterprise commitments distinguish
commercial paying customers. The exact contract governing this OpenRouter free route
was not established, so enterprise no-training/retention assumptions cannot be applied.
This is an unresolved contractual mapping, not a claim that every OpenRouter request is
a Cohere trial request. [Cohere privacy policy](https://cohere.com/privacy),
[enterprise commitments](https://cohere.com/enterprise-data-commitments)

OpenRouter distinguishes its own optional prompt logging from upstream provider policies.
Account privacy settings were not changed or asserted verified. Disabling OpenRouter
logging alone does not establish upstream confidentiality. [Data collection](https://openrouter.ai/docs/guides/privacy/data-collection),
[provider policies](https://openrouter.ai/docs/guides/privacy/provider-logging)

The public ZDR catalog returned 1,098 entries. It listed four *non-free* Lightning routes,
but no matching selected free route; no North Mini Code route was found. This does not
authorize using those alternative routes or claim they are free. No paid alternative was
called. Request-level `zdr=true` can restrict routing, but must be tested with account
Safety Retention settings and actual free endpoint eligibility before any private-data
release. Unknown policy is a stop condition, not permission to relax filtering.
[OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr)

**Decision needed:** retain real business-data scope and establish compatible provider
terms/routes, or explicitly scope the two validated free models to synthetic/public
portfolio demonstration with suitable safeguards. No such scope change was made.
No provider account/privacy setting or key credit limit was changed.

## SSH and server access

The configured alias resolves to the existing host and dennis account. Only that alias
and its configured identity were used; no alternate account/key was guessed.
The server accepted the public key, but batch authentication could not sign with the
locked encrypted identity. The local OpenSSH agent is stopped. A local diagnostic
confirmed an empty passphrase cannot unlock it. No private key or passphrase was printed,
logged, uploaded or requested in chat. The local credential owner must unlock the
existing SSH identity through a secure local SSH-agent/authentication flow.

No SSH shell command reached the server in this run. Thus sudo access, current image,
active Compose overlays, DB state and backup state are unknown. Historical runbooks are
not substituted for live verification. Public GET-only probes returned 403 at both
app.dennisbasadre.com and abap.dennisbasadre.com; no edge/security check was bypassed.

## Concrete candidate and disabled configuration proposal

Local candidate image ID:
`sha256:2d905cb24d345a5ce410349c52ff63da70c96a17a71d1a00332e4f65ab50bb98`

Source hashes:
- `014_advanced_assistant.sql`: `56e9eedafbf88be7b34bfcc64f1556a662a6f9f0a7a8b4cbf77d85435fffa24f`
- `015_assistant_cloud_controls.sql`: `120f200245b7d74576087e37f80256191fef5cc00f35eaead65708d8081c5e56`

The working tree contains other uncommitted public-RAG/deployment work. Do not copy the
whole checkout or replace running base Compose files as an assumed assistant-only patch.
Once access is restored, compare the running release/source contracts and freeze the
reviewed candidate and exact overlays before release approval.

Prepared local artifacts:

- `output/production-assistant-preflight/candidate-manifest.json`
- `output/production-assistant-preflight/disabled-credential-override.json`
- `output/production-assistant-preflight/public-health.json`
- `output/cloud-validation/production-ssh-preflight.json`
- `output/cloud-validation/production-policy-endpoints.json`
- `output/cloud-validation/production-zdr-catalog.json`

The override targets only web. It leaves existing business, worker, public-RAG, n8n,
Caddy and database settings alone. Proposed server files (not yet installed):

- `/etc/abap/credentials/advanced-assistant-openrouter-key`
- `/etc/abap/credentials/advanced-assistant-model-validation.json`

Use a root-controlled non-public directory, files root:10001 mode 0440 for the existing
unprivileged application group, and read-only file mounts into the web container only.
Do not overwrite an existing credential without verifying its purpose. Missing mount
sources fail rather than create directories. Never put the key in YAML, image layers,
command arguments, Git, logs or rendered Compose output. Local key/evidence remain in
the already protected .abap-secrets directory; no new key copy was created in the repo.
The plan preserves the existing dedicated $0 key and two model IDs, but does not approve
their private-data use. Proof must be refreshed on the server before expiry/activation.

The proposed overlay explicitly sets both assistant and remote-approval flags false,
local development false and the *new assistant* n8n allowlist empty. It does not change
existing integration-enabled settings or existing workflow definitions. Empty is an
intentional deny-all for assistant dispatch, not authorization to run a canary. Specific
production workflow IDs need ownership/action review after the inventory is readable.

## Migration and backup assessment

014 adds assistant history/proposals/budgets; 015 adds shared concurrency/cooldown
controls. Both are additive and were already tested on disposable PostgreSQL, including
reapplication. No production migration was applied or even queried in this run.

The existing runner applies every pending migration, not only 014. The live ledger must
be read and compared before listing the exact migrations in a deployment request. If
other migrations are pending, stop and expand the review rather than silently applying
them. Local static checks cannot prove production DB readiness.

Read-only backup checks after SSH unlock: inspect installed timers and latest results,
latest encrypted Restic snapshot/time and repository status, protected-volume inventory,
recent restore-drill evidence and available disk space. Do not run prune/forget, restore,
raw-volume copies or an old deployment/canary script as a preflight check. A dated
historical restore drill does not prove a fresh recoverable pre-release snapshot.

A fresh verified release backup is required during an approved release procedure before
migrations. Provider credential files are outside the existing documented Restic source
set and need independent secure recoverability; do not silently broaden backup paths.

## Deployment plan — conditional, NOT execution authorization

1. Unlock the existing SSH identity locally. Re-run read-only host, release, DB ledger,
   backup, resource, proxy and workflow inventory checks. Do not alter services.
2. Clear the provider data-policy gate for the intended data scope. If safeguards or
   provider-route changes are needed, implement/test them locally before freezing the
   candidate. Never send real personal/confidential data merely to test privacy claims.
3. Compare/freeze the candidate against the actual running public-RAG/business release.
   Record exact image/source hashes, complete pending-migration list, current overlays,
   backup ID and rollback image. Review the empty or explicitly approved assistant-only
   workflow allowlist. Keep unrelated workflows and all existing production volumes.
4. With authenticated server access, prepare credentials/evidence in unreferenced private
   files, verify ownership/readability/fingerprint without displaying contents, and
   validate the merged *disabled* configuration. No activation, migration or deployment
   is authorized by this preflight step. No such server preparation occurred in this run.
5. Only after all gates pass, present the concrete image, migrations, web/worker targets,
   policy-approved models, allowlist, quotas, freshness job, backup/rollback references,
   smoke criteria and maintenance window for **explicit production deployment approval**.
6. Only after that later approval: take/verify the release backup, apply approved pending
   migrations once, replace only approved services, perform default-off checks, then
   activate only as authorized. Smoke health/readiness, old login/business functions,
   public RAG, authorized/unauthorized assistant behavior, model switching, quota errors
   and a separately approved synthetic workflow. No Job Scraper smoke runs.
7. Roll back the approved web image/config and disable assistant flags if checks fail;
   retain additive tables and reconcile committed outbox work. Disabling the assistant
   does not retract already queued deliveries. Never restore the business database as
   routine feature rollback or stop unrelated workers without authorization.

No final deployment authorization is requested while these gates are blocked.
Current ABAP status: inference validation passed previously; production preflight on
hold for SSH unlocking and provider-policy resolution. Next step: restore secure SSH
access and confirm the intended data scope. All unaffected independent checks above
are complete; production remains unchanged.
