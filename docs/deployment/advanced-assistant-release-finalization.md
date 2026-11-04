# Advanced Assistant release finalization — 2026-11-04

**CURRENT STATUS: RELEASE COMPLETE / LIVE — approved synthetic-only scope.**
R2 deployed November 4 at 09:32 Shanghai. Both approved free models passed final
authenticated production tool-summary checks (NVIDIA English synthetic leads,
Cohere Japanese synthetic invoice). Confirmation and private history passed.
Health/readiness/login 200; ledger 001–016 reused; other containers/environment
preserved; provider limit/usage 0; zero B2 requests. Actual evidence and the
November 5 01:27 Shanghai proof-renewal deadline are at the top of
[the release procedure](advanced-assistant-final-release-procedure.md).
All older pending/NO-GO/preparation entries below are historical. Full disaster
recovery remains unverified under the owner's accepted residual-risk decision.

**Current decision: CONDITIONAL GO, pending explicit consolidated deployment
approval accepting the remaining unrehearsed disaster-recovery risk.** The owner
requested the smallest safe production path. The additional recovery rehearsal
is not essential to ordinary additive migrations/web-only rollback; no recovery
success is fabricated. See the current decision at the top of the consolidated
release procedure. Older NO-GO/rehearsal-required entries below are historical.
Current app health/readiness and browser login access passed, the tested candidate
and key-bound model proofs match, and the existing successful backup remains valid.
No production service/credential/migration/activation change has occurred.

Latest protected operator check (November 3 17:46:18 UTC): effective production
configuration, disabled proposal preservation, five dedicated public-RAG files
and production-state comparison **PASS**. No verified image/configuration/dump
archive was found in the bounded ABAP backup-directory scan. The exact production
Docker image is cached, but the offline recovery controller is **BLOCKED on local
archive inputs**. Existing encrypted snapshots have not been rechecked or altered.
The next naturally scheduled backup remains pending at this observation. Do not
repeat the completed read-only check or startup diagnostic. See the consolidated
release procedure for evidence and the current input dependency.

Latest preparation and exact remaining gates are recorded in
[consolidated release procedure](advanced-assistant-final-release-procedure.md).
Both approved free models passed a fresh six-request synthetic validation at $0;
production Compose source is byte-identical to the reviewed local base. Protected
runtime/artifact checks await the staged read-only operator command. The next
natural backup was still pending at the latest observation. An offline-only
application continuation is prepared locally, not authorized or executed. No
completed recovery/startup/backup operation was repeated.

**NO-GO for production activation.** This is the current continuity record; older
preflight reports describe historical states. No production changes, B2 API calls,
new backups, restores, full repository checks or recovery rehearsals were executed
in this finalization task. Existing n8n recovery and artifact preservation evidence
is reused.

Latest operator evidence: the separately approved zero-B2 startup-only diagnostic
**PASSED in 55.640 seconds**. The exact cached PostgreSQL image was imported into
a private daemon, started once and reached readiness with PostgreSQL major 18.
Isolation, zero-owned-container cleanup, daemon/workspace cleanup and independent
production-state comparison passed. The original connection-refused cause remains
UNKNOWN; stronger private `/run` isolation was used, so causality is not proven.
No data restore or ABAP startup was included. See
[startup diagnostic result](postgresql-startup-zero-b2-diagnostic.md). Do not
repeat this completed diagnostic. The outstanding recovery evidence gap is now
specifically preserved-dump restoration and recovered application health, rather
than the ability to start an empty PostgreSQL instance. The later diagnostic had
zero B2 requests and did not change production services.

## Supported PostgreSQL diagnosis

The second rehearsal imported both images and verified the preserved application
configuration digest and ten layers. It then failed at `start_postgresql`:
`docker_start`, exit 1, `connection_refused` (264 stderr bytes). The container was
not running, exited 128, was not OOM-killed and had no application logs. SQL
readiness polling, database restoration and application startup were never reached.
The private daemon subsequently serviced inspection/removal and exited cleanly.

This is a container runtime startup failure, not evidence of a PostgreSQL SQL
readiness race or an application connection-string error. **The refused component
and underlying root cause remain UNKNOWN.** The old diagnostic report cannot
recover the omitted socket/component identity.

