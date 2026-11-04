> Current readiness is **NO-GO**: [production preflight](../deployment/advanced-assistant-production-preflight.md) found a provider data-policy restriction and blocked SSH/backup checks. Earlier inference-only conditional readiness is superseded.

> Latest: [dedicated OpenRouter $0-key live results](advanced-assistant-openrouter-live-validation.md). Two cloud models passed real English/Japanese/protocol and switching checks; production remains disabled.

# Cloud-only free-tier assistant — implementation and validation

Date: November 3, 2026. **NO-GO for production activation: authenticated live cloud
validation is blocked by missing credentials/model configuration.** No production
service, database, n8n workflow, public RAG setting or billing account was modified.
No commit, push or deployment was performed.

This supersedes earlier references to local Qwen as a release requirement. Production
uses cloud APIs directly from the ABAP server. The owner's laptop and any local model
server are **not required**. The legacy local adapter remains an explicit development
option only; the production overlay disables it and the registry excludes it in
production even if its development opt-in is supplied.

## Completed changes

- Server-only Gemini, OpenRouter and compatible HTTPS adapters preserved behind the
  existing gateway. No anonymous business-tool access or authorization changes.
- Production selector fails closed unless a cloud model has fresh (24-hour) server-side
  free-eligibility, account-access and ABAP structured-tool-protocol validation evidence.
  Evidence is bound to the credential fingerprint; rotation/staleness disables it.
  Labels distinguish unverified/unavailable models from recently live-validated ones.
- OpenRouter requires explicit `:free` IDs. The validator discovers today's candidates
  from the provider catalog and excludes any nonzero pricing. Requests send zero prompt/
  completion price ceilings, disable upstream fallback and contain no fallback-model list.
- Gemini/compatible models additionally require a reviewed, explicit free-model allowlist
  and a billing-disabled/free-account review flag. These are operator attestations, not
  a claim that ABAP can query the provider's billing console. Gemini has no per-request
  free-only switch in this integration: a paid project's key must never be supplied.
- Provider errors/quota exhaustion mark model or provider cooldowns across users. Other
  eligible models remain manually selectable. No automatic paid or local fallback exists.
  A reported positive OpenRouter cost fails closed and blocks the model for 24 hours
  pending operator review; ABAP cannot reverse an upstream billing discrepancy.
- Daily and per-minute budgets, provider-wide sharing, and user/model/provider/global
  concurrency are reserved atomically in PostgreSQL. The existing per-process circuit
  breaker remains. Denied reservations roll back without consuming other budgets.
- A 45-second response watchdog supplements the existing 30-second socket timeout.
  Concurrency slots are released in finally blocks; five-minute leases recover crashes.
  No database transaction remains open during the cloud HTTP call. ABAP counts failed
  calls too; read summaries use two calls. Provider quotas remain separate.
- Localized quota/error messages and no-eligible-model state. Old assistant POSTs redirect
  to the advanced page when enabled, preventing a legacy-provider bypass.

## Public discovery versus authenticated validation

**Live authenticated providers validated: none. Live validated model IDs: none.**
Presence-only inspection of the current process and existing project .env found no
Gemini/OpenRouter keys, key-file references, configured cloud model IDs, compatible
credentials/endpoint or validation manifest. Common GEMINI_API_KEY/GOOGLE_API_KEY and
OPENROUTER_API_KEY variables were also absent. No credential values were printed.
Evidence: `output/cloud-validation/configuration-presence.json`.

