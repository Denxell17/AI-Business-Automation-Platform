# ABAP Full Platform Completion Roadmap

## Objective

Expand the current secure ABAP automation-core MVP into a demonstrable,
production-oriented business automation platform. The completed system must run
an end-to-end scheduled workflow through n8n, persist and display its result,
support the remaining coherent business modules, operate through PostgreSQL and
Docker, and be available from a secured public cloud URL.

This roadmap supersedes the earlier instruction to move directly into general
GoHighLevel study. Work remains incremental: complete and verify one milestone
before beginning the next.

## Existing Baseline

The repository already provides:

- Authenticated FastAPI application and approved responsive ABAP interface
- Administrator and viewer roles with default-deny permissions
- Employee management, payroll, workforce reporting, and CSV export
- Workflow definitions, ordered tasks, lifecycle rules, schedules, due-time
  evaluation, duplicate-safe occurrence claims, and manual execution history
- AI Agent Templates, protected execution records, and a one-off AI Assistant
- SQLite local support and PostgreSQL migrations/repositories
- Activity history, health/readiness endpoints, automated tests, Docker image,
  and PostgreSQL Compose deployment packaging

## Completion Principles

- Never weaken current authentication, authorization, CSRF, escaping, audit,
  database, or provider-safety boundaries.
- Never store secrets in Git, logs, browser pages, task payloads, or execution
  results. Use environment variables or the hosting provider's secret manager.
- External operations require timeouts, bounded payloads, idempotency,
  allowlisted destinations, safe failures, and an audit trail.
- Background processing must support retries without duplicating side effects.
- Use SQLite for fast local tests and PostgreSQL for production-equivalent
  verification. Never run integration or destructive tests against production.
- Build only real, permission-scoped features. Do not add inactive navigation,
  fabricated metrics, or placeholder integrations presented as complete.
- Every milestone ends with focused tests, the full regression suite,
  documentation, and a clean commit before the next milestone.

## Milestone 0 — Baseline and Delivery Controls

### Deliverables

- Confirm `main` is synchronized and the full test suite passes.
- Create a feature branch using the `codex/` prefix for the completion program.
- Add configuration contracts for worker, webhook, n8n, and integration values.
- Add an implementation status matrix to this roadmap and maintain it after
  every milestone.
- Define local, integration-test, staging, and production environments.

### Exit gate

- Baseline tests pass and no real credentials or application data are committed.

## Milestone 1 — Autonomous Scheduler and Worker

### Deliverables

- Create a dedicated worker process separate from FastAPI request handling.
- Poll and claim due schedule occurrences through the existing duplicate-safe
  claim service.
- Start workflow and task execution records transactionally.
- Implement bounded retries, exponential backoff, terminal failure handling,
  graceful shutdown, and stale-run recovery.
- Add structured operational logging and worker readiness visibility.
- Keep manual execution fully functional.

### Verification

- Unit tests for due, early, late, disabled, inactive, duplicate, retry, restart,
  concurrency, and shutdown scenarios.
- PostgreSQL concurrency test proving one occurrence produces one execution.
- Compose test proving the worker starts only after migrations and database
  readiness.

### Exit gate

- An enabled schedule automatically creates exactly one tracked workflow run.

## Milestone 2 — Secure Webhook and Integration Foundation

### Deliverables

- Add integration configuration with destination allowlisting.
- Define versioned outbound and inbound webhook schemas.
- Sign outbound requests and verify inbound signatures using separate secrets.
- Add timestamp windows, nonce or event-ID replay protection, request-size
  limits, strict content types, timeouts, and safe response bounds.
- Store delivery attempts, response status, retry state, correlation IDs, and
  sanitized failure information without storing secrets.
- Add administrator-only integration status and delivery-history views.

### Verification

- Tests for valid signatures, invalid signatures, replay, stale timestamps,
  oversized bodies, disallowed destinations, timeout, retry, malformed response,
  duplicate callback, and redacted logs.

### Exit gate

- A deterministic local receiver can complete the authenticated round trip once
  and duplicate callbacks cannot duplicate outcomes.

