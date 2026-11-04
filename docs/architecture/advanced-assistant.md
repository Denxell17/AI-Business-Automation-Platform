> Historical baseline: current follow-up implementation and release gates are in [the final mission report](advanced-assistant-final-validation.md).

# Advanced authenticated assistant — local implementation, November 3, 2026

ABAP's existing single-question assistant remains available by default. Setting
`ABAP_ADVANCED_ASSISTANT_ENABLED=true` redirects its GET page to the new workspace.
The public RAG chatbot, Job Scraper, production services and existing workflow
definitions are unchanged. No commit, push, provider purchase or deployment was performed.

## Implemented and reused

- A server-only explicit model registry: Gemini REST, OpenRouter chat completions,
  an operator-configured HTTPS compatible endpoint, and the existing loopback
  llama.cpp/Qwen adapter. Native tool calling and structured output are not required.
- Manual selection with configured/unavailable labels. Availability means configured,
  not a successful live health probe. There is no automatic fallback, retry or billing activation.
- OpenRouter IDs must end in `:free`. Gemini and custom endpoints require operator
  review of billing/quota settings, as do all remote models. No guaranteed zero-cost claim.
- Read tools for assigned leads, related customers, self-created invoices belonging to
  assigned leads, employee directory fields, owned workflows with recent self-started
  executions, and the user's CRM audit events. Queries return at most 30 records.
  Invoice outstanding/overdue figures are calculated from that sample, not company totals.
- Proposals for creating/updating leads, converting a qualified owned lead to a customer,
  creating a USD draft invoice, and recording an owned active manual workflow run.
  Contact validation, stage transitions, invoice calculations and domain writes reuse
  `crm_service.py`, `invoice_service.py`, and `workflow_service.py`.
- Exact arguments and record snapshots shown before a separate confirmation POST.
  Rechecks cover active account/session version, permissions, ownership, schema, business
  rules, object version, expiration, CSRF and an atomic single-use action claim.
- Reminder preparation is ordinary text drafting only. No email, external communication,
  payment, deletion, bulk action, SQL execution or arbitrary workflow creation tool exists.
- EN/JA response choice independent from the existing gettext interface preference.
  New UI strings extend the existing Japanese catalogs. Outputs are escaped text.
- Private server-side history with seven-day logical retention, clear-history controls,
  and cancellation of pending proposals. History is displayed but not sent to models;
  each turn is independent. At most 30 history/action entries are displayed.
- Existing session authentication, authorization, CSRF, CSP, private no-store responses,
  audit logger and shared provider rate/concurrency protection are reused.
- Durable UTC daily model-call budgets (100/user, 1000/global). Each actual call is
  reserved before sending; read summaries need two calls. Failed calls consume budget.
  Safe numeric provider usage/cost fields and duration/error markers are retained for
  seven days; missing cost means unknown, not zero. Browser displays the user's daily count.
- 64 KiB streamed form limit, strict extra-field rejection, bounded responses, fixed
  provider endpoints, 30-second remote socket timeouts, no HTTP redirects or model fallback.

The text protocol lets a model propose one validated JSON tool object. ABAP executes
at most one read tool and one summary call, or stores one write proposal. Model text,
retrieved records and user messages never authorize writes. Record instructions can
affect answer quality, but the summary phase has no executable tools.

## Boundaries and security findings

1. **Single organization only.** The existing schema has no tenant identifier. CRM and
   workflow tools use tighter ownership checks than the existing shared admin screens.
   Employee directory access remains shared under the existing employee permission.
   Multi-tenant deployment requires a tenant-aware data model and tests before activation.
2. **Concurrency/atomicity remains a production blocker.** The action claim commits before
   domain services open their own transactions. Duplicate confirmation of that ID is prevented,
   including concurrent claims. A crash after claiming fails closed and must be reconciled
   manually. Record snapshots reject changes observed before execution, but existing domain
   writes do not atomically combine ownership checks and writes. An ownership/status change
   racing between validation and commit remains possible. Add transaction-aware domain APIs
   with row/version locking and an atomic action result before production write activation.
   Separate newly proposed actions with different IDs are not semantic duplicates.
3. **No assistant n8n dispatch.** Existing signed webhooks, replay rejection, outbox leases
   and callbacks are preserved. The manual start service records a running execution and
   task snapshots; it does not dispatch n8n. Assistant starts reject `n8n_enabled` workflows.
   A transactional bridge to the existing scheduled-execution outbox, an operator allowlist,
   and integration tests are still needed. Never present recorded starts as completed work.
