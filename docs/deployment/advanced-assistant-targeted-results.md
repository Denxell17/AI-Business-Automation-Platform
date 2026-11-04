# Targeted production results — November 3, 2026

Follow-up: [backup repair and recovery review package](n8n-backup-repair-and-recovery.md)
is implemented/tested locally, awaiting explicit installation approval. Production is
unchanged; live coverage and recovery gates below remain open.

Owner executed the reviewed diagnostic at **07:26:10 UTC**. Sanitized evidence:
`output/server-preflight/operator-targeted-2026-11-03.json`. This report supersedes
the pending-execution findings in the [targeted preflight](advanced-assistant-targeted-preflight.md).
No repair, service change, secret installation, migration, deployment or activation
was performed. **Final readiness: NO-GO**, now based on concrete backup and recovery gaps.

## PASS: production identity and migration history

Independent live proxy and configured database-volume evidence agree:

- Authoritative production Compose project: **`abap-deploy`**.
- Production web: `03879253cea0`; image tag `abap:public-rag-0ef5085524b6-r3`;
  image ID `sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9`.
- Production PostgreSQL: `34809645f723`;
  image ID `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`.
- Migrations **001–013 applied**, zero unknown names. Complete candidate pending list:
  `014_advanced_assistant.sql`, `015_assistant_cloud_controls.sql`,
  `016_assistant_demo_leads.sql`.

The real users key has the required BIGINT type and single-column uniqueness.
`assistant_entries` is absent, as expected before 014; 014 creates its TEXT primary
key before 016 references it. Neither demo table already exists. **016 dependency
review passes conditional on ordered 014/015/016 deployment**; this is not a live
migration rehearsal or proof of all table/constraint compatibility. No migration was
applied. The filename ledger does not establish applied SQL checksums.

Public RAG is enabled; general integrations are disabled. Assistant activation/demo
settings and cloud credentials/proof remain unset. Preserve this exact serving public-
RAG release when reviewing the candidate; older general release records do not replace
the current serving image/config as the rollback reference.

## FAIL: n8n backup operation and freshness

**Failure cause confirmed:** the backup main command exited 0; its
`/usr/local/sbin/n8n-ensure-running` post-command exited 1. Installed source requires
exactly one container with the n8n Compose service label without selecting the project;
journal evidence confirms that exact cardinality error. Multiple n8n projects now
match. Do not execute this helper as a diagnostic: it can start a container.

The standalone `n8n` project is the proxy-facing instance targeted by the installed
`/usr/local/sbin/n8n-backup`. Its timer remains inactive/disabled; no alternative n8n
timer or root cron reference was identified by the diagnostic. Other external backup
systems were not established or excluded.

Correct executable paths and source hashes were verified. The installed main and n8n
backup policies retain 14 daily, 8 weekly and 12 monthly snapshots; main maintenance
also retains release-tagged snapshots. A configured retention policy is not proof of
fresh snapshots or a tested restore.

## PASS: repository access; FAIL/BLOCKED: coverage and recovery

The corrected `/usr/local/bin/restic` query succeeded. The repository contains **25
snapshots**:

| Scope | Matching snapshots | Latest at diagnostic time | Assessment |
| --- | --- | --- | --- |
| ABAP staging backup source | 20 | November 3, 02:15:37 UTC; 5.18 hours old | Fresh source metadata; content/recovery proof still needed |
| Standalone production n8n volume | 5 | October 31, 03:36:55 UTC; 75.82 hours old | Outside documented 24-hour backup objective |
| Current public-RAG production n8n volume | 0 exact source matches | None | No direct-volume snapshot coverage established in this repository |
| Public-RAG staging n8n volume | 0 exact source matches | None | No direct-volume snapshot coverage established here; distinct from production |

Latest ABAP snapshot:
`ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45`.
Latest standalone n8n snapshot:
`6f21cc3df8a89e0dd05b12313b05748038e7423d894bdfe944509200e6dea12d`.
ABAP has one retained release-tagged snapshot; standalone n8n has none in the returned
scope. Counts reflect exact source-path inclusion, not verified snapshot contents.

Do not conclude that every form of public-RAG backup is absent: bundled/other repository/
provider backups were not verified. But the current standard n8n backup targets the
standalone instance, not public RAG. Confirm protection of the RAG database, workflow
definitions, credentials and persistent encryption-key configuration before release.
No restore was performed. The existing restore-marker journal query did not succeed,
so its zero markers provide no negative evidence about prior drills.

