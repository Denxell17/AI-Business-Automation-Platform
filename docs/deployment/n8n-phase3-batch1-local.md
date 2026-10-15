# n8n Phase 3 Batch 1: Private callback authority

This batch is for isolated local validation only. It is not approval to deploy,
activate an integration, or change the HostHatch n8n instance.

## Trust boundary

n8n now has one narrow HTTP Header Auth credential for the private provider.
Code-node environment access is blocked. Neither ABAP HMAC secret, the callback
URL, callback body, callback UUID, nor callback signature is present in an n8n
environment variable, workflow definition, or workflow export. The token is
used once to import an encrypted n8n credential, removed from the startup shell
environment, and is only accepted by the provider's four private endpoints.

The provider verifies the original signed ingress as before. A claim returns
only its event UUID. The deterministic action and outcome endpoints look up the
authoritative PostgreSQL record and require a current processing lease. Outcome
acceptance additionally requires a matching, running scheduled ABAP execution
and an allowed `completed` or `failed` transition. Unknown, unclaimed, expired,
completed, duplicated, and mismatched events are rejected.

The provider constructs the callback from stored data, uses the callback UUID
and occurrence time assigned during durable ingress, signs exact canonical
bytes with the ABAP inbound secret, and delivers only to the fixed private ABAP
callback URL. It uses a three-second timeout and three bounded attempts by
default. A failed delivery remains recoverable through the existing lease and
processor-attempt limit. ABAP retains its inbound HMAC verification, replay
protection, audit history, and idempotent result transition.

## Migration and compatibility

Migration `012_move_n8n_callback_authority.sql` adds two non-null integer
columns with zero defaults to `n8n_demo_events`. It is compatible with rows
created by migration 011 and requires no table rewrite for values beyond the
database's normal metadata/default handling. `outcome_attempt` atomically gives
one reporter ownership per lease attempt; `callback_attempt_count` records
bounded delivery attempts without payloads, signatures, secrets, destinations,
or response bodies.

Apply 012 before starting the upgraded provider. The isolated startup now
reimports only the two fixed ABAP demo workflow IDs so an existing Phase 2 demo
volume cannot retain the old signer workflow. Independent course and Job
Scraper workflow IDs are not read or changed.

## Rollback

The safest rollback is forward-compatible: stop the isolated Batch 1 services,
restore the Phase 2 code and workflow exports, and leave the two additive
columns in place. Do not drop migration 012 while any event is processing;
doing so would erase callback-attempt ownership and audit metadata. A schema
rollback, if separately approved and required, must first drain or explicitly
retire all demo events, then drop only `callback_attempt_count` and
`outcome_attempt`. No production rollback is authorized by this document.

## Operations

Use independent synthetic values for the two HMAC secrets, n8n encryption key,
and provider token. Keep the provider and n8n unpublished on the private Docker
network. Callback retry count, timeout, and wait are configurable but should
remain bounded. This batch does not enable Qwen or any production workflow.