4. **Real providers unverified.** Adapter tests use mocks only. A model may emit plain text
   instead of a tool object or poor Japanese; malformed/unsupported tool calls fail closed.
   Free model availability, data policies, billing settings and quotas must be checked
   in the actual provider account. Model IDs are deliberately not hardcoded to volatile offerings.
5. **Retention and privacy.** History can contain personal information and is stored as text
   in the existing private database. Existing database/backup access controls apply. Expired
   rows are excluded immediately; physical deletion runs on page access and must also be
   scheduled hourly via `python assistant_maintenance.py`, including after feature disablement.
   Backups retain historical content under the existing backup policy. Clear-history deletes
   chat content and cancels proposals, retaining action/usage audit entries until expiry.
6. **Process-local concurrency.** Existing per-minute/concurrency controls are per web process;
   daily budgets are durable across processes. Use one web worker for the staging trial.
   A socket timeout is not a total wall-clock deadline. Upstream proxy request deadlines and
   distributed concurrency control need verification before scaling.
7. No browser visual/mobile device audit, live PostgreSQL migration/concurrency run, image
   build, real-provider request or production smoke test is claimed by this implementation.

## Configuration and staging preparation

Use `.env.example` for the new settings. Provider keys stay on the server. Each key accepts
either its environment variable or a preferred `_FILE` path (UTF-8, maximum 4096 characters).
Never put real keys in Git, model IDs, browser forms, screenshots or this document.

For local Qwen, reuse `ABAP_INTEGRATIONS_ENABLED=true`,
`ABAP_EXTERNAL_PROVIDER=llama_cpp`, and the existing validated `ABAP_LOCAL_AI_*`
configuration. No local server was started or downloaded as part of this change.

For remote adapters, configure explicit model IDs and keys, verify provider account
settings and data policies, and only then set `ABAP_ASSISTANT_REMOTE_APPROVED=true`.
For a compatible adapter the URL is an operator-controlled complete HTTPS chat-completions
endpoint. Untrusted browser input cannot supply endpoints, keys or model registry entries.

Migration `014_advanced_assistant.sql` adds `assistant_entries` and `assistant_budgets`
with supporting indexes. PostgreSQL uses the existing versioned migration runner;
SQLite creates this additive schema only when the advanced workspace/store is used.
Do not apply migrations to production during local development.

Optional Compose overlay: `compose.advanced-assistant.yaml`, combined with
`compose.deploy.yaml`. It passes only explicit assistant settings to `web`; flags
default false. The Dockerfile already copies the new modules/static/templates/catalogs.
For secret-file deployment, supply a separate reviewed override mounting Docker secrets
and setting the corresponding `_FILE` variables. This overlay uses server environment
credentials by default; it does not create or provision provider accounts.

Before an isolated staging deployment:

1. Build the image and run migration 014 on a disposable PostgreSQL database.
2. Verify migration reapplication, foreign keys, concurrent action claims and durable
   budget reservations across two connections/processes; use synthetic data only.
3. Run tests and schedule hourly retention maintenance using the same database settings.
4. Enable only the staging flag. Sign in as two distinct administrators and a viewer.
5. Check model choice, consent, EN/JA responses, denial of another user's records,
   exact action review, cancel/confirm/repeated confirm, account revocation, daily/rate
   limits, and the public RAG/chatbot and existing assistant regression paths.
6. Monitor generic audit outcomes plus numeric usage entries; never log questions,
   contact details, credentials, raw provider error bodies or authorization headers.
7. Resolve production blockers above and perform a keyboard/mobile visual review.

## Rollback

Disable `ABAP_ADVANCED_ASSISTANT_ENABLED` and recreate only the reviewed web service
using the existing deployment procedure. The old assistant page resumes. Keep remote
approval false when unused. Retain additive tables and hourly cleanup; do not drop them
or restore the entire business database as a routine rollback. Pending proposals expire
after ten minutes. Reconcile any claimed/failed action against business audit records;
never retry an ambiguous action automatically. Previous image rollback follows the
existing release procedure. Production rollout requires separate explicit authorization.

## Portfolio demonstration

Use synthetic contacts/invoices and a deterministic provider or reviewed local Qwen.
Show an owned-lead query, minimized tool result, Japanese response selection, a draft
lead proposal with exact parameters, explicit confirmation, and duplicate rejection.
Explain that permission checks and action claims are enforced by Python/database code,
while the language model only proposes an operation. Describe n8n dispatch and tenant
support as remaining work, not completed capabilities.

## Validation record

Final test counts and deployment readiness are recorded in
`docs/architecture/advanced-assistant-validation.md`. Local command output is retained
under `output/advanced-assistant-*.log` (ignored working artifacts).
