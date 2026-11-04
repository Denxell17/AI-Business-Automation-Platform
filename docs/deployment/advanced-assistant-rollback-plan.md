# Controlled assistant release rollback dependencies

Prepared November 3, 2026. **Plan only; no deployment, migration or restart authorized.**
Backup/recovery gates in [the repair report](n8n-backup-repair-and-recovery.md) must pass
before requesting assistant deployment approval.

## Verified baseline and unresolved artifacts

Diagnostic follow-up prepared in [the second-attempt review](application-rehearsal-second-attempt-review.md):
23 tests plus healthy and deliberately failing local fixtures passed. V2 retains failed
stage/command/exit/category, partial successes, protected reports and both postflight
comparisons on failure. Its new receipt is distinct from the consumed first attempt.
The first Docker root cause is still UNKNOWN. No second privileged execution or
assistant deployment is authorized by that preparation.

Latest rehearsal result (November 3): the one approved isolated application rehearsal
was **unsuccessful**, inner code `isolated_docker_operation_failed_raw_output_suppressed`.
All three artifact hashes matched; disposable cleanup passed after 205.266 seconds.
The exact failing Docker command was not retained. No successful image import, PG18
restore, app startup or health check can be claimed. Final production-state/snapshot
comparisons were skipped on failure, so their success is not inferred from static
no-change flags. See [operator result and limitations](isolated-application-recovery-rehearsal.md).
Do not repeat the consumed rehearsal, preservation or n8n drills. Rollback rehearsal
readiness remains BLOCKED; assistant deployment remains NO-GO. Further privileged
diagnostics or a corrected attempt require separate explicit approval.

Next requirement prepared: [isolated application recovery rehearsal](isolated-application-recovery-rehearsal.md).
Eight guard tests and a new synthetic PostgreSQL-18 restore/read-only app/health fixture
passed. The exact preserved-artifact rehearsal requires separate privileged approval;
no private production artifact was loaded or restored during that preparation.

Latest update, November 3 at 14:14 UTC: the approved image/configuration preservation
operation **PASSED**. Immutable current image, config digest and all 10 layers verified;
encrypted image snapshot
`6980ad9af5cd4281a5a1e88e1d5f6470a615d675384ad6d7b61810ef548fcf06` and configuration snapshot
`a6cf741f6bc5cdeaf0016b698bf77b0f651ffbb521c760796869418953a5a848` authenticated on full read-back.
All 39 configured and 5 image-default environment keys reconciled. Existing DB snapshot
`ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45` passed checksum, source/DB
identity, PostgreSQL **18** compatibility and full archive parsing without restore.
See [complete evidence and limitations](current-application-rollback-preservation.md).
Earlier statements below about missing current artifacts are historical, superseded
by this result. No preservation or n8n drill repeat is authorized. Fully rehearsed
readiness still lacks isolated image load/application boot and actual DB restore proof.
No production rollback, timer, migration or assistant deployment is authorized.

Update, November 3 at 13:17 UTC: both exact approved n8n snapshots passed isolated
offline restoration, SQLite integrity, workflow/reference checks and recovered-key
credential decryption (10 standalone and 3 RAG records). See
[recovery evidence](n8n-offline-recovery-verification.md). No server boot or application
rollback was exercised. The recovery audit confirmed the current web image is locally
available and privately rendered Compose matches its image, command and checked RAG
settings. The bounded artifact scan found 20 config-copy sets but no matching
current-image record; complete current merged configuration preservation and a durable
image rollback artifact remain unproven. Do not repeat the completed recovery drill.

Owner's 07:26 UTC read-only diagnostic independently identifies `abap-deploy` through
live proxy routing and the configured PostgreSQL volume. Current serving web is
`abap:public-rag-0ef5085524b6-r3`, image
`sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9`.
Database image is `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`.
Production public RAG uses the separate `abap-public-rag-production` n8n instance with
two active workflows. Standalone automation is project `n8n`; staging is separate.

The old October 16 config copies reference an older ABAP image and are insufficient
as the current RAG rollback baseline. No matching numeric rollback tag was returned;
this does not prove the current image is unavailable. Its observed running ID is the
required rollback reference; ensure a retrievable artifact/immutable reference exists.
The backup installer rechecks these web/database IDs and reports current Compose-source
existence, without editing application configuration.

