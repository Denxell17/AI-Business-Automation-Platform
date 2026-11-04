> Historical baseline: current follow-up implementation and release gates are in [the final mission report](advanced-assistant-final-validation.md).

# Advanced assistant consolidated development report

Date: November 3, 2026. **Production deployment readiness: NO-GO.**
The local feature is implemented and disabled by default. The full mission's production
definition of done is not met. Production services, databases, workflows, backups and
provider accounts were not modified. Nothing was committed, pushed or deployed.

## Features implemented and why

The existing authenticated assistant now has an optional advanced workspace with
multi-model selection, controlled business-data tools, explicit business-action review,
private history, English/Japanese response selection and usage controls. The language
model proposes operations; Python permission checks and database claims decide whether
they may run. This keeps authorization outside prompts.

Read tools cover owned leads, related customers, self-created related invoices,
sample overdue/outstanding figures, permitted directory fields, owned workflows/recent
runs and self-authored CRM activity. Queries are bounded and minimize personal fields.
Business-data retrieval/sharing requires a per-request checkbox.

Write proposals cover lead creation/update, conversion of a qualified lead to a customer,
USD draft invoices and manual workflow execution records. Exact arguments, implied copied
contact information or invoice totals, and current object snapshots are displayed.
Proposals expire after ten minutes. Confirmation revalidates the account, permissions,
ownership, input, object version and business rules; a durable single-use claim rejects
duplicate confirmation. Cancellation is supported. No destructive, bulk, payment or
external-communication tool exists. Follow-up reminders can be drafted as text only.

History stays on the server and is scoped to account/session version. Questions are
independent: prior chat history is not included in model context. Logical retention is
seven days. Hourly physical cleanup is prepared as a maintenance command, not installed
in production. Budget reservations survive restarts: 100 model calls/user/day and
1000 globally/day, UTC. Provider numeric usage/cost metadata is stored where supplied;
missing pricing remains unknown. The UI shows the current user's daily call count.

## Existing functionality reused

- Authentication/session refresh, roles, CSRF, CSP, private caching and audit logging.
- Provider rate/concurrency limits and existing local llama.cpp/Qwen provider.
- Contact validation, lead stage transitions, qualified-lead conversion and CRM audits.
- Decimal-safe invoice calculations and existing invoice creation service.
- Active manual workflow validation, execution records and task snapshots.
- Application layout/styles and gettext English/Japanese localization.
- Versioned PostgreSQL migration runner, database backend adapter and Docker image layout.
- Existing signed n8n webhook/replay/outbox infrastructure was preserved; it is not
  newly invoked by the assistant.

## Files changed by this mission

Paths below are relative to the repository root; existing unrelated uncommitted work
was preserved. Shared files received only the assistant additions described here.

| File | Purpose |
| --- | --- |
| `Projects/employee_management_system/assistant_gateway.py` | Explicit registry and remote/local text adapters; sanitized failures and usage |
| `Projects/employee_management_system/assistant_tools.py` | Strict schemas, scoped reads, action validation, review snapshots, service delegation |
| `Projects/employee_management_system/assistant_store.py` | Private history, atomic action claims, retention, durable daily budgets |
| `Projects/employee_management_system/advanced_assistant.py` | Bounded proposal/read/summary protocol and response language |
| `Projects/employee_management_system/advanced_assistant_web.py` | Authenticated/CSRF-protected routes, confirmation, body limits and safe errors |
| `Projects/employee_management_system/assistant_maintenance.py` | Physical retention maintenance entry point |
| `Projects/employee_management_system/web_app.py` | Route registration and feature-gated page redirect |
| `Projects/employee_management_system/templates/advanced_assistant.html` | Model/language/consent/history/action review UI |
| `Projects/employee_management_system/static/advanced-assistant.js` | Accessible loading status and duplicate-submit prevention |
| `Projects/employee_management_system/migrations/postgresql/014_advanced_assistant.sql` | Additive assistant storage schema |
| `Projects/employee_management_system/tests/test_advanced_assistant.py` | 23 new adapter/service/store/web tests |
| `Projects/employee_management_system/tests/test_postgresql_migrations.py` | Register migration 014 in existing schema expectations |
| `Projects/employee_management_system/translations/messages.pot` | New UI message IDs |
| `Projects/employee_management_system/translations/ja/LC_MESSAGES/messages.po` | Japanese translations, preserving existing entries |
| `Projects/employee_management_system/translations/ja/LC_MESSAGES/messages.mo` | Compiled Japanese catalog |
| `.env.example` | Disabled flags and empty provider credential/model templates |
| `compose.advanced-assistant.yaml` | Optional web-only deployment environment overlay |
| `docs/architecture/advanced-assistant.md` | Architecture, limitations, staging, maintenance, rollback and portfolio demo |
| `docs/architecture/advanced-assistant-validation.md` | This consolidated report |
| `docs/roadmap/full-platform-completion-roadmap.md` | Concise current status and next development step |

## Database migrations

Migration 014 adds `assistant_entries`, `assistant_budgets`, and user/expiry indexes.
No existing business table is rewritten or dropped. PostgreSQL application/reapplication
on a live server remains unverified. SQLite equivalent schema creation, foreign-key use,
durable reservations and concurrent action claims ran against disposable databases.
No production migration was run.

## Executed validation

