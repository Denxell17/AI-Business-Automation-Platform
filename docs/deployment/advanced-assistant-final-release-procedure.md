# Synthetic-only assistant: consolidated release procedure

## RELEASE COMPLETE — LIVE, synthetic-only

**November 4, 2026: GO for the approved synthetic-only release.** Public URL:
`https://app.dennisbasadre.com/ai-assistant/advanced`.
The corrected web image was deployed November 4 **09:32:16–09:32:34 Shanghai**.
Image `sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49`,
tag `abap:assistant-synthetic-20261104-r2`. The ledger remains 001–016; the
correction did not rerun migrations. Health, readiness and login returned 200;
RAG UI baseline, original environment and all other containers were preserved.
Dedicated credential/proof files are installed server-side; transfer copies were
removed. No B2 request, backup, recovery drill or n8n workflow was run for release.

Final authenticated production browser verification PASSED after the correction:

- NVIDIA `nvidia/nemotron-3.5-lightning:free` returned a real synthetic-tool English
  summary with `DEMO-LEAD-1` and the previously confirmed isolated demo lead.
  Its expanded tool payload explicitly reports synthetic scope and those records.
- Cohere `cohere/north-mini-code:free` returned a Japanese invoice summary backed
  by the synthetic tool: `DEMO-INVOICE-1`, number `DEMO-001`, USD 100.00, draft.
- Model switching, persisted private history across web replacement and explicit
  pending-to-completed isolated confirmation passed. Confirmation created only
  `DEMO-f40ec546383c42d0bf65ae1f0b3c4c05` in the demo table. The confirmation button
  disappeared after completion; no production replay request was attempted.
- Both models consumed two calls for their final tool summaries as documented;
  the account displays 7/10 daily calls after all deployment smoke requests.
- Authenticated provider-account read at **09:38:41 Shanghai** reports limit 0,
  usage 0, daily usage 0 and free-tier true. No paid fallback was enabled.

Evidence: `output/approved-assistant-production-release-20261104-r2/` contains
the operator production-result summary, `authenticated-smoke-final.json`, final
health receipt, provider-account receipt and `live-assistant.jpg`. The initial
browser snapshot timed out after submission of the NVIDIA request; the request
was not resubmitted. A fresh snapshot showed its successful persisted result.

**Automatic validation renewal installed November 4, 10:33 Shanghai:** the hourly
timer is enabled/active and the read-only proof-directory mount is verified.
The initial service check passed with `SKIP-not-due` and zero provider requests.
Both approved models remained available; the image, original environment and
other containers were unchanged. Due evidence is renewed six hours before its
24-hour expiry; failed checks do not extend validity. The first due live renewal
has not yet been observed. See `advanced-assistant-maintenance.md` for the exact
installed mechanism and verification evidence. No image rebuild or migrations
were performed for this maintenance change.
Free-provider/shared quotas and the configured user/model/global caps remain finite.

The accepted residual full-application disaster-recovery risk remains unverified;
it is not represented as a passed restore. Dedicated public-RAG files, configuration,
UI baseline and containers were preserved; no new public-RAG provider round-trip or
live n8n execution is claimed. Completed regression evidence is reused. Four
focused prompt/privacy correction tests and six release safeguard tests passed;
no broad regression or unrelated feature was added during final deployment.

Historical execution preparation and earlier partial results follow.

## Current live result and one-file correction

The owner executed the approved production deployment on November 4,
**08:51:55–08:52:15 Shanghai**. It PASSED: credentials installed, migrations
001–016 recorded, tested image d811c3f9 deployed, assistant active in synthetic-only
mode, health/readiness/login HTTP 200, RAG marker preserved, other containers and
original environment preserved, transfer key removed, zero B2 requests.

Actual authenticated browser smoke at the public URL passed both free models
(NVIDIA English, Cohere Japanese), manual switching, private history and an explicit
pending-to-completed synthetic lead confirmation. Created isolated demo identifier:
`DEMO-f40ec546383c42d0bf65ae1f0b3c4c05`. No real CRM lead was created.

