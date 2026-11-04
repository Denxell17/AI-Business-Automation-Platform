> Current scope: [server-enforced synthetic/public-only release](../deployment/advanced-assistant-synthetic-release.md). Owner approved this restricted scope. Production preflight still awaits SSH unlock; no activation/migrations/deployment.

> Current readiness is **NO-GO**: [production preflight](../deployment/advanced-assistant-production-preflight.md) found a provider data-policy restriction and blocked SSH/backup checks. Earlier inference-only conditional readiness is superseded.

# Dedicated OpenRouter $0-key live validation

Date: November 3, 2026. **CONDITIONAL GO for a separately approved controlled
production release**, subject to server secret/evidence installation, current proof,
provider data-policy review and the existing deployment/backup/rollback checks.
Production has not been activated, changed, committed, pushed or deployed.

## Results

| Check | Result |
| --- | --- |
| Dedicated key authentication | **PASS** — OpenRouter GET /api/v1/key authenticated |
| Key credit cap | **Confirmed $0** before and after testing; it was never increased |
| Actual free-model inference with that $0 cap | **PASS**, eight successful synthetic calls |
| English, Japanese, structured ABAP business-tool protocol | **PASS on both models below** |
| Manual model switching | **PASS** — both selected IDs returned SWITCH_OK through one gateway |
| Per-response reported cost | **0 for all eight successful calls** |
| Post-test key usage / daily usage | **0 / 0 as reported by OpenRouter** |
| Paid fallback | Disabled; explicit :free IDs, zero-price routing ceilings and allow_fallbacks=false |
| Unknown/unconfigured model | Rejected before a network request |
| Quota/error handling | Actual HTTP 429 observed; existing safe gateway error handling and mocked concurrency/quota regressions passed |
| Relevant regression | **52 passed, zero failures/skips**, 23.610 seconds |

**The $0 cap works for these two free models in this test.** This does not promise
unlimited availability or guarantee other free endpoints will accept a request.

## Validated models and language/protocol evidence

| Model | English marker | Japanese synthetic answer | Structured response |
| --- | --- | --- | --- |
| `nvidia/nemotron-3.5-lightning:free` | PASS | 業務の確認を徹底し、ミスを防ぎます。 | `{"tool":"leads"}` |
| `cohere/north-mini-code:free` | PASS | 要求されたタスクを理解し、受け付けたことを確認いたします。 | `{"tool":"leads"}` |

The structured response is ABAP's validated text/JSON tool proposal protocol. No
business records were sent, no lead data was read by these probes and no business write
was executed. Native API function calling remains separately marked unverified; it is
not required by this gateway. Model-native tool advertisement alone was not treated as
successful native execution.

Two additional calls, one per model, verified explicit switching using SWITCH_OK.
All generation calls used the existing gateway with fixed requested model IDs, no
fallback model list and provider price ceilings of zero. No paid model or local Qwen
was tried as a fallback.

## Unavailable candidates and upstream limits

Initial `google/gemma-4-26b-a4b-it:free` and `google/gemma-4-31b-it:free` requests failed.
Direct safe diagnostics confirmed HTTP 429, with provider metadata identifying
`upstream_provider_shared_pool`. A tiny `liquid/lfm-2.5-2.6b:free` diagnostic also returned
429. These observations did not show a key-budget rejection. The zero key budget was
left intact while other zero-price model families were tested.

`recursive/flint-v1.0:free` and `thinkingmachines/inkling-small:free` did not pass this run
and returned the gateway's safe provider_error category; their raw provider error bodies
were not logged. They were excluded from the validated model configuration.

OpenRouter reported free-tier status and an allowance snapshot of 50 requests, used=0,
remaining=50 both before and after the successful probes. That counter did not reflect
the eight observed successful requests during this test, so it is recorded as provider
telemetry, not claimed as an exact remaining entitlement. ABAP's own durable counters
remain separate. Operator validation probes consume upstream capacity but do not run
under an ABAP user's application budget. Free pools can throttle before an account's
reported daily ceiling.

The first diagnostic attempt added HTTP-class instrumentation that failed locally before
sending requests. It was discarded and the live checks were rerun through the unmodified
HTTP transport. No application code was changed to bypass provider errors or price rules.

## Secure local configuration

The real key remains only in the protected file:
`C:/Users/user/.abap-secrets/openrouter-api-key.txt`.
Neither its value nor raw authorization headers were printed, logged, committed or
included in command arguments. The dedicated name supplied by the owner was not used
as proof; actual authenticated key metadata established the zero cap.

Ignored local `.env` now contains the key-file path, the two validated free model IDs,
and `ABAP_ASSISTANT_CLOUD_VALIDATION_FILE` pointing to
`C:/Users/user/.abap-secrets/openrouter-model-validation.json`.
That private manifest contains metadata and a credential fingerprint, not the raw key.
Its fingerprint was checked against the gateway's actual credential loader.

`ABAP_ADVANCED_ASSISTANT_ENABLED=false` and `ABAP_ASSISTANT_REMOTE_APPROVED=false`
remain stored. An in-memory approved configuration preview selected exactly the two
verified models; no stored activation flag was changed. The production server still
needs its own approved secret-file and read-only evidence mounts. No laptop or local
model server is a production dependency.

Earliest proof expiry for this run: **2026-11-04T05:36:25.953127+00:00**. Repeat validation before expiration
or credential/model changes. Availability can change before then; quota errors still
trigger cooldown and require manual switching.

## Evidence and regression

Safe local artifacts (no raw key):

- `output/cloud-validation/key-access.json`
- `output/cloud-validation/openrouter-live-results.json` — successful synthetic answers and numeric usage
- `output/cloud-validation/openrouter-safe-diagnostics.json`
- `output/cloud-validation/openrouter-budget-diagnostics.json`
- `output/cloud-validation/openrouter-final-state.json`
- `output/cloud-validation/openrouter-regression.log`

Regression scope: cloud eligibility/zero-price guards, credential proof, shared quotas,
concurrency, switching, unavailable responses, assistant authentication/CSRF and public
RAG browser routes. All 52 passed. Earlier full PostgreSQL snapshot (907 passed) and
real isolated n8n/browser staging evidence remain unchanged; a complete repeat was not
needed because this session changed no application code.

## Remaining release conditions and approval

No live-provider blocker remains for these two models at the observed $0 cap. Remaining
conditions are operational: install the protected key and fresh validation evidence on
the intended server, review selected free-provider data policies before sending real
business data, verify the reviewed candidate image/pending migrations 014/015 and backup,
and follow the existing production smoke/rollback procedure. Free models are limited,
shared services; availability and quota are not guaranteed.

**CONDITIONAL GO**, not activation authorization. A separate explicit approval must
identify the reviewed release/image or commit, pending migrations, target services,
exact n8n allowlist, these cloud model IDs and data-sharing policy, validation-refresh
plan, and whether to enable the advanced assistant. None of those production changes
was performed here. Public RAG and the private n8n integration were not modified.
