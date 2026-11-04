> Latest: [dedicated OpenRouter $0-key live results](advanced-assistant-openrouter-live-validation.md). Two cloud models passed real English/Japanese/protocol and switching checks; production remains disabled.

> Current cloud-only production requirements and validation: [free-tier cloud report](advanced-assistant-cloud-validation.md). Local Qwen is not required; no laptop dependency.

# Final release-gate validation — November 3, 2026

**Production activation: NO-GO until live AI-provider validation passes.**
This report supersedes the remaining-gate status in the earlier final-validation report.
No production canary, production database/service change, paid provider call, commit,
push or deployment was performed. Application code and existing workflow sources were
not changed during this session.

| Gate | Result | Evidence |
| --- | --- | --- |
| Live AI providers | **BLOCKED** | No configured Gemini/OpenRouter credentials/model IDs or local Qwen model/endpoint |
| Private n8n round trip | **PASS** | Browser proposal/confirmation → real n8n 2.42.3 ingress/processor → signed callback → completed execution |
| Staging UI | **PASS within tested coverage** | Real browser, desktop and 390×844 mobile, EN/JA, tools, history, confirmation/cancellation, quota/error states |
| Final relevant regression/configuration | **PASS** | 82 tests passed, no failures/skips; default-off Compose assertions; unchanged workflow sources |

## Provider inspection and exact missing requirements

Checked the process environment and existing project .env without printing secret
values. Presence-only evidence is `output/final-gates/provider-presence.json`.
No new provider was provisioned and billing was not activated.

- Gemini: missing `ABAP_ASSISTANT_GEMINI_MODELS` and server-side
  `ABAP_ASSISTANT_GEMINI_KEY` or `_KEY_FILE`; common GEMINI_API_KEY/GOOGLE_API_KEY
  variables were also absent. Billing/free quota and data policy require operator review
  before remote approval is enabled. Authentication, live availability, EN/JA and live
  structured-tool output were **not run**.
- OpenRouter: missing `ABAP_ASSISTANT_OPENROUTER_MODELS` and server-side
  `ABAP_ASSISTANT_OPENROUTER_KEY` or `_KEY_FILE`; common OPENROUTER_API_KEY absent.
  A reviewed explicit `:free` model ID and quota/data policy are required. Live requests
  were **not run**.
- Local Qwen: missing configured `ABAP_LOCAL_AI_MODEL` and `ABAP_LOCAL_AI_BASE_URL`.
  A running loopback llama.cpp endpoint, the actual served model ID and existing validated
  local-provider settings are required. No local model was downloaded or assumed available.
- Compatible endpoint: no `ABAP_ASSISTANT_COMPATIBLE_URL` was configured. Such an adapter
  additionally needs explicit model IDs and server credentials under its existing settings.

No paid fallback remains enforced by the gateway and its regression tests: OpenRouter
paid IDs are rejected, model selection is explicit, provider failure does not switch
models. Staging used fixture-a and fixture-b **deterministic test providers**. Their
English/Japanese strings prove UI plumbing, not real model quality or authentication.
Never paste real keys into the chat or put them in browser fields/screenshots.

## Private n8n proof

Inspected the existing canary procedure as text only. Did not run its SSH commands or
connect to its production destination. Reused existing signed-workflow and processor
JSON files, HMAC verifier, outbox/retry worker, private provider, replay store and callback
handler in a newly created Compose project `abap-final-gates`.

The project had its own PostgreSQL, fresh n8n volume and two demo workflows, with
independently generated synthetic HMAC/token values. n8n/provider ports were not
published. Only the staging web port was published, bound to 127.0.0.1:58589.
The app image was the previously verified local candidate. A mounted staging-only
factory injected deterministic providers, seeded a synthetic administrator and allowed
only the owned `WF-GATE` workflow. Production feature flags/configuration were not edited.

Observed sequence:

1. Browser question proposed `start_workflow` with exact ID and reviewed n8n_enabled=true.
   A direct audit query showed **zero executions before confirmation**.
2. Clicked the explicit confirmation button. Exactly one action committed, including
   execution/tasks and its durable outbox record.
3. Existing retry worker delivered to real isolated n8n. Outbound audit: succeeded,
   attempt_count=1. n8n's durable event: completed, result_status=completed.
4. Signed callback audit: inbound accepted, attempt_count=1. ABAP execution reached
   completed: `WFE-2AD6E0C3E4BB41518B2BBD6AE92F02F3`.
5. Repeating confirmation returned **409**. Repeating the signed n8n event returned
   **202 duplicate**. Repeating its callback returned **200 duplicate**. These are
   idempotent acknowledgments; neither created a second event, execution or effect.