| Check | Result |
| --- | --- |
| Full application regression suite | 879 run: **864 passed, 15 skipped, 0 failed**; 192.134 seconds |
| Final focused suite after incremental changes | **58 passed**, 0 failed/skipped; 19.242 seconds |
| Final Japanese proposal/no-write-before-confirmation check | **1 passed** after final terminology addition |
| New Python module compilation | Passed |
| Docker Compose base + assistant overlay, synthetic configuration | Passed; advanced and remote-approval flags asserted false |
| Working diff whitespace checks | Passed |

The full regression run preceded the final focused additions; the 58-test focused suite
covers the final assistant, legacy assistant browser routes, localization and migration
contract. Counts overlap and must not be added as unique tests.

The 23 new tests cover owner-scoped/minimized reads, stale/inactive accounts, viewer
denial, malicious/unknown tools and extra arguments, cross-user writes/history/claims,
no write before confirmation, cancellation, expiry/session boundaries, concurrent
duplicate claims, durable daily caps, explicit sharing consent, scoped summary payloads,
provider errors, model switching, local-provider reuse, Gemini/OpenRouter/compatible
payloads, secret-file configuration, free-only OpenRouter registry, HTTP quota/redirect/
timeout/size failures, customer/invoice ownership, manual workflow ownership and n8n
rejection, authentication/CSRF, escaped rendering, history deletion, oversized forms
and stale-review rejection.

All 15 regression skips require `ABAP_TEST_DATABASE_URL`: CRM (1), invoices (1), n8n
durability/concurrency/callbacks (9), general PostgreSQL integration (3), and worker
concurrency (1). No disposable PostgreSQL URL was available. Docker's CLI was present
but its engine was not running; image build/container checks could not run. No live
provider or production smoke calls were made. Visual/mobile browser review remains open.

Initial restricted Windows test runs could not create a working internal loopback socket;
test execution succeeded outside that process restriction with synthetic temporary files
under `output/assistant-test-tmp`. Stalled diagnostic test processes were stopped.
One initial assertion expected `no-store` exactly; ABAP correctly emits `private, no-store`.
The assertion was corrected and final suites passed. No unresolved executed test failure
remains. Detailed command logs are local ignored artifacts in `output/`.

## Models and actual limitations

| Adapter | Implemented boundary | Remaining verification |
| --- | --- | --- |
| Gemini | Explicit operator model IDs; REST text requests with server-side key | Actual available models, account billing/free quota, privacy and Japanese/tool-proposal quality |
| OpenRouter | Explicit `:free` IDs only; compatible chat-completions requests | Live availability, account quota, data policy and actual provider usage |
| Local Qwen | Reuses existing validated loopback llama.cpp integration | Running local model/server quality and resources; no server was started |
| Compatible HTTPS | Operator-controlled complete chat-completions URL and explicit IDs | Endpoint compatibility, billing and data policy |

Protocol implementation follows the [Gemini generation API](https://ai.google.dev/api/generate-content)
and [OpenRouter's API entry point](https://openrouter.ai/developers). These references
do not establish the user's actual account quota or zero cost. No native tool-call or
structured-output support is assumed; a model can fail to emit a valid proposal and
the application will not execute an unsupported call. No paid fallback exists.

## Security findings and remaining blockers

1. **Atomic business writes:** claims and domain writes use separate transactions.
   An ambiguous crash is fail-closed and requires manual reconciliation. Existing
   services still have a concurrent ownership/status-change race between revalidation
   and commit. Production writes need transaction-aware services with atomic ownership,
   object-version and action-result handling. Distinct proposal IDs are distinct actions.
2. **Tenant isolation:** ABAP has no tenant key. This implementation is for one existing
   organization, with stricter ownership scoping for CRM/workflows and existing shared
   employee permissions. Multi-tenant isolation cannot be claimed or tested against
   a nonexistent tenant schema.
3. **n8n dispatch:** the assistant can inspect permitted workflow state and record a
   confirmed manual start. It rejects n8n-enabled starts. The existing worker/outbox
   path needs a transactional, allowlisted assistant bridge and integration tests.
   No Job Scraper or production workflow was changed.
4. **External validation:** disposable PostgreSQL migration/concurrency, image build,
   live provider/account verification, keyboard/mobile visual QA and staging smoke
   tests remain required. Secret values or production customer records were not used.
5. **Operations:** physical retention scheduling is prepared but not installed.
   Concurrency remains per web process; durable daily caps are shared. Confirm upstream
   wall-clock deadlines and distributed limits before scaling. Stored history follows
   existing database/backup privacy controls, including longer backup retention.

The complete mission is therefore unfinished, despite the working local implementation.
**Current ABAP status:** existing production/public RAG preserved; advanced assistant is
a tested local feature behind a default-off flag, not a production-complete milestone.
**Next step:** resolve transactional write guarantees, implement the allowlisted n8n
outbox bridge, and validate on disposable staging infrastructure.

## Deployment readiness and exact future approval

**NO-GO for production activation.** Disabled-feature staging preparation is reviewable;
the release gates above must be resolved first. Deployment and rollback instructions
are in `advanced-assistant.md`. Rollback disables the feature and retains additive tables;
it does not restore or destructively modify the business database.

After those gates pass, separate explicit authorization must name the reviewed release
image/commit, authorize migration 014 on the production ABAP database, the target web
service, selected provider/model configuration and reviewed billing/data-sharing policy,
and whether to enable the advanced feature. It must also approve the specific staging-
validated n8n allowlist if that bridge is included. No such production authorization
has been requested or inferred from this local-development mission.