## PASS: production RAG workflow inventory and per-instance key configuration

Current n8n image:
`sha256:240eaa2a3d491adac5817aa4c3f1c521bb18ec79f6e448517158d5220ee0f37b`.

| Project / container | Identified role | Workflow evidence | Encryption configuration |
| --- | --- | --- | --- |
| `abap-public-rag-production` / `0a800fdbc70e` | Actual production ABAP RAG destination | 2 workflows, both active; committed RAM snapshot | Persistent config key present; no environment override, which is not a mismatch |
| `abap-public-rag-staging` / `cad1a5ac6bd1` | Separate staging RAG | 2 workflows, both active | Persistent config key present; no environment override |
| `n8n` / `3a65b2018880` | Proxy-facing standalone automation instance; installed backup target | BLOCKED by bounded snapshot size/missing-source guard; do not infer empty inventory | Stored and environment keys both present and match |

Production RAG inventory fingerprint:
`8a299936c6db9ad4400d2c0b89246dd5ee7b8c22d1d56b90332dac844f157b83`.
Counts/fingerprints do not inspect per-workflow authorization or prove unchanged history
without a matching earlier baseline. No workflow, callback or Job Scraper was executed.

The diagnostic also listed `30fa4cccd4b2` from `abap-deploy` due n8n-related environment
settings. It has the older ABAP image and no n8n data-volume result; do not count it as
a fourth n8n database instance. Standalone inventory remains unverified until a bounded
method suitable for its actual size is reviewed; do not simply remove resource limits.

## BLOCKED: current rollback and recovery completeness

Older October 16 deployment/manifest records and two complete legacy base config sets
exist. No image tags matched the diagnostic's `rollback-<digits>` filter. That does
not prove rollback images are absent: current/previous image IDs and other tag patterns
may be available. The legacy records reference the older `5f06...` ABAP release, not
the current `e9b09...` public-RAG web release.

Before approval, identify/preserve the exact current production web image and merged
public-RAG configuration/overlays as the rollback target, verify artifact availability
and recovery procedure, and obtain applicable recovery proof. Do not apply an old base
Compose/config set that could remove the current public RAG. Routine assistant rollback
must not run migrations or restore the business database; disable assistant flags and
restore the approved web image/config while retaining additive tables and workflow state.

## Exact remaining requirements

1. Prepare and approve a scoped backup repair: select the standalone production n8n
   project explicitly in the recovery helper, preserve other instances, resolve its
   disabled schedule and verify fresh backups/recovery. No repair or enablement is
   authorized by the current read-only mission.
2. Establish current production public-RAG n8n backup coverage, including its persistent
   config/encryption key. If absent, prepare a separately approved backup change.
   Verify actual snapshot contents/recovery evidence, not source inclusion alone.
3. Finish bounded standalone workflow inventory and applicable workflow authorization
   review while preserving Job Scraper. Demo assistant allowlist remains empty, and
   synthetic mode must continue to block real workflow dispatch.
4. Establish current public-RAG rollback config/image artifacts and a recovery proof
   reference. Any new isolated restore drill needs separate authorization.
5. Review the candidate delta against the now-identified public-RAG release and approve
   only the exact ordered 014/015/016 migration set, approved services and rollback plan.
   Complete the restricted-menu staging visual check before activation.
6. Under separate secret-installation approval, use protected web-only read-only mounts:
   `/etc/abap/credentials/advanced-assistant-openrouter-key` to
   `/run/secrets/advanced-assistant-openrouter-key`, configured through
   `ABAP_ASSISTANT_OPENROUTER_KEY_FILE`; likewise mount the model proof and set
   `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE`. Keep raw key environment empty, verify app
   UID/GID, establish independent credential recovery and refresh the 24-hour proof.
7. Retain the two validated free models, $0 cap, no paid fallback and shared server
   usage limits. Set demo-only explicitly true; leave both activation/remote-approval
   flags false and assistant workflow allowlist empty until separately authorized.
   Unrestricted confidential-data access remains prohibited.

Only documentation/evidence were updated in this review. No application regression
tests were repeated, no new provider checks claimed and no production authorization
is requested while backup/recovery gates remain unresolved.