6. Expired callback signature returned **401**. Expired signed n8n ingress was rejected
   with a generic **500 Error in workflow**, rather than a mapped 401. Counts remained
   one execution/one n8n event. This is a diagnostic status-code limitation of the existing
   workflow error path, not successful acceptance. No workflow source was edited to
   change that response. Future ingress improvements should map verification failures
   to an authentication status; current retryable 500 classification is an operational caveat.
7. On mobile, a second proposal was cancelled. Final audit: one completed execution,
   one completed action, one cancelled action, one succeeded outbound and one accepted
   inbound delivery.

`n8n list:workflow` showed only `abapM3Demo000001` and `abapM3Demo000002` in this fresh
instance. Git diff confirmed the original two demo JSON files unchanged. No unrelated
workflow, Job Scraper or production n8n installation was accessed.

Replay evidence: `output/final-gates/roundtrip-results.json`; synthetic verification
script: `output/final-gates/roundtrip-check.py`. A temporary assertion originally expected
403 for expiration; it was corrected to ABAP's actual 401 contract and the checks passed.
The first staging startup raced database readiness; web and retry were started again
once the disposable database/migrations were ready. No application change was needed.

## Graphical UI validation

Used the supported browser automation surface and inspected screenshots/accessibility
state in the actual Docker-hosted staging application. Browser interactions covered:

- Sign-in; assistant navigation/rendering; two model options; manual A→B selection.
- English response and Japanese response; independently changed interface language to
  Japanese while response language remained English; observed preserved history.
- Explicit data-sharing checkbox; minimized owned synthetic lead result with ID, name,
  company and stage; expandable tool result separate from assistant text.
- Exact pending-action review, confirmation, completed state and mobile cancellation.
- Injected provider-unavailable error rendered safely; synthetic user budget set to its
  daily cap rendered the Japanese error and 100/100 without a provider request.
- Desktop navigation and two-column layout; mobile 390×844 stacked layout/navigation.
  Measured no document horizontal overflow; Japanese review parameters wrapped visibly.
  Keyboard Tab moved from question to consent checkbox; mobile confirm/cancel controls
  were focusable, visible and usable.

Evidence screenshots:

- [Desktop business result](../../output/final-gates/desktop.png)
- [Mobile error state](../../output/final-gates/mobile.png)
- [Mobile Japanese confirmation](../../output/final-gates/mobile-confirmation.png)

This is one-browser desktop/mobile-emulation coverage, not physical-device,
cross-browser, screen-reader or formal accessibility certification. Loading-state timing
was not independently stress-tested. Existing UI/rate/CSRF/authorization tests supplement
these checks. No real provider response is claimed by screenshots.

## Regression, migration and deployment checks

82 relevant regression tests passed in 31.166 seconds, **zero failures/skips**:
assistant/gateway/store, atomic actions, legacy assistant browser routes, localization,
private n8n provider, webhook delivery and PostgreSQL migration contracts.
Log: `output/final-gates/regression.log`. No application code changed, so the previously
verified **896-test PostgreSQL-enabled baseline** and Docker build remain the full-suite
baseline; a second full run was not needed for documentation/staging-only changes.
Staging applied the existing migrations, including 014, in the fresh PostgreSQL database.

Production Compose validation used synthetic settings and asserted:
`ABAP_ADVANCED_ASSISTANT_ENABLED=false`, `ABAP_ASSISTANT_REMOTE_APPROVED=false`, and an
empty assistant n8n allowlist. Whitespace checks passed. Existing public RAG, business
functions, backups and monitoring configurations were preserved.

Temporary stack/volume/network and generated synthetic secret/config files were removed
after evidence collection. Screenshots, sanitized evidence and scripts remain under output.
The mounted staging factory is **not** production code and must never be used to release
an image or bypass real provider testing.

## Decision and exact next step

**NO-GO for production activation** solely on the unresolved live-provider release gate;
the n8n ingress status-code caveat above should also be accepted or improved in a reviewed
workflow revision before rollout. Controlled local/staging demonstration is supported.

To finish validation, provide/configure at least the intended release provider's explicit
model ID and credentials via existing server environment/secret-file settings, or a
running validated local Qwen endpoint/model. Remote settings also need reviewed billing,
quota and data policy. Then run authentication, model availability, EN/JA business-tool
responses, switching and unavailable-model checks against that actual provider.

After those checks pass, separate production approval must name the candidate image or
reviewed commit, migration 014, target web/worker services, exact workflow allowlist,
provider/model configuration and reviewed billing/data-sharing policy, and explicitly
authorize feature activation. Existing backup/rollback/smoke instructions remain in
`advanced-assistant-final-validation.md`; nothing has been committed, pushed or deployed.
