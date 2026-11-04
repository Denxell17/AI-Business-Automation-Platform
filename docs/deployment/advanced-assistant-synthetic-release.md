# Synthetic/public-only release safeguards

November 3, 2026. Owner selected Option 2. This scope decision is implemented locally;
it does not authorize deployment, activation or production migrations.

**Production readiness: HOLD / NO-GO pending the remaining live-server preflight.**
Existing SSH identity is accepted by the server but encrypted/locked, and the local agent
was stopped at the last check. Server secret installation, live migration ledger, fresh
backup evidence, running-image comparison and actual workflow inventory remain blocked.
No server changes or production migrations occurred.

## Enforced boundary

`ABAP_ASSISTANT_DEMO_ONLY=true` is hardcoded in the proposed production overlay and
is also the application default when ABAP_ENVIRONMENT=production. Local ignored .env
is restricted too. Assistant activation and remote approval remain false. A later
unrestricted release requires a separate reviewed configuration/policy decision;
ordinary request parameters cannot change this server setting.

- The UI offers a fixed EN/JA prompt menu. Free-form text, uploads, user URLs, arbitrary
  public-data claims and custom business parameters are not accepted. Direct forged
  POST input is rejected server-side before the provider call. This removes the common
  path where a visitor might paste confidential content into an otherwise generic chat.
- All six assistant read tools return fixed fictional leads/customers/invoices/employees/
  workflows/activity fixtures. The lead demo may include that account's own isolated
  demo leads. Queries never read the real business repository in this mode. Existing
  authentication, active-account checks and permissions are still required.
- Provider prompts contain only the fixed selected question, static system/schema text
  and synthetic fixtures. Account identity, old chat history and real business records
  are not included. No arbitrary document or public URL fetch path was added.
- Both selected free OpenRouter models use the same boundary. There is no model-specific
  private-data exception. Synthetic/public use avoids the confidential/personal-data
  restriction found during preflight; this is not approval for future private-data use.
- One supported demo action is available: create a synthetic lead with fixed name
  `Synthetic Demo Lead`, fixed company `Fictional Company`, and stage `new`. Parameters
  come from server constants, not user/model suggestions. Ask creates a pending review;
  explicit CSRF-protected confirmation is required to insert the record.
- The record is inserted only in `assistant_demo_leads`, with ownership and a 20-record
  per-account cap. No CRM/customer/invoice/employee/workflow row is created or changed.
  No email, payment, webhook or live workflow is triggered. Other business actions and
  model-generated writes are blocked. Existing normal domain services remain intact.
- Confirmation, isolated insert, action state and completion history commit atomically.
  Account revalidation, ownership, expiry, duplicate protection and normal audit logging
  remain. Older real-business proposals cannot be confirmed or cancelled in demo mode.
  Demo proposals cannot be routed to real services if mode is later changed.
- Demo history uses an explicit `assistant_demo_entries` membership table. The UI queries
  demo entries only, so private prior history is not fetched for display. Clearing demo
  history removes only demo history/proposals, preserving older private history. Created
  demo leads remain isolated and count toward the 20-record cap.

The authorized ABAP application's ordinary CRM/payroll/invoice/workflow screens and
background services retain their own existing permissions and behavior. The new
restriction applies to the Advanced Assistant; it does not remove the owner's existing
business application. Public RAG and existing n8n workflows were not modified.

No general-purpose open-text AI chat is included in this initial release. Additional
approved public data must be curated and reviewed into the server fixture bank before
release; simply labelling client-supplied content as public is not accepted.

## Files and migration

New under Projects/employee_management_system: `assistant_demo.py`,
`migrations/postgresql/016_assistant_demo_leads.sql`, `tests/test_assistant_demo.py`.
Updated: `advanced_assistant.py`, `advanced_assistant_web.py`, `assistant_tools.py`,
`assistant_confirmation.py`, `assistant_store.py`, `business_transaction.py`, advanced
assistant template, gettext catalogs, and migration contract tests. Configuration updates:
`.env.example`, ignored local .env, `compose.advanced-assistant.yaml`, and the disabled
local preflight override/manifest. Current local candidate image: `sha256:d811c3f9388226f3b3356f82cf348beb9afde9d66ebf9dbbe136ed7d18fc64db`.