Live summary smoke exposed a prompt contradiction: the hidden share-data checkbox
left `allow_data=false`, adding a data-disabled instruction even though synthetic
mode permits fixed fixtures. A one-file correction in `advanced_assistant.py`
omits that conflicting instruction in demo mode and requests the exact read-tool
JSON for each predefined fixture-summary question. Existing read-tool permission
and synthetic-data boundaries are unchanged. Four targeted mocked boundary tests
passed. Six deployment safeguards passed for the same runner's revision support.

Corrected image `abap:assistant-synthetic-20261104-r2` is built directly on the exact
verified first release, replacing only that application file; dependencies are
unchanged. Immutable image:
`sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49`.
An initial full Dockerfile build with networking disabled failed because its pip
cache step was not reusable; no production change occurred. The minimal inherited
image build passed without installing dependencies or using network access.

The correction is within the existing deployment/fix authorization; no new approval
is requested. Its private staged bundle is
`/tmp/abap-assistant-release-r2.EvpKKy0j`, all remote hashes/syntax verified. It
reuses ledger 001–016 and does not rerun migrations. Existing dedicated credentials
must match and are reused. It replaces web only via disabled checks/activation and
retains old-image rollback on failure. Authenticated sudo is unavailable to the
assistant's SSH session, so operator execution is required once.

Corrective runner SHA-256:
`042411390709fcb874833d3691c884b49dc7794ae87cce8a31d9e784458b63d0`.
Manifest SHA-256:
`3ff96aa62b253b759ff03c2c997fd7bc19d7f97c5be9e38a2c42800bf8d0bacf`.
Command: `output/approved-assistant-production-release-20261104-r2/operator-command.txt`.
Do not rerun the consumed first release command. Continue live summary checks after
the corrective result; do not mark the whole release complete until that check passes.

## Production deployment approved — authenticated sudo execution pending

The owner explicitly accepted the disclosed disaster-recovery risk and authorized
dedicated credential/proof installation, migrations 014–016, web-only disabled
deployment, smoke tests, synthetic-only activation and web rollback on failure.
No repeat approval is required. The reviewed tested image (98,848,256-byte export),
key, current proof, overlays and single-use release runner are transferred into
`/tmp/abap-assistant-release.5uliRHEb` with private directory/file permissions.
All remote SHA-256 checks and syntax checks passed. Six focused new deployment
guard tests passed; completed application tests were not repeated. No B2 or
recovery operation was performed. Production credentials are not yet installed
and production services/migrations remain unchanged pending the operator command.

Runner SHA-256:
`18103367eaad94a0cf1ff2511e1e175f2ff357bd7ed2826a5ae39ba47b49b7e9`.
Release-input manifest SHA-256:
`1a7ba19d4f45700195ca47229a340e3504eae7d9b8730de99ae752b2c59d991c`.
One command is stored in
`output/approved-assistant-production-release-20261104/operator-command.txt`.
It verifies both frozen runner and manifest before mutation. Single-use receipt:
`/var/backups/abap/approved-assistant-production-release-20261104-1.json`.
The SSH session lacks authenticated sudo; the owner must run that command in
their Ubuntu terminal. Do not request/store the password or rerun after failure.
After result, continue the same release with authenticated browser model/language/
synthetic confirmation smoke tests. The owner reported an existing account is
signed in; no credentials were shared in chat. Browser smoke completion is not
yet claimed. The prepared runner automatically rolls web back on failed critical
deployment checks and retains additive migrations; it never restores the database.

## Current release decision — November 4, 08:34 Shanghai

**CONDITIONAL GO pending one explicit consolidated production authorization.**
The owner requested reassessment of whether the additional application disaster-
recovery rehearsal is essential. It is not a necessary gate for this narrowly
scoped additive, web-only synthetic release, provided the owner accepts the
residual disaster-recovery risk below. Do not represent the incomplete restore
as passed. Earlier blanket NO-GO/rehearsal-required statements below are historical
and superseded by this scoped decision; no production deployment is authorized yet.