## Milestone 3 — n8n End-to-End Automation

### Deliverables

- Add a pinned n8n service and persistent n8n data to a development Compose
  profile; do not expose n8n publicly by default.
- Create one exportable, documented n8n workflow for the portfolio demo.
- Send an ABAP workflow execution to n8n using the secure outbound contract.
- Perform one useful external or AI action through an approved test provider.
- Return the result through the signed ABAP callback.
- Complete or fail the ABAP task and parent execution with a safe summary.
- Display delivery and execution state in the approved ABAP interface.

### Verification

- Run a full local Compose demonstration from scheduled claim to displayed
  result.
- Test n8n unavailable, delayed, duplicate, invalid-signature, invalid-payload,
  external-provider failure, and successful completion scenarios.

### Exit gate

- The eight-step ABAP → n8n → external action → ABAP demonstration works
  repeatedly without duplicate side effects.

## Milestone 4 — Leads and Customers Domain

### Deliverables

- Add normalized Lead and Customer models, migrations, repositories, services,
  permissions, activity events, API routes, and approved UI screens.
- Support lead creation, editing, lifecycle stages, owner assignment, notes,
  searching, and conversion into a customer.
- Support customer identity, contact details, status, related leads, and audit
  history.
- Prevent duplicate conversion and preserve immutable source references.
- Replace dashboard placeholders with permission-scoped real metrics.

### Exit gate

- An authorized user can manage a lead, convert it once, and view the resulting
  customer and audit history through PostgreSQL-backed ABAP.

## Milestone 5 — Invoices and Documents Domain

### Deliverables

- Add customer-owned invoices, immutable line-item snapshots, totals, currency,
  status transitions, due dates, and payment-state history.
- Use decimal-safe calculations and explicit rounding rules.
- Add protected document metadata and storage-provider abstraction.
- Validate file type, size, ownership, authorization, safe filenames, and
  download headers. Keep document storage private.
- Generate one portfolio-safe invoice document and connect it to a workflow.
- Replace dashboard placeholders with real permission-scoped information.

### Exit gate

- An authorized user can create a customer invoice, generate/retrieve its
  protected document, and trigger a tracked workflow without exposing files.

## Milestone 6 — Selected External Connections

### Deliverables

- Implement only the connections required by the portfolio flow, starting with
  n8n and one approved AI or business API.
- Add provider-independent adapters, connection tests, rate-limit handling,
  timeouts, credential validation, and safe error translation.
- Add integration health and delivery metrics based on real stored events.
- Prepare a GoHighLevel adapter only after webhook contracts and customer
  ownership are stable.

### Exit gate

- Each advertised integration has a repeatable test/demo, documented scopes,
  failure behavior, and credential-rotation procedure.

## Milestone 7 — Production Operations

### Deliverables

- Add PostgreSQL-native automated backups, retention policy, encrypted storage,
  and restore drills into an isolated database.
- Add activity/application log rotation and retention.
- Add worker, webhook, database, integration, and queue-depth health signals.
- Add deployment runbook, backup runbook, incident checklist, rollback plan,
  and release checklist.
- Add dependency and container vulnerability review without publishing secrets.

### Exit gate

- A backup restores successfully in isolation and a documented rollback drill
  returns the application to a verified healthy state.

## Milestone 8 — Cloud Deployment and HTTPS

### Deliverables

- Select and document the approved host, domain, cost limit, and environments.
- Deploy the pinned ABAP image, worker, PostgreSQL, and required private
  services using the platform secret manager.
- Configure a valid TLS certificate, HTTPS redirect, trusted proxy settings,
  restricted database networking, secure cookies, and least-privilege access.
- Keep n8n private or protect it with appropriate authentication and network
  restrictions.
- Configure liveness, readiness, alerts, persistent volumes, backups, and log
  retention.
- Run staging verification before production promotion.

### Exit gate

- ABAP is reachable from the approved HTTPS cloud URL, survives restart,
  retains data, reports healthy/readiness correctly, and completes the n8n demo.