Migration 016 adds only isolated demo-lead and demo-history-membership tables. It does
not alter real business tables. Pending production migrations must be established from
the live ledger before approval; review 014/015/016 rather than assuming only 014 is
needed. No production ledger was queried or migration applied.

## Executed verification

- Full PostgreSQL-enabled regression snapshot: **928 passed, 0 failures/skips**,
  190.129 seconds (`output/cloud-validation/demo-postgresql-regression.log`).
- Final focused suite: **69 passed, 0 failures/skips**, 22.104 seconds
  (`output/cloud-validation/demo-final-focused.log`). This includes final fixture cleanup
  and authentication assertions, public RAG, old business actions, localization, browser
  tampering and migration contracts. Counts overlap; they are not unique totals.
- Eight additional live PostgreSQL boundary tests passed in 7.337 seconds in disposable
  schemas (`output/cloud-validation/demo-postgresql-boundaries.log`). They verify fixture-
  only reads, rejected private input, isolation, confirmation ownership/duplicates,
  rollback/concurrency, private-history preservation and no mode-switch bypass.
- Candidate Docker image built successfully. All **16 migrations** applied twice on a
  separate disposable smoke database; the ledger contains 16 records.
- Production default is synthetic-only in the candidate image. Merged proposal checks
  passed: demo_only=true, assistant=false, remote_approved=false, empty assistant n8n
  allowlist. Source whitespace checks passed.
- No new cloud inference was needed; the two prior model validations used synthetic
  prompts only. Their credential-bound evidence still needs refreshing before expiry
  and before server activation. No API key or SSH passphrase was printed.

No deployed visual/browser review of this new restricted menu is claimed. Its rendered
HTML and confirmation flows were exercised with the application TestClient. Earlier
responsive styling was preserved; a staging graphical smoke check remains in the final
release checklist. Temporary PostgreSQL resources are removed after verification;
the local candidate image and sanitized evidence are retained.

## Current preflight / deployment plan

The provider privacy condition is addressed **for this restricted data scope only**.
Do not remove the synthetic guard to obtain a more general demo. Retain the selected
NVIDIA and Cohere free IDs and $0 cap, with no paid/local fallback. Preserve the existing
shared usage limits, manual model switching and availability cooldowns.

After the owner unlocks the existing SSH identity locally, continue the previously
approved read-only server preflight: verify running release/overlays, exact migration
ledger, resource headroom, current encrypted snapshots/restore evidence, secret mount
ownership/readability and workflow inventory. Then stage unreferenced protected key and
fresh evidence files without printing them. The assistant-specific workflow allowlist
remains empty, and demo mode blocks workflow starts regardless of that list.

Compare the candidate against the running public-RAG/business release before selecting
service updates. Present the exact candidate image, complete pending-migration list,
backup ID, unchanged proxy/n8n/public-RAG settings, restricted data scope, quotas,
credential/proof refresh plan, smoke criteria and rollback image for separate deployment
authorization. Do not apply old deployment/canary scripts as preflight checks.

Only after explicit later approval: take the verified release backup, apply only approved
pending migrations once, replace approved services, smoke the disabled configuration,
and activate only the restricted assistant if authorized. Rollback disables assistant
flags and restores the reviewed image/config; retain additive tables and reconcile any
older outbox work. Do not restore the business database as routine rollback.

Current ABAP status: synthetic-only implementation and local validation complete.
SSH now works; [live read-only preflight](advanced-assistant-live-server-preflight.md)
found healthy origins and successful main backup services, but a failed separate n8n
backup service and inactive timer. Sudo authentication blocks protected checks of actual
backup coverage, migration ledger, containers and rollback inventory. NO-GO pending
that verification; no production deployment authorization is requested yet. The earlier
SSH-unlock prerequisites above are historical; secret installation now also requires
separate explicit approval under the latest read-only authorization.