Basis: existing verified encrypted image/configuration preservation and successful
database backup stand; both n8n recovery drills and isolated PostgreSQL startup
passed. Migrations 014–016 only create assistant tables/indexes and one assistant
control row, and the migration runner is transactional. Normal application rollback
returns web to the cached preserved image and retains the additive schema; it
does not depend on restoring production PostgreSQL or discarding business writes.
Production configuration/proposed disabled merge checks passed and dedicated public
RAG files are unchanged. Reuse completed application test evidence, with no new
broad tests or recovery attempt.

Fresh observations: at November 4 00:34:15 UTC, last scheduled backup remained
success/exit 0, completed November 3 02:15:49 UTC (approximately 22 hours earlier).
Next natural run is November 4 02:15 UTC; do not wait for or trigger it as an added
release prerequisite while the existing backup evidence remains acceptable.
VPS-local `/health` and `/ready` both return HTTP 200 with healthy/ready statuses.
The actual Caddy config includes `app.dennisbasadre.com`; the in-app browser
successfully rendered its public login page. Scripted public HTTP requests receive
an existing Cloudflare 403; this is not proof that browser access is broken and
does not authorize changing Cloudflare protections.

The candidate immutable image matches the tested build. Both existing model proofs
are current and match the available private key. They expire at approximately
**November 5 01:27 Shanghai**; no new provider validation was performed for this
decision. Deploy with the exact two approved free IDs and no paid fallback.

Residual risk requiring explicit acceptance: a full current-production image+
configuration+database recovery has not completed. If a database/host disaster
occurs, successful full recovery is not demonstrated, B2 availability may delay
access, and writes since the most recent backup may be lost. These limitations
remain even if ordinary web rollback succeeds. No B2 retrieval or recovery is
needed for the proposed normal deployment/rollback path.

The single approval must authorize server-side installation of the dedicated
OpenRouter key/current proof, loading the tested image, migrations 014–016,
web-only disabled deployment, focused baseline and authenticated synthetic smoke
tests, controlled synthetic-only activation, and disabling/restoring old web on
failed checks. Preserve original env/session secret, database data, other services,
public RAG, n8n workflows and timers. No confidential business-data access, live
assistant business/workflow actions or paid model fallback may be enabled.
Existing authenticated VPS sudo execution will require one operator command;
sudo authentication is not available to the assistant SSH session. Do not request
the password. Final authenticated browser smoke may require an existing account
sign-in; never forge a production session or expose credentials to avoid that step.

Latest input resolution: [minimal targeted retrieval plan](application-recovery-targeted-retrieval-plan.md).
No verified offline archive copies were located in the documented paths checked.
The cached exact preserved Docker image can be reused, reducing the remote input
requirement to the configuration package and database dump only (133,498 recovered
bytes). The local offline controller has been minimally updated and six guard
tests passed. No B2 request or recovery ran. A two-file retrieval exception and
one isolated continuation require separate explicit approval. Earlier three-file
requirements below describe the superseded archive-only transport approach.

2026-11-04, preparation only. **NO-GO for deployment or activation.** No recovery,
new backup, artifact preservation, repository request, migration, production
credential installation or service change was executed in this preparation.

## Latest protected operator result — 17:46:18 UTC November 3

The approved read-only collector completed. All runtime/Compose reconciliation
checks and all disabled-proposal preservation checks passed. Production state
comparison passed. Five dedicated public-RAG files are unchanged. Existing code
differences are limited to `database.py`, `database_connection.py`,
`n8n_demo_provider.py` and `web_app.py`; no new implementation was introduced in
this preparation. The report also lists `performance_boundary_demo.py` and
`run_tests.py` as candidate-only source files: these are development files
explicitly excluded by `.dockerignore`, not contents of the release image.
The selected source comparison contained 149 local files; the reviewed image
build set remains 147 files after those two exclusions.

