> Latest: [dedicated OpenRouter $0-key live results](advanced-assistant-openrouter-live-validation.md). Two cloud models passed real English/Japanese/protocol and switching checks; production remains disabled.

> Current cloud-only production requirements and validation: [free-tier cloud report](advanced-assistant-cloud-validation.md). Local Qwen is not required; no laptop dependency.

> Latest release-gate evidence: [provider, isolated n8n and graphical UI results](advanced-assistant-release-gates.md). N8n/UI gates passed; live provider validation remains blocked.

> Docker follow-up, November 3, 2026: the engine is now available. The candidate image built successfully, six live PostgreSQL atomic tests passed, and image smoke checks passed. The complete PostgreSQL-enabled suite passed all 896 tests. This follow-up supersedes the earlier Docker/PostgreSQL-unavailable statements.

## Docker and live PostgreSQL follow-up

Created only the disposable `abap-assistant-validation-20261103` PostgreSQL 18.6 container,
a separate `abap_image_smoke` database, and `abap-assistant-image-smoke` web container on
a dedicated test network. Ports bind to loopback; credentials and records are synthetic.
No existing container, production database or production service was changed.

The first live atomic run exposed a test-fixture issue: Psycopg's keyword connection
string did not satisfy ABAP's URL-only configuration validator. The fixture now keeps
an explicit PostgreSQL URL and URL-encodes its per-test schema search-path option.
No production database-configuration validation was weakened.

- Six live PostgreSQL atomic tests passed: all domain handlers, concurrent confirmation,
  invoice/claim rollback, outbox/duplicate callback handling, stale review and revocation.
- Complete PostgreSQL-enabled regression: **896 passed, 0 failed, 0 skipped**, 211.258 seconds; log: `output/assistant-live-postgresql-regression.log`.
- Docker candidate image `abap:assistant-validation-local` built successfully.
- Image migrations applied twice successfully to a separate disposable smoke database;
  all 14 migrations are recorded.
- Image `/health`, `/ready`, `/login`: HTTP 200. Advanced assistant and `/docs`: HTTP 404.
- Candidate runs as UID 10001. Assistant and remote-approval flags remain false;
  the assistant n8n allowlist is empty.
- Provider live coverage remains unavailable: no configured models/credentials/local
  Qwen service. A real n8n workflow-network round trip and visual/keyboard/mobile review
  remain unverified; PostgreSQL callback/store tests are not a real n8n deployment.

Readiness remains **NO-GO for production activation** pending those remaining live
provider/n8n and staging UI checks. PostgreSQL and image-build blockers are resolved
with the complete-suite result above. The two disposable containers and their dedicated network were removed after validation; the local candidate image is retained for review. Existing production-approval requirements
and backup/rollback instructions below still apply.

# Final implementation mission — current status

This report supersedes the earlier local-baseline report. Production remains unchanged;
flags remain disabled by default. No commit, push, deployment, paid activation, real
provider call, or production database operation was performed.

## Completed implementations

Confirmation now uses `business_transaction.py`: a context-local connection loan lets
existing CRM, customer, invoice and workflow services share a single transaction.
Repository commit/close calls cannot commit or close the owning transaction. A nested
rollback poisons the unit of work. Claim, account/ownership/schema/version validation,
domain writes, audit records, workflow tasks, outbox insert and completion history
commit together or roll back together. A failed operation leaves its proposal pending
until expiry; it can be retried only through another explicit confirmation. Completed
proposal IDs cannot execute twice. Different proposal IDs remain different actions.

SQLite uses BEGIN IMMEDIATE. PostgreSQL uses bounded lock/statement timeouts and
conservative SHARE ROW EXCLUSIVE locks on the relevant domain tables before validation.
Those locks conflict with ordinary domain writes as well as assistant writes, closing
the ownership/status race. This intentionally serializes low-volume assistant writes;
staging must measure contention before any higher-volume deployment. Connection scope
is confined to the database path and execution context. No network calls occur inside
the business transaction.

For n8n-enabled workflows, the server requires the current user's ownership, active
workflow state, enabled existing integration configuration and an explicit
`ABAP_ASSISTANT_N8N_WORKFLOWS` identifier allowlist. The review includes n8n_enabled.
Confirmation creates a manual execution and one existing signed-delivery outbox record
in the same transaction. Existing worker signing, timeouts, leases, bounded retry,
replay protection and audit infrastructure are reused. No private endpoint is placed
in prompts, browser data or history. Ordinary manual runs still only record execution.

Callback application and the private demo processor now accept a manual execution only
when an outbound workflow-start record exists for that execution. Existing scheduled
handling remains intact. The assistant does not create or edit n8n workflows; neither
the Job Scraper nor public RAG workflows were modified. Successful network delivery and
end-to-end operation against a real n8n instance still require staging validation.

## Files changed in this follow-up

- New: `Projects/employee_management_system/business_transaction.py`,
  `assistant_confirmation.py`, and `tests/test_assistant_atomic.py`.
- Updated: `database.py`, `database_connection.py`, `assistant_tools.py`,
  `advanced_assistant_web.py`, `advanced_assistant.py`, `n8n_demo_provider.py`,
  `templates/advanced_assistant.html`, and gettext source/Japanese compiled catalogs.
- Configuration: `.env.example`, `compose.advanced-assistant.yaml` (empty n8n allowlist).
- Documentation: this report, links from earlier architecture/validation documentation,
  and the existing completion roadmap.

No additional schema migration is needed. Existing additive migration 014 supplies
claims/history/budgets; existing execution/outbox tables supply dispatch. A live
PostgreSQL migration run remains outstanding.

## Validation and live coverage

- Complete regression snapshot: **892 run, 873 passed, 19 skipped, 0 failed**
  in 244.752 seconds (`output/advanced-assistant-release-regression.log`).