Before release approval, verify and privately preserve the actual web container's
`com.docker.compose.project.config_files` list in order, working directory, effective
environment source, public-RAG overrides/networks/secrets and proxy configuration.
Render the merged Compose configuration privately and confirm it reproduces the running
web image/service. Never print or attach the resolved environment/config. Record safe
hashes/metadata for non-secret artifacts and root-private recovery copies of secret
configuration. No older base-only Compose file may substitute for those current sources.
This protected current-configuration review is still incomplete.

The next bounded task is prepared in
[current application artifact preservation](current-application-rollback-preservation.md).
Its read-only audit and tests are ready; protected source discovery and any encrypted
artifact creation remain distinct steps. No preservation or deployment permission
is inferred from the completed n8n recovery drills.

Update at 13:32 UTC: protected source discovery passed. The exact source is the r2
release's `compose.deploy.yaml`, with `/etc/abap/production.env`, current Caddyfile and
two mounted public-RAG secret files. Configured image/command/entrypoint and all 39
configured environment values match production. Five extra runtime keys still need
private comparison to image defaults. Durable current artifacts remain unpreserved.
The audit's zero ABAP snapshot count was a multi-source-filter defect, fixed locally
with 12 passing tests; it is not evidence of missing backups. See the preservation
report for verified paths, ownership, digest metadata and the bounded approval scope.

## Database and migration dependency review

Live ledger: 001–013 applied, no unknown names. Pending in order:
`014_advanced_assistant.sql`, `015_assistant_cloud_controls.sql`,
`016_assistant_demo_leads.sql`. All three are additive; none alters existing business
columns in the reviewed source. The live `users.user_id` BIGINT unique key matches.
014 creates `assistant_entries.entry_id` TEXT primary key; 016 then references it.
Its absence in today's production schema is expected, not a defect.

The deployment migration command enumerates all pending files and applies them in one
PostgreSQL transaction. Run it only under separately approved deployment, after recording
the exact ledger and backup ID. The web application factory is separate from the explicit
migration command. Compose web depends on the migration service, so a generic whole-stack
`up` is inappropriate for rollback. Existing local 16-migration validation is retained;
no production migration or restore rehearsal was performed in this mission.

## Exact rollback sequence after a separately authorized release

1. Record incident and approved current/past image/config/snapshot references. Freeze
   further assistant writes by disabling `ABAP_ADVANCED_ASSISTANT_ENABLED` and
   `ABAP_ASSISTANT_REMOTE_APPROVED` in the approved web override; retain demo-only true
   and empty assistant workflow allowlist. Do not edit business/RAG integration flags.
2. Restore the verified captured web configuration and immutable pre-release web image
   above, using the actual captured Compose project/files/environment in their original
   order. Apply a final web-only override for image and disabled assistant flags.
3. Replace **only web**, with Compose options `--no-deps --no-build`, waiting for its
   health check. Do not name `migrate`, database, worker or n8n, and do not run a generic
   stack deployment script. This service replacement itself requires approved rollback
   authority; none is granted by this preparation task.
4. Retain additive tables/ledger entries for 014–016. Do not run down migrations or
   restore the business database as routine rollback. Preserve confirmations/history
   and unrelated workflow/outbox state. Synthetic-only release must have produced only
   isolated demo records; investigate any contrary evidence before further changes.
5. Smoke health/readiness, login/permissions, ordinary business pages and approved public
   RAG synthetic request. Confirm the existing production RAG n8n workflows/container
   identity and standalone Job Scraper instance remain untouched. Confirm assistant is
   unavailable through its protected endpoint and no new dispatch is accepted.
6. Report actual image/config/ledger state and observed outcomes. If incompatible schema
   or wider data corruption is found, stop and request a separate recovery decision;
   never replace a live DB volume or reuse a legacy raw-volume restore script.

Rollback can be declared ready only once current artifacts, backup freshness/content
and applicable recovery evidence are verified. No assistant deployment approval is
requested now. Future release must separately authorize protected OpenRouter key/proof
installation, fresh model evidence, exact migrations, limited service deployment and
optional restricted activation; unrestricted confidential-data access stays disabled.
