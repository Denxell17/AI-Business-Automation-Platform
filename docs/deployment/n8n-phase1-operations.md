# n8n Phase 1 Operations

Phase 1 adds an optional, asynchronous ABAP outbound boundary. It does not
change or deploy n8n, enable production integrations, or enable Qwen.

## Database migration

`010_add_workflow_n8n_outbox_controls.sql` adds `workflows.n8n_enabled` as a
non-null boolean with a default of `FALSE`. Existing and new workflows are
therefore opted out. It also adds an index used by delivery-history retention.

The application creates a scheduled execution, its task snapshots, and a
pending webhook-delivery row in one transaction only when both the workflow
opt-in and the global integration switch are enabled. A failure inserting any
of those records rolls back the entire transaction.

The migration is forward-only. Before applying it outside a disposable test
database, retain the normal verified database backup. A code rollback is
compatible with the added column and index because both are additive. Do not
drop them during an application rollback; remove them only in a separately
reviewed schema change after confirming no newer application version needs
them.

## Runtime compatibility

The scheduler no longer makes outbound HTTP calls. It only writes the outbox.
The existing `webhook_retry_worker` leases and delivers pending rows, using the
existing allowlist, HMAC, timeout, response-bound, and retry controls.

`compose.deploy.yaml` includes a `webhook-retry-worker` under the explicit
`integrations` profile. The profile is not started by the normal deployment
command, and `ABAP_INTEGRATIONS_ENABLED` defaults to `false`. The HostHatch
overlay also keeps this value false. Production activation requires a separate
approved configuration change and deployment.

This phase does not import or modify an n8n workflow. Compatibility with n8n
2.42.3 remains a Phase 2 verification item.

## Retention maintenance

While the enabled retry worker is running, it periodically removes:

- replay-event IDs after their signature replay window has expired; and
- terminal inbound/outbound delivery metadata older than
  `ABAP_WEBHOOK_DELIVERY_RETENTION_DAYS` (90 days by default).

Pending and retrying deliveries are never removed by retention. Maintenance
runs at most once per `ABAP_WEBHOOK_MAINTENANCE_INTERVAL_SECONDS` (one hour by
default). Request bodies, response bodies, destinations, and secrets remain
unstored.

## Safe disable and rollback

To stop new outbox creation without changing workflow records, keep
`ABAP_INTEGRATIONS_ENABLED=false`. To isolate one workflow, clear its n8n
checkbox. Stopping the retry worker leaves pending rows durable for later
review; it does not affect ABAP web, scheduler, CRM, invoice, or manual workflow
operations.

Before re-enabling after a long pause, review pending delivery age and the
associated running executions so stale events are not sent unexpectedly.
