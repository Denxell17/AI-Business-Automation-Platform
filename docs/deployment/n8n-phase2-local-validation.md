# n8n Phase 2 Local Validation

Phase 2 is an isolated, synthetic proof of concept for n8n 2.42.3. It is not
approved for production activation. The overlay publishes no n8n or demo
provider port, does not enable Qwen, and imports only the two ABAP demo
workflow IDs. Independent n8n installations and course workflows are outside
this setup.

## Security and processing boundary

The ingress workflow preserves the Webhook node's raw binary body and sends a
base64 wrapper across the private Compose network. The private demo provider
decodes those exact bytes and reuses ABAP's `verify_inbound_webhook`. Acceptance
therefore requires the existing HMAC contract, canonical event ID, matching
header/body event ID, supported content type, signature expiry, 60-second
future-skew limit, request-size limit, complete envelope schema, and the narrow
scheduled-execution event schema.

Migration `011_add_n8n_demo_event_acceptance.sql` adds a PostgreSQL table used
only by this proof of concept. The event ID is its primary key. Authentication,
validation, and an atomic insert complete before n8n returns HTTP 202. A repeat
with the same event ID and body hash is acknowledged without another action; an
event-ID collision with different bytes is rejected. Only identifiers, a SHA-256
body hash, callback identity, status, attempts, leases, and timestamps are
stored. Payloads, signatures, secrets, destinations, and response bodies are
not stored or logged.

The processor workflow atomically claims accepted events using PostgreSQL
`FOR UPDATE SKIP LOCKED`, performs a deterministic local action, and sends an
ABAP callback. `WF-N8N-DEMO-FAIL` is the synthetic failure case; all other
synthetic workflow IDs complete. The callback event ID and `occurred_at` value
are stored at acceptance and remain stable through retries or restarts. Each
HTTP operation has a three-second timeout. The callback node retries at most
three times per claimed attempt; expired leases permit at most three processor
attempts, after which the event becomes `dead` with a metadata-only failure
code. ABAP still performs its normal inbound verification, replay protection,
audit recording, and atomic execution-result update.

## Configuration and compatibility

The overlay pins `n8nio/n8n:2.42.3` by tag and image digest. It needs three
different synthetic values supplied at runtime:

- `ABAP_OUTBOUND_WEBHOOK_SECRET` for ABAP-to-n8n messages;
- `ABAP_INBOUND_WEBHOOK_SECRET` for n8n-to-ABAP callbacks; and
- A scoped provider token for private n8n-to-provider calls. Phase 3 Batch 3
  supersedes the earlier environment-variable bootstrap with the file-mounted
  procedure in `n8n-phase3-batch3-preflight.md`.

Do not reuse production credentials. The two HMAC secrets and internal token
must each be generated independently. n8n execution-data persistence is
disabled for these workflows so the signed wrapper and callbacks are not kept
in n8n history. The disposable PostgreSQL database must have migrations through
011 before the provider starts.

## Rollback

Code rollback is compatible with migration 011 because the table is additive
and no existing table changes. Stop the isolated stack first. Keep the table
during a code rollback unless its synthetic history has been reviewed; dropping
it discards pending and audit state. In disposable validation, remove only the
Compose project and volumes created for the run. Production schema removal, n8n
workflow import, activation, deployment, or service restart requires a separate
approval.

## VPS resource and isolation assessment

The proof of concept reuses ABAP PostgreSQL and adds one small metadata table,
one private Python process, and two lightweight n8n workflows. A second
production n8n instance would duplicate n8n's baseline Node.js memory, its
SQLite storage, and operational monitoring. Do not recommend one without first
measuring the existing VPS's steady-state and peak CPU, memory, disk, and swap.
Logical isolation in the existing n8n instance—separate ABAP workflow IDs,
credentials, tags/project ownership, and no shared nodes with course workflows—
is the lower-resource starting point. A second instance is justified only if
measured headroom and stronger fault or administrative isolation outweigh that
overhead.