The exact old production image remains cached. However, **none of the three
verified archive files was found** within the checked `/var/backups/abap` scope
(depth 3, scan completed within bounds). This is not evidence that the preserved
encrypted snapshots are missing or damaged, nor a claim about every VPS path.
The prepared offline continuation must stop on these missing inputs. Do not run
it or repeat the completed startup check.

The last scheduled backup is confirmed successful by unit status and the existing
`backup_ok` journal category. The next November 4 02:15 UTC run had still not
occurred. No additional backup or repository operation was performed.

**Critical dependency:** provide existing verified offline archive copies through
a separately approved secure transfer, if available. Otherwise the outstanding
recovery test cannot be completed under the present no-B2 rule. Access to remote
preserved artifacts would require an explicit exception; do not silently download,
list snapshots or substitute a newly generated production dump. Deployment remains
NO-GO. Evidence summary:
`output/release-finalization-preparation-20261104/protected-preflight-operator-summary.json`.

The execution-pending wording below is historical preparation, superseded by this
operator result. The recovery controller itself remains unexecuted and unapproved.

## Current evidence and outstanding dependencies

| Requirement | Current evidence |
| --- | --- |
| n8n recovery and preserved app image/configuration | Prior PASS, reused without repetition |
| Isolated PostgreSQL 18 startup | Prior PASS, 55.640 seconds; no repeated startup diagnostic |
| Current application recovery | Offline continuation prepared; execution not approved; exact local input availability protected by sudo |
| Next natural ABAP backup | Pending at observation 2026-11-03 17:26:19 UTC; last completed run November 3 02:15:49 UTC, success/exit 0; next due November 4 02:15 UTC (10:15 Shanghai) |
| Exact production Compose source | PASS, byte-identical to local base, SHA-256 c39e87d3b5e2a0cfe74336d37de70467e421f62baf69c628523ed3d74c3f878f |
| Effective production environment and proposed merge | Protected read-only collector staged; not executed |
| Free cloud models | Fresh PASS for both exact approved IDs, six synthetic inference requests, all reported cost 0 |

Evidence is in `output/release-finalization-preparation-20261104/`. Existing broad
application regressions are reused: 928 PostgreSQL tests, 69 focused tests and
8 live PostgreSQL boundary tests passed previously; counts overlap. Only the new
preparation tooling was tested: 7 read-only collector fixtures and 5 offline
continuation guard fixtures passed. No broad suite was repeated.

### Fresh model validation

- `nvidia/nemotron-3.5-lightning:free`: English, Japanese and structured business
  JSON protocol PASS.
- `cohere/north-mini-code:free`: English, Japanese and structured business JSON
  protocol PASS.
- Current provider catalog marks both as zero-price `:free`. Six total synthetic
  inference requests exercised explicit selection of each model. No automatic
  retry, substitute model or paid fallback was used. Routing retains maximum
  prompt/completion price 0 and provider fallback disabled.
- Authenticated account checks before/after: limit 0, remaining 0, usage 0,
  daily usage 0, free-tier true. The $0-limit key works for these requests.
- Native provider function calling was not tested or claimed; the existing
  assistant structured business protocol passed. Local and production activation
  flags were not changed. No credential was printed, copied to production or
  added to source control.
- `cloud-model-proof.json` is credential-bound and expires 24 hours after its
  recorded `checked_at`. Reuse this fresh proof within its validity; do not call
  providers again merely for another status report. If deployment occurs after
  expiry, a new minimal validation is required. A proof for another key is invalid.

## Immediate read-only operator check

Existing SSH works; protected artifact directories and production environment are
not accessible to the unprivileged account, and non-interactive sudo is unavailable.
One collector is staged at `/tmp/abap-release-readonly.cdFPqITO/`. This is covered by
the owner's current read-only preparation approval; it is not a recovery operation.
Run only the checksum-verifying command in
`output/release-finalization-preparation-20261104/readonly-operator-command.txt`
from the authenticated Ubuntu terminal, then return its sanitized JSON.

