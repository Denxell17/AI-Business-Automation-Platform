# Linked CRM → invoice → signed automation — PASS in isolation

The new missing acceptance scenario passed against the exact deployed security
image `sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c`,
cached PostgreSQL 18 and n8n 2.42.3. This was local isolated execution, not a
production demonstration or authorization to enable shared integrations.

Reproducible scenario: `scripts/verify_linked_portfolio_demo.py`.
It uses existing CRM, invoice, schedule/worker, delivery, provider and web services;
no product functionality, routes or application image were changed.

## Executed evidence

| Check | Actual result |
| --- | --- |
| Fictional lead → customer conversion | PASS; one lead and one customer |
| Invoice and protected PDF | PASS; one invoice, generated document |
| Active workflow and stored daily schedule | PASS |
| Worker occurrence claim/start | Exactly one claimed, one started, zero failed |
| Invoice → workflow execution link | Exactly one |
| Signed outbound delivery to real n8n | Succeeded, one attempt |
| n8n deterministic action and signed callback | Completed; inbound accepted, one attempt |
| Stored executions/events | One execution and one n8n event |
| Authenticated customer/invoice/workflow HTML | PASS; linked workflow and completed result displayed |
| AI/provider/B2 requests | Zero |
| Published ports/external network | None; internal Docker network |
| Disposable cleanup | PASS |

The initial fixture setup needed its Python import path and n8n cache tmpfs
corrected. A subsequent first delivery failed; its exact HTTP cause was not
retained, so no root cause is claimed. The final fixture checks n8n's readiness
endpoint rather than liveness alone and passed with one delivery attempt. Failed
setup resources were removed; no production service or data was involved.

The final successful project was `abap-linked-6dd7e60292cc`. It used fresh random
fixture credentials, a fresh synthetic database, no real records, no cached
production dump and no restored production configuration. Fixture credentials
were removed with its task resources. Prior broad suites, security scans,
provider probes, backups and recovery drills were not rerun.

## Remaining acceptance boundary

HTTPS and production application/assistant availability are separately verified.
Production shared integrations remain disabled and the n8n endpoint is unset.
No production linked run is claimed. The existing roadmap's secured-public-app
n8n demonstration gate remains open unless the owner explicitly accepts this
isolated demonstration and labels live n8n integration as deferred. Otherwise a
controlled production demonstration needs separate approval and preparation that
preserves the current assistant and unrelated n8n workflows. The legacy canary
which stops/restarts shared n8n must not be used unchanged.

The recurring n8n timer is active/enabled, next event November 5 at 05:30 UTC.
Its first corrected scheduled backup is not yet observed. This is a separate
operational observation, not a successful new backup or a reason to force one.

The owner subsequently required the controlled production demonstration rather
than accepting isolated-only scope. The prepared temporary authenticated HTTPS
procedure is documented in
[the production review](controlled-public-linked-demonstration-20261105.md).
Its execution remains pending explicit authorization; no gate waiver is inferred.