A disposable local fixture used the VPS's checksum-pinned public Docker 29.8.2,
containerd 2.3.6 and runc 1.5.1 binaries, a private store and cached stock PostgreSQL
image. It ran only a PostgreSQL version probe, without restoring data. It failed
with a different nested-container cgroup/runc error and no connection-refused
classification. Cleanup passed. This does not reproduce or explain the VPS error;
no PostgreSQL timeout, URL, cgroup, capability or resource change is justified by it.

Evidence: `output/backup-repair/application-rehearsal-v2-production-result.json`
and `output/backup-repair/local-private-runtime-start-result.json`.

## Minimum correction and validation

- `application_rehearsal_core.py` now distinguishes runtime container start from
  PostgreSQL readiness and retains fixed component categories for containerd,
  shim, runc, ttrpc and Unix socket type. Actual addresses, arguments and raw
  stderr remain excluded. Existing stage, exit/timeout, partial-result, protected
  report, cleanup and independent postflight comparisons remain in place.
- The importing controller's expected core checksum was updated. Its consumed
  second-attempt receipt was not changed; this does not authorize another run.
- Targeted local recovery guard suite: **24 passed**, zero failures/skips.
- Application code unchanged in this task. **147 build inputs match** candidate
  image `sha256:d811c3f9388226f3b3356f82cf348beb9afde9d66ebf9dbbe136ed7d18fc64db`.
- Prior application evidence reused: **928 PostgreSQL regression tests**, **69
  focused tests**, and **8 live PostgreSQL boundary tests** passed; counts overlap.
  All sixteen migrations were previously reapplied on a disposable database.
- Local static Compose validation passed with synthetic environment values:
  other services, existing web volumes and non-assistant environment preserved;
  assistant disabled, synthetic-only, no assistant workflows, read-only secret
  mounts, and explicit candidate migration image. No containers were started.
  The exact private production Compose merge still requires server-side review;
  the local base is not asserted identical to production.

## Backup reliability observation

Existing November 3 scheduled ABAP backup evidence remains successful, exit 0
at 02:15:49 UTC. Read-only service metadata at November 3 16:37:02 UTC showed
the next natural run due **November 4 02:15 UTC / 10:15 Asia/Shanghai**. That run
had not occurred at observation time. No success is claimed in advance.

After it is due, inspect existing service status/journal metadata only. Do not
trigger another backup or remote Restic verification. An unsuccessful natural run
or inability to establish current backup freshness keeps release blocked. Routine
n8n timer qualification is not claimed from the successful manual drills; no timer
activation or infrastructure expansion is part of this release.

## Prepared review assets

`output/assistant-release-final-20261104/` contains checksum-listed JSON Compose
overlays, exact migrations 014–016, a manifest and static validation receipt.
These are local review assets, not a deployed package or executable authorization.
The unique local candidate tag is `abap:assistant-synthetic-20261104`.

The disabled web overlay preserves authentication, permissions, confirmations and
audit controls. The server accepts fixed EN/JA demo requests and fixed fictional
tool data only; real customer, employee, invoice and workflow records are blocked.
Only isolated synthetic demo-lead writes are permitted. The assistant workflow
allowlist stays empty. Existing RAG, normal business integrations and workers must
retain their current configuration.

The two previously validated free IDs are:

- `nvidia/nemotron-3.5-lightning:free`
- `cohere/north-mini-code:free`

Prior English, Japanese and structured business JSON protocol tests passed with
the dedicated $0-limit key. Native provider tool-calling is not claimed. No new
inference was performed here. Both exact models need fresh credential-bound
validation within 24 hours of activation; unavailable models must remain excluded.
No paid model or paid fallback is allowed.

Proposed server-only credentials (not installed):

- `/etc/abap/credentials/advanced-assistant/openrouter-key`
- `/etc/abap/credentials/advanced-assistant/cloud-validation.json`

Parent directory root:10001/0750; files root:10001/0640, read-only mounted into
web. Use `ABAP_ASSISTANT_OPENROUTER_KEY_FILE` and
`ABAP_ASSISTANT_CLOUD_VALIDATION_FILE`; leave inline key empty. Never place keys
in chat, arguments, Compose text, output or source control. The existing isolated
validation command is `python -m assistant_cloud_validate --output <protected-file>`;
review both exact records, free eligibility and matching key fingerprint rather
than relying on command exit status alone. Permit remote calls only in that
approved one-off validator while production web remains disabled.