Controller SHA-256:
`f1bb60cba42c3befa386581c7e7903d0e0c42a67571c1051c7b582d78fc249c3`.
Its non-secret review-input file is independently pinned by SHA-256
`f98ae09a197ef43f722f3cc8d07c1221ba06b8daf9701491906a17e86b448ce4`.
Both uploaded files matched reviewed local checksums and syntax/JSON validation.
The collector writes no production files. It only:

- reads current backup service results and categorizes recent existing journal
  events without emitting message bodies;
- scans `/var/backups/abap` to depth 3, at most 100 directories/2,000 entries,
  hashes only three fixed artifact names within size bounds, follows no symlinks
  and reports whether hashes match the already authenticated originals;
- reconciles the exact Compose project, image, command, entrypoint and complete
  effective environment privately; no environment or secret values are printed;
- resolves the proposed disabled overlay through Compose stdin, without writing
  an override or starting anything, and checks preservation of unrelated services,
  non-assistant environment, existing mounts, networks, ports and secrets;
- hashes a fixed reviewed list of application code files inside the running web
  container using a read-only Python process, reports differences/absences and
  checks dedicated public-RAG files; no business data or file contents are printed;
- independently compares production configuration fingerprints after the check.

## Smallest offline recovery continuation

Prepared local controller: `deploy/hosthatch/continue-current-application-offline.py`.
It is **not staged for execution or authorized to execute**. It reuses the reviewed
engine, image/configuration verifiers and proven private runtime configuration,
including namespace-private `/run`, private daemon/store/socket, loopback-only
networking, no published ports and RAM-only disposable database data.

It requires exact-hash local copies of `application-image.tar`,
`application-configuration.tar` and `database.dump` identified by the read-only
collector. It stops before creating a receipt/workspace if any input is unavailable.
Hashes and snapshot provenance remain those already authenticated in the completed
preservation operation. There is no repository-client invocation or download path.
Imported verifier helpers are reused for offline parsing only.

Under later separate approval, one continuation would import the existing local
image archives, restore the already verified dump into a disposable PostgreSQL 18
instance, retain ledger 001–013, start the exact old ABAP image with isolated fresh
credentials/read-only database role, and verify `/health`, `/ready` and `/login`.
This does not rerun preservation, n8n drills or a standalone startup diagnostic.
Required PostgreSQL startup is part of restoring the application, not a separate
diagnostic attempt. Integrations, providers, email, workflows and workers remain
disabled. Cleanup and independent production comparisons run after success/failure;
no snapshot listing/check is performed. No automatic retry is permitted.

**If exact local copies are absent, this continuation is BLOCKED.** Earlier
rehearsal workspaces were cleaned, and preservation streamed artifacts rather than
retaining plaintext files. Their presence must not be assumed. Existing offline
copies could be supplied through a separately approved secure file transfer; do
not download from B2, generate a replacement dump, alter scheduled backup cleanup
or treat the live database as a substitute under the current approval.

## One later consolidated production authorization

Request deployment authorization only after recovery evidence and protected
configuration checks pass and the naturally scheduled backup result is acceptable.
That approval must explicitly cover all of the following, with stop-on-failure:

1. Transfer/load the pinned candidate image and reviewed release assets; install
   only the dedicated server-side OpenRouter key and current matching model proof.
2. Apply only pending migrations 014–016 once using the candidate migration image.
3. Replace web only with assistant disabled, verify baseline behavior, then perform
   controlled synthetic-only activation and approved synthetic smoke requests.
4. Disable/revert web immediately if the listed rollback conditions occur.

No deployment authorization is requested by this preparation document. The
remaining offline recovery operation also needs its own explicit execution approval.

## Exact deployment order, for that future approval

1. Verify running release and baseline ledger have not drifted. Candidate:
   `abap:assistant-synthetic-20261104`, image
   `sha256:d811c3f9388226f3b3356f82cf348beb9afde9d66ebf9dbbe136ed7d18fc64db`.
   Release assets and exact SQL checksums are listed in
   `output/assistant-release-final-20261104/release-manifest.json`. Verify image
   configuration/layers as well as the immutable image reference when transferring
   between Docker stores. Do not build or pull an unreviewed replacement.