- Latest focused run: **71 run, 65 passed, 6 skipped, 0 failed** in 47.095 seconds
  (`output/advanced-assistant-release-focused.log`). This includes the final two added
  atomic negative tests and their optional PostgreSQL counterparts; these test additions
  occurred after full-suite discovery. Counts overlap and are not additive.
- Full-suite skips: 15 existing PostgreSQL integration cases plus 4 new PostgreSQL
  atomic cases discovered at the start of that run. The latest focused suite discovers
  all 6 PostgreSQL atomic cases and skips them without an isolated URL.
- No unresolved executed failures. Module compilation and whitespace checks passed.
- Compose validation passed using synthetic settings; assistant=false,
  remote-approval=false, workflow allowlist empty. No Docker image build was possible.
- Migration 014 contract coverage remains in the complete regression suite; no new
  schema migration was introduced and no production migration was executed.

New tests inject failures after business writes and during outbox insertion, verify
rollback of invoice line items and action claims, exercise concurrent confirmations,
all domain action handlers, stale reviews and account revocation, and apply/replay
manual execution callbacks. The same atomic tests have an optional PostgreSQL class
that provisions a uniquely named schema inside ABAP_TEST_DATABASE_URL and cleans up
only that test schema. It is skipped without an explicitly supplied isolated database.

Gemini/OpenRouter/compatible adapters and local-provider reuse pass mocked tests.
There are no configured live assistant models in the process. A presence-only check
also found no Gemini/OpenRouter assistant keys, compatible endpoint, local Qwen endpoint,
or isolated PostgreSQL URL in the project configuration. Credentials were not printed.
Live provider results: **not run**, not passed. Quota/timeout/error handling, manual
switching, no paid fallback, EN/JA behavior and malicious argument rejection are covered
by deterministic/mocked tests. Actual model quality, remote billing/data policy, account
quota and real Japanese responses remain unverified.

Docker CLI configuration validation passes with synthetic settings. Docker's engine
pipe is unavailable even after attempting a hidden local Desktop startup. No PostgreSQL
server binaries were found on the command path or standard PostgreSQL installation
path. No isolated ABAP_TEST_DATABASE_URL exists. Consequently the complete live
PostgreSQL suite, container image build and real n8n delivery cannot be claimed.

## Security verification and remaining blockers

Authorization, object ownership, session version, expiration, CSRF and schema checks
remain mandatory; business writes require explicit confirmation. Single-use proposal
claims and domain changes are now atomic in code and verified with local SQLite tests.
PostgreSQL locking and rollback behavior are implemented but **not live-verified**.
Existing CSP/escaping, request limits, durable budgets, privacy/retention rules and
free-only OpenRouter/no automatic fallback policies remain in place. ABAP remains a
single-organization application; no tenant isolation beyond the existing schema is claimed.

Genuine external blockers:

1. An available local Docker/PostgreSQL runtime or an explicitly isolated test database
   URL is required to execute PostgreSQL migrations, concurrency tests and all currently
   skipped live integration tests. Production credentials must not be supplied for this.
2. Approved provider model IDs plus server-side credentials/quota policy, or a running
   configured loopback Qwen service, are required for live provider validation.
3. A private isolated n8n staging destination with existing HMAC credentials and approved
   workflow IDs is required to prove real delivery, retry, timeout and callback behavior.
4. Container build and staging browser/mobile/keyboard smoke checks remain unexecuted.

## Backup, rollout, smoke checks and rollback

Before a separately authorized production rollout, follow the existing
`docs/deployment/hosthatch-backup-restore-monitoring-runbook.md`: verify a fresh encrypted
Restic backup and its restore evidence; do not create an unencrypted business-data copy.
Record the current image tag, migration version and reviewed configuration securely.

First stage the candidate image on disposable PostgreSQL, apply migration 014 twice,
run the entire PostgreSQL-enabled suite and atomic concurrency tests, and verify no
unexpected migration diff. Keep the assistant and remote-approval flags false until
explicit staging configuration is reviewed. Schedule existing assistant retention
maintenance and verify worker/outbox monitoring.

Production smoke checks, only after authorization: health/readiness; existing login and
public RAG; admin versus viewer access; two-account data isolation; EN/JA questions;
proposal cancel/confirm/repeat; read-only inspection of the queued allowlisted execution;
verified callback and retry status; usage counters and audit logs without secret data.
Use synthetic records and a separately approved staging/demo workflow. Never run the Job
Scraper as a smoke test or assume enqueue means remote completion.

Rollback: disable the assistant flag, empty its allowlist and recreate only the reviewed
web service using the existing deployment runbook. Retain additive tables. Inventory
already queued deliveries: disabling the assistant does not retract a committed outbox
record or undo an external action. Stop/disable the integration worker only with separate
operational authorization if delivery suspension is required. Reconcile executions via
audit history; never blindly rerun or delete queued work. Use the previous image tag if
needed. Database restore is a disaster-recovery decision, not routine feature rollback.

## Readiness and exact approval

**NO-GO for production activation** until live PostgreSQL, real n8n staging, configured
provider validation and staging smoke checks pass. The prior code-level atomicity and
outbox gaps have been implemented; external validation remains a release gate.

Current ABAP status: advanced assistant implementation extended; default-off and local
verification complete as recorded above. Next step: supply isolated test infrastructure
and approved provider/staging configuration, then execute the prepared live checks.

Only after those gates pass, production approval must explicitly identify the reviewed
release image/commit, authorize migration 014 on the named ABAP database, the web/worker
release, the exact n8n workflow allowlist, provider/model and billing/data-sharing settings,
and feature activation. No production authorization is requested prematurely here.