Proposed initial ABAP limits: user 10/day and 10/model/day; model 20/day;
provider/global 40/day. Per-minute limits user/model/provider/global 3/6/10/10;
concurrency 1/1/2/2. Provider free quotas are separate and shared; availability
and unlimited use are not promised. Quota errors offer manual selection of another
verified free model, never paid fallback.

## Shortest safe remaining path

1. Resolve the runtime blocker with a separately reviewed, bounded **zero-B2,
   startup-only** diagnostic if existing evidence cannot suffice. Reuse cached
   stock PostgreSQL, a new private store/socket and disposable resources; no
   artifact re-download, database restore, app rehearsal or production daemon
   modification. Do not run it without explicit permission. A successful version
   probe alone would not prove production-dump restore/application recovery.
   Actual current-image/database application recovery remains unverified and
   needs closure before claiming rollback readiness.
2. Observe the next naturally scheduled ABAP backup after its due time using
   existing local service evidence. No B2 verification loop or extra backup.
3. Complete private exact-production Compose/runtime configuration and running
   image source comparison against the candidate, especially public RAG and
   existing business behavior. Do not substitute a legacy checkout comparison.
4. Once critical gates close, present **one consolidated production approval**
   covering secure key/proof installation, exact candidate image transfer,
   migrations 014–016, disabled web deployment, smoke checks and controlled
   synthetic-only activation. No such authorization is requested or implied yet.

## Bounded deployment plan for that later approval

- Pin the candidate image ID and all release asset checksums. Verify current
  production image, environment, available capacity, migration ledger 001–013
  and pending set exactly 014–016. Stop on drift or unknown migrations. Do not
  rerun backup/repository integrity procedures as a deployment preflight.
- Privately compare effective production configuration; use the actual ordered
  production Compose source at
  `/opt/abap-public-rag-production/releases/0ef5085524b6-r2/compose.deploy.yaml`,
  project `abap-deploy`, env `/etc/abap/production.env`. Preserve existing
  database, volumes, networks, secrets, public RAG, workers and n8n instances.
- Install only the separately approved credential/proof files securely. Validate
  exact free IDs and policy boundary, then leave web flags false. Stop on quota,
  provider failure, stale proof or nonmatching key fingerprint.
- Run the migration service once with the **explicit candidate image override**
  and `python -m deployment`; its PostgreSQL transaction applies the approved
  additive migrations. Do not infer that a web-only image override changes the
  migrate service. Verify ledger 001–016; no destructive down migration.
- Recreate **web only**, with `--no-deps --no-build`, using the disabled overlay.
  Do not run whole-stack startup or historical deployment/canary scripts.
- Verify `/health`, `/ready`, existing login/business screens and public RAG;
  advanced route `/ai-assistant/advanced` must remain 404 while disabled.
- Under the approved activation scope, set only assistant enabled/remote-approved
  true with demo-only true. Test anonymous denial, authorized model list, EN/JA
  fixed requests, model switching, synthetic read results, one isolated confirmed
  demo action, duplicate rejection, private history, quota/error messages and
  mobile/desktop rendering. Do not send real records, trigger live workflows,
  deliberately exhaust provider quotas or test credentials through logs.
- Stop/rollback on health regression, RAG/business regression, private-data access,
  wrong-model selection, missing proof, migration inconsistency or failed isolation.

## Rollback conditions and limitations

Disable assistant flags immediately on an assistant-specific safety failure. For
application rollback use the original ordered Compose files plus only the reviewed
rollback web overlay (omit candidate/activation/secret-mount overlays), restore
web to the preserved current release and run web-only `--no-deps --no-build`.
Verify immutable preserved image
`sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9`
and existing tag `abap:public-rag-0ef5085524b6-r3` before use. Preserve the original
session secret and business integration settings. Do not recreate other services.

Keep additive assistant tables and migration ledger records; ordinary application
rollback does not restore the entire database or discard intervening business
writes. Database recovery is a separate disaster-recovery operation requiring
approval and an explicit data-loss decision. Encrypted image/configuration
preservation and database dump authentication/parsing passed previously, but the
current production application recovery rehearsal has not completed. Proxy/TLS,
host disaster recovery and document/activity-log payload restoration were not
exercised. These limits must not be represented as a proven full-system restore.