## Milestone 9 — Final Portfolio Release

### Deliverables

- Update README, architecture diagram, screenshots, API/webhook contracts,
  deployment instructions, demo data procedure, and troubleshooting guide.
- Record actual automated, PostgreSQL, Compose, security, backup/restore, and
  cloud smoke-test evidence.
- Create a concise demonstration script covering the complete end-to-end flow.
- Clearly label any intentionally deferred features.
- Tag the verified release only after all exit gates pass.

### Final acceptance scenario

1. An administrator creates and activates an ABAP workflow.
2. PostgreSQL stores its tasks and schedule.
3. The worker claims the due occurrence exactly once.
4. ABAP sends a signed, allowlisted webhook to n8n.
5. n8n performs the approved external or AI action.
6. n8n sends a signed result callback to ABAP.
7. ABAP records and displays delivery, task, and workflow outcomes.
8. The complete system operates through Docker from a secured public HTTPS URL.
9. The same demonstration connects a lead/customer and, where applicable, an
   invoice or protected document to the tracked automation.

## Definition of Done

The completion program is finished only when:

- Every milestone exit gate above is satisfied with evidence.
- All advertised modules use real persisted data and enforced permissions.
- The full automated suite passes, including new worker/webhook/domain tests.
- Live PostgreSQL, isolated Compose, backup/restore, and cloud smoke tests pass.
- No secrets, private data, placeholder production credentials, or unsafe
  external destinations exist in the repository.
- `main` and `origin/main` contain the verified release and the working tree is
  clean.

## Current Status

| Milestone | Status | Evidence / gate |
| --- | --- | --- |
| 0 — Baseline and Delivery Controls | Complete | On 2026-09-17, `HEAD`, `main`, and `origin/main` were verified at commit `123044d`; branch `codex/full-platform-completion` is active. Environment and configuration contracts are recorded in `.env.example` and `Notes/abap_environment_configuration.md`. The full suite passed in the project-local Python 3.14 environment: 631 tests passed, 3 PostgreSQL integration tests skipped because no integration database was configured. Common tracked-file credential signatures were absent. `.venv/` and generated activity logs are ignored; no application database, export, or secret file is tracked. No external/cloud behavior was claimed or verified. |
| 1 — Autonomous Scheduler and Worker | In verification | A separate `workflow_worker` process claims due schedule occurrences and atomically creates one schedule-triggered workflow execution with task snapshots. It has bounded exponential retries, interruptible retry shutdown, stale-run recovery, structured safe logs, and a Compose health check. SQLite-focused coverage verifies due, early, late, disabled, inactive, duplicate, retry, restart, shutdown, and stale recovery behavior. The full local suite passed: 641 tests ran with 4 optional PostgreSQL tests skipped because `ABAP_TEST_DATABASE_URL` was not configured. `docker compose -f compose.deploy.yaml config --quiet` passed using isolated synthetic values. Live PostgreSQL worker concurrency and Compose startup were not verified: the local Docker Desktop engine was unavailable. The exit gate is therefore not marked complete. |
| 2 — Secure Webhook and Integration Foundation | Not started | No webhook behavior is claimed. |
| 3 — n8n End-to-End Automation | Not started | No n8n or external/cloud behavior is claimed. |
| 4 — Leads and Customers Domain | Not started | Exit gate not evaluated. |
| 5 — Invoices and Documents Domain | Not started | Exit gate not evaluated. |
| 6 — Selected External Connections | Not started | No provider connection is advertised. |
| 7 — Production Operations | Not started | Exit gate not evaluated. |
| 8 — Cloud Deployment and HTTPS | Not started | No cloud deployment is claimed. |
| 9 — Final Portfolio Release | Not started | Exit gate not evaluated. |

## Immediate Next Action

Start the local Docker Desktop engine, then use an isolated test project and
synthetic credentials to run the Compose startup check and the live PostgreSQL
concurrency test. Verify that one enabled schedule produces exactly one tracked
run, record that evidence, and only then mark Milestone 1 complete. Do not
begin webhook or n8n work until the exit gate passes.
