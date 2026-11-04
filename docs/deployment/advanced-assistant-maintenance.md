# Minimal post-deployment maintenance — installed and verified

November 4, 2026. The synthetic-only assistant remains LIVE. The approved renewal
maintenance installation completed at 02:33:45 UTC, based on the operator-provided
sanitized controller result. No provider request, B2 operation, backup or recovery
test was performed. Existing deployment and regression evidence is reused.

## Why healthy models expire

`assistant_cloud_config.verified()` requires `0 <= now - checked_at <= 86400`
and successful free/access/business-protocol flags. `configured_models()` also
requires a fingerprint matching the current key and explicit remote approval.
After 24 hours the registry marks the model unavailable, irrespective of provider
health. This is an intentional fail-closed eligibility rule, but no renewal job
was previously installed. `assistant_maintenance.py` only purges retained history; it does
not renew model evidence. The TTL and admission checks are left unchanged.

## Installed fix

`deploy/hosthatch/renew-assistant-model-validation.py` is a host-side job using
the existing Docker CLI, Python standard library, running web container and its
existing gateway/catalog helpers. No image rebuild or dependency is needed.

- An hourly systemd timer checks freshness. Fresh proofs cause **zero provider
  requests**. At six hours remaining, renew only the due approved models.
- A normal two-model renewal makes **four requests**: one authenticated key-limit
  read, one zero-price catalog read, and **one combined English/Japanese/business-
  JSON synthetic probe per model**. No business tool is executed by the probe and
  no account identity, user input/history or business data is transmitted.
- Both exact approved IDs are hardcoded. Unexpected models, changed credentials,
  missing reviewed seed evidence, live-workflow configuration or non-demo mode
  require manual review before any network request. No new model is authorized.
- Confirm the key's credit limit is exactly zero. Existing gateway zero-price
  routing, disabled fallback and positive-cost rejection remain in force. The job
  does not change provider limits/billing or application quotas.
- Authoritative loss of free eligibility or a nonzero/unlimited key limit marks
  affected evidence unavailable. Transient failures retain its existing timestamp;
  failed probes never extend expiry. Successful models can renew independently.
  No immediate retry loop: a failed batch is retried by the next hourly tick.
- The job has a single-flight lock, a 150-second in-container deadline, bounded
  output and service timeout. Logs contain fixed statuses/model IDs/request counts,
  not credentials, provider bodies or probe answers.
- Publish atomically, preserving root:10001/0640. Refuse to overwrite a concurrent
  operator update. Failed publication preserves the last valid file.

### Approved and completed production change

1. Install the script as root:root/0750 at
   `/usr/local/lib/abap/renew-assistant-model-validation.py` and the two reviewed
   `abap-assistant-validation.service` / `.timer` files under `/etc/systemd/system`.
   They reuse the existing systemd/Docker infrastructure; existing backup, monitoring
   and retention units are unchanged. The service protects the key read-only and
   writes only in its proof/runtime directories. Enable the new hourly timer only
   after explicit approval.
2. Add `deploy/production/compose.assistant-validation-renewal.json` after the
   existing production base + R2 disabled/activation overlays, then recreate
   **web only**, using the same pinned image, with `--no-deps --no-build --pull never`.
   This adds one read-only directory bind:
   `/etc/abap/credentials/advanced-assistant` -> `/run/assistant-validation` and
   changes only `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE` to
   `/run/assistant-validation/cloud-validation.json`. All other environment, flags,
   quotas, models, mounts, ports, networks and other services remain unchanged.
   The old individual proof bind remains unused; the existing key-file bind stays
   unchanged. The directory reaches only the already authorized web container.
3. The directory bind is necessary: an individual-file bind retains the old inode
   after a host atomic rename. The directory bind lets each new registry read see
   the newly published proof without subsequent restarts or writable web mounts.
4. After approval, one service invocation can verify admission/publication. If the
   proof is still fresh it performs zero provider calls. Once installed, no laptop
   or manual daily validation is needed for normal renewal. Persistent upstream
   failure beyond the TTL still fails closed; renewal cannot guarantee provider
   availability. Operator probes consume shared free-provider quota.

No application source, image, migrations, real-data permissions, original production
environment, key, or existing workflows changed. The explicitly approved installer
at `/tmp/abap-assistant-renewal.n7JadnUn/install-assistant-validation-renewal.py`
completed successfully. Do not rerun this consumed single-use controller.

Operator receipt: `PASS-automatic-model-validation-renewal-installed`,
02:33:35–02:33:45 UTC. Health, readiness and login returned 200; RAG UI marker,
other containers, original environment and OpenRouter key were preserved. The
read-only proof mount was accessible and both approved models were available.
The service completed with `Result=success`, exit 0, `SKIP-not-due`, zero provider
requests and unchanged proof. Its subsequent inactive/static state is normal for
a completed oneshot service. The hourly timer was enabled/active with its next
tick at 03:00:37 UTC (11:00:37 Shanghai). The image remained
`sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49`.

Automatic scheduling, no-request freshness handling and evidence access passed.
The first due provider renewal/publication is not yet observed in production;
the earlier 16 mocked renewal tests cover that path. No forced probe is needed.

The installer verifies all payload checksums and running image/configuration,
installs only the renewal script/units/overlay, recreates only web without builds,
checks health and evidence access, runs the service once (fresh evidence skips
provider requests), then enables the hourly timer. It preserves the current key,
environment and other containers, and restores the original web configuration on
failure. A root-only single-use receipt prevents automatic repeated installation.
Staging checksums and the operator command are recorded under
`output/approved-assistant-renewal-install-20261104/`. Three additional local
installer guard tests passed; existing renewal tests were not repeated.

### Local checks

- **16 new renewal-only tests passed**, using mocked providers/Docker and disposable
  local files. Includes no-request fresh case, expiry recovery, key rotation,
  rejected paid/unexpected models, $0 limit, partial failures, safe logging,
  exact combined probe, atomic replacement, permissions, operator-update races,
  failure preservation and rejection of the old file-only mount.
- Local `systemd-analyze verify` passed for both new units. A dummy Docker service
  was used solely as a local dependency fixture; no units were installed or started.
- Static Compose merge passed with synthetic values: only the validation-file
  environment setting and one new read-only bind change. No services started.
- Existing successful application/deployment/provider tests were not repeated.

## Specific deferred disaster-recovery verification

The remaining gap is **one restored-backup-to-application chain**:

Restore the already authenticated 72,058-byte PostgreSQL 18 dump into an empty,
isolated disposable PostgreSQL 18 instance; verify integrity and baseline ledger
001–013; then start the already verified/imported preserved ABAP image with its
recovered configuration against that restored database and verify `/health` and
`/ready`. Keep external networking, integrations and jobs disabled and verify owned
cleanup. The existing deferred continuation already describes these steps.

Image/configuration authentication, image import, dump authentication/full parsing,
both n8n restore drills and isolated PostgreSQL startup already passed; do not
repeat those as independent gates. Current production health does not prove the
backup can be restored. This is the preserved pre-assistant rollback baseline,
not verification of later writes. Its two offline inputs were unavailable locally;
their retrieval and execution remain deferred. No new controller, restore, B2
read, backup or production change is requested or performed by this document.