A real unauthenticated request to [OpenRouter's model catalog](https://openrouter.ai/api/v1/models)
returned 14 explicit `:free` text-model candidates with zero advertised pricing. This is
catalog verification only; it does not establish authentication, current account quota,
actual inference access or native tool behavior. Snapshot:
`output/cloud-validation/openrouter-candidates.json`.

| Candidate ID | Eligibility evidence | Native function calling |
| --- | --- | --- |
| `recursive/flint-v1.0:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `xingchen-agi/xing4.0-29b-a4b:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `nvidia/nemotron-3.5-super-vl:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `dots-studio/dots-3-note-preview:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `liquid/lfm-2.5-2.6b:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `nvidia/nemotron-3.5-lightning:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `thinkingmachines/inkling-small:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `thinkingmachines/inkling:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `cohere/north-mini-code:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `nvidia/nemotron-3.5-content-safety:free` | $0 advertised catalog pricing | Not advertised |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `google/gemma-4-26b-a4b-it:free` | $0 advertised catalog pricing | Advertised; not live-tested |
| `google/gemma-4-31b-it:free` | $0 advertised catalog pricing | Advertised; not live-tested |

Google currently documents free input/output tiers for `gemini-3.5-flash-lite` and
`gemini-3.6-flash`. Those are documentation candidates, not authenticated API-validated
models or hardcoded defaults. Free-tier data-use terms also need review before business
data is shared. [Google pricing](https://aistudio.google.com/docs/pricing)

Gemini quotas vary by project/model; RPD resets at midnight Pacific, whereas ABAP's own
daily budgets reset in UTC. Actual project limits must be checked in AI Studio.
[Google rate limits](https://aistudio.google.com/docs/rate-limits)

OpenRouter account limits and remaining free-model allowance require an authenticated
`GET /api/v1/key`; no such account check was possible. Public catalog pricing does not
promise unlimited usage. [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits)
The zero-price routing ceiling and disabled provider fallback follow the
[provider-routing reference](https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/provider-selection.mdx).

ABAP uses a validated text/JSON business-tool protocol and does not require native
function calling. The operator validator checks an English marker, Japanese text and
exact read-only `{"tool":"leads"}` output. Native-tools advertisement and actual native
function-call verification are separate fields; native function calling is not claimed
as tested or used. No real business records are sent by the validation utility.

## Configurable server limits

All settings below use the `ABAP_ASSISTANT_` prefix. These are application safeguards,
not provider entitlements, promises of free capacity, or token quotas.

| Scope | Daily default | Per-minute default | Concurrent default |
| --- | ---: | ---: | ---: |
| User | 100 | 10 | 1 |
| User + model | 20 | User cap applies | User cap applies |
| Model (all users) | 40 | 20 | 2 |
| Provider (all models/users) | 40 | 20 | 2 |
| Global | 1000 | 60 | 4 |

Names: USER_DAILY_LIMIT, USER_MODEL_DAILY_LIMIT, MODEL_DAILY_LIMIT,
PROVIDER_DAILY_LIMIT, GLOBAL_DAILY_LIMIT; USER_PER_MINUTE, MODEL_PER_MINUTE,
PROVIDER_PER_MINUTE, GLOBAL_PER_MINUTE; USER_CONCURRENCY, MODEL_CONCURRENCY,
PROVIDER_CONCURRENCY, GLOBAL_CONCURRENCY. Limits are bounded positive integers.
Per-model defaults apply independently to every configured model. Provider counters cover
this assistant's calls; other applications using the same upstream account also consume
provider quota and may cause earlier rejection. Quota/availability cooldown is 60 seconds,
not a claim that upstream quota resets then. At expiry a fresh request can still fail.

## Exact missing configuration and prepared live validation

Configure intended models and keys on the **ABAP server**, never in the browser/chat:

- Gemini: `ABAP_ASSISTANT_GEMINI_MODELS`, `ABAP_ASSISTANT_GEMINI_KEY_FILE` (preferred)
  or GEMINI_KEY with the same prefix; `ABAP_ASSISTANT_GEMINI_FREE_MODELS` listing only
  currently reviewed free-tier IDs; `ABAP_ASSISTANT_GEMINI_FREE_ACCOUNT_REVIEWED=true`
  only after verifying the actual key's project is billing-disabled and free-tier eligible.
- OpenRouter: `ABAP_ASSISTANT_OPENROUTER_MODELS` with explicit discovered `:free` IDs,
  and `ABAP_ASSISTANT_OPENROUTER_KEY_FILE` or the corresponding KEY variable. Multiple
  configured model IDs may share the same server key and upstream quota.
- Additional compatible cloud provider: existing COMPATIBLE_MODELS, COMPATIBLE_URL,
  COMPATIBLE_KEY/KEY_FILE plus COMPATIBLE_FREE_MODELS and COMPATIBLE_FREE_ACCOUNT_REVIEWED,
  all under ABAP_ASSISTANT_. The operator must verify that endpoint/account's pricing.
- `ABAP_ASSISTANT_REMOTE_APPROVED=true` only after billing/quota/privacy review.
  This flag alone no longer makes a model selectable.
- `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE` pointing at a private server-side manifest
  produced by successful validation. Mount it read-only into the web container alongside
  secret files using a reviewed override. The Compose overlay passes paths but does not
  invent host mounts, keys, accounts or model IDs.

Prepared utility: `Projects/employee_management_system/assistant_cloud_validate.py`.
It is runnable inside the application image on the deployment/staging server, with no
owner-laptop dependency. `--discover-openrouter --output <path>` fetches only public
zero-price metadata. `--output <manifest-path>` validates explicitly configured approved
cloud models, at most five per invocation, using three synthetic generation requests
per model. Those checks consume upstream free quota, independently of application user
budgets. Gemini authentication/model support is checked before generation. Models not
currently free in the OpenRouter catalog are rejected before generation.

The manifest contains safe metadata/fingerprints, not keys or raw provider responses.
It records real access, English/Japanese and business-protocol success separately from
native-tool advertising. Failed models are omitted and not selectable. Refresh it before
its 24-hour expiry and after credential changes; schedule any such server task separately
within actual provider quotas. The code never enables billing or creates provider accounts.
Until keys/models are supplied, it reports `blocked_no_configured_models=true` and writes
an empty manifest. Current result: `output/cloud-validation/live-validation.json` is empty.

## Files changed

New: `assistant_cloud_config.py`, `assistant_cloud_validate.py`,
`migrations/postgresql/015_assistant_cloud_controls.sql`,
`tests/test_assistant_cloud_controls.py` (all under Projects/employee_management_system).
Updated there: `assistant_gateway.py`, `assistant_store.py`, `advanced_assistant.py`,
`advanced_assistant_web.py`, `web_app.py`, assistant template, gettext catalogs,
`tests/test_advanced_assistant.py`, `tests/test_postgresql_migrations.py`.
Updated configuration: `.env.example`, `compose.advanced-assistant.yaml`.
Documentation: this report and continuity links in existing architecture/roadmap records.

Migration 014 is unchanged. Additive migration 015 adds cloud-control mutex, concurrency
leases and safe cooldown status tables; existing budget storage is reused. No business
table or public RAG schema was modified. PostgreSQL uses the existing migration runner;
local SQLite creates the equivalent additive schema when its assistant store is opened.

## Executed tests and deployment verification

- Full PostgreSQL-enabled regression snapshot: **907 passed, 0 failed, 0 skipped**,
  216.564 seconds. `output/cloud-validation/postgresql-regression.log`.
- Final focused suite after subsequent small safety/UI changes: **76 passed, 0 failed, 0 skipped**, 24.084 seconds.
  `output/cloud-validation/final-focused.log`. Includes public RAG browser-route regression.
- Six additional live PostgreSQL cloud-control tests passed in 6.145 seconds: cross-user
  provider budgets, per-model caps, minute caps, shared concurrent lease acquisition,
  expired lease recovery and cooldown isolation. These ran in disposable schemas.
  `output/cloud-validation/postgresql-cloud-limits.log`.
- Earlier local full snapshot: 905 run, 884 passed, 21 environment skips, no failures.
  Superseded for PostgreSQL coverage by the no-skip live snapshot above. Counts overlap
  and must not be added as unique tests.
- Docker candidate build passed. All 15 migrations applied twice successfully in a
  separate disposable image-smoke database; 15 migration records were verified.
- Production-registry container check passed with local integration deliberately
  configured: local models were still excluded in production. Default-off assistant,
  remote approval, empty n8n allowlist and local-development=false Compose checks passed.
- Synthetic mocks cover quota exhaustion, HTTP 402/429, timeouts, malformed responses,
  model switching, unexpected positive cost, freshness/credential revocation, paid-model
  rejection and structured protocol. These are not real cloud-provider success claims.
- No code in public RAG or private n8n workflows was changed. Existing real n8n and UI
  staging evidence remains in `advanced-assistant-release-gates.md`; this session's
  focused/public-RAG and full regression checks passed. Whitespace checks passed.

The full snapshot preceded the final cost-response guard, legacy POST redirect and
small template/probe refinements; the final focused suite covers those affected paths.
The new candidate image is built from the final source. Temporary PostgreSQL test
container/network are removed after evidence collection; the local candidate image is
retained for review. No production flags were enabled.

## Status, rollback and production approval

Current ABAP status: cloud-only gateway and shared usage safeguards implemented;
existing business actions, confirmation and signed n8n integration preserved. Next step:
configure approved cloud credentials/model IDs and run the prepared live checks, including
at least one real model and two real IDs for live switching coverage.

**NO-GO for activation.** Actual account free-tier eligibility, authentication, model
availability and real EN/JA/tool-protocol behavior remain BLOCKED. No unlimited-free
promise is made. Local Qwen is not a blocker or required alternative.

Before separately authorized deployment, back up using the existing encrypted backup
runbook, apply pending migrations 014/015, mount validated server credentials/evidence,
and retain default-off flags until approved. Rollback disables the assistant and retains
additive tables; do not restore/drop business data as routine rollback. Existing outbox
records can still dispatch after disabling the assistant; retain the reviewed n8n worker
reconciliation procedure from the earlier final-validation report.

After live cloud checks pass, approval must name the reviewed image/commit, pending
migrations 014/015, target web/worker services, exact n8n allowlist, free-cloud model IDs,
verified billing/quota/data policy, server validation-refresh plan and feature activation.
No such production authorization is inferred from this local development request.