2. Preserve `/etc/abap/production.env` and existing secrets/configuration. Install
   the approved key and proof as root:10001/0640 under root:10001/0750 directory
   `/etc/abap/credentials/advanced-assistant/`, named `openrouter-key` and
   `cloud-validation.json`. Transfer private file bytes securely, never via chat,
   argument literals, source files or logged commands. Mount read-only at the
   reviewed `/run/secrets/advanced_assistant_*` targets. Use the `_KEY_FILE` setting;
   leave inline key empty. Verify key fingerprint, both exact model records, server
   clock and proof age without printing the key. Do not enable Gemini/local models.
3. Use the actual existing base file
   `/opt/abap-public-rag-production/releases/0ef5085524b6-r2/compose.deploy.yaml`,
   existing project `abap-deploy`, its original working directory and
   `/etc/abap/production.env`. Do not substitute an r3 source directory because the
   current image tag ends in r3. Stage new overlays separately; do not overwrite base.
4. Resolve the complete candidate configuration privately. Abort if other services,
   public RAG, integration settings, workers, current secret mounts, networks or
   volumes change. Require assistant enabled/remote-approved false, demo-only true,
   empty assistant workflow allowlist and only the two reviewed free model IDs.
5. Require production pending migrations exactly 014, 015, 016. Use the reviewed
   `migration-once.json` **explicit image override**, together with the existing
   base and `disabled-web.json`, for one `compose run --rm --no-deps --pull never
   migrate`. Its `python -m deployment` applies pending migrations transactionally.
   Verify ledger 001–016. Never run destructive SQL/down migrations or a whole-stack
   startup. Stop on any unknown migration or checksum discrepancy.
6. With only base plus disabled web overlay, perform `compose up -d --no-deps
   --no-build --pull never web`. Do not recreate database, worker, retry-worker,
   proxy or n8n. Verify health/readiness, login, an approved normal business page,
   existing public-RAG UI and one approved synthetic RAG smoke request. The
   advanced route `/ai-assistant/advanced` must return 404 while disabled.
7. Only after disabled deployment passes, add the reviewed activation overlay,
   setting assistant enabled/remote-approved true while demo-only remains true.
   Replace web only with the same bounded command. Check anonymous denial, an
   existing authorized account, both selectable free models, fixed English/Japanese
   demo requests, synthetic tool results, private demo history and one fixed demo
   lead confirmation/duplicate submission. Check desktop/mobile rendering. Never
   submit real records or invoke live n8n workflows. Reuse tested quota-exhaustion
   and concurrency boundaries; do not deliberately exhaust provider quotas.
8. Initial application caps from the reviewed overlay: user 10/day, user/model
   10/day, model 20/day, provider/global 40/day; per-minute 3/6/10/10 and concurrency
   1/1/2/2 for user/model/provider/global. Provider free quotas remain separate,
   shared and finite. Quota/provider failures must fail safely or offer another
   available free model for manual selection. Never enable a paid fallback.

## Rollback conditions and actions

Stop activation or disable assistant immediately for private-data exposure,
unconfirmed real writes, missing/stale model proof, paid routing/cost, authentication
or ownership bypass, or broken confirmation/quotas. Revert web for health failures,
public-RAG regression, business regression or unreconciled production configuration.

Use the original ordered base configuration plus only `rollback-web.json`; omit
candidate/activation/assistant-secret-mount overlays. Verify old tag
`abap:public-rag-0ef5085524b6-r3` still identifies preserved image
`sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9`.
Replace **web only** using `--no-deps --no-build --pull never`; preserve the session
secret, existing RAG configuration, business integrations and every other service.
Repeat health/login/RAG baseline smoke checks. Keep additive assistant tables and
ledger records. Do not restore the whole database or lose intervening business
writes as routine rollback; database disaster recovery is separately approved.

No timer activation, new repository checks, full backup, production canary,
infrastructure upgrade or unrelated workflow changes are part of this release.
