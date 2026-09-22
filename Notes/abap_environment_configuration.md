# ABAP Environment and Integration Configuration Contract

## Purpose and current scope

This document fixes the configuration boundary for the completion roadmap. The
dedicated worker is introduced in Milestone 1; webhook, n8n, and external
provider capabilities remain gated by Milestones 2, 3, and 6.

Configuration is supplied through environment variables. `.env.example`
contains names and non-secret examples only. Real secrets must be stored in an
ignored local `.env` file for development or in the hosting platform's secret
manager for staging and production. Secrets must never appear in Git, logs,
browser responses, task payloads, execution results, screenshots, or test
fixtures.

## Environment definitions

| Environment | Database and services | Credentials and data | Required verification |
| --- | --- | --- | --- |
| `local` | SQLite by default; loopback PostgreSQL is optional. Future n8n must be private or bound to loopback. | Developer-owned fake credentials and synthetic data only. An ignored `.env` may be used. | Unit suite; focused local tests. |
| `integration-test` | Disposable PostgreSQL and deterministic local webhook receiver. Future worker/n8n services use an isolated Compose project and private network. | Generated, short-lived test secrets and synthetic data only. Never target production. | Full suite, PostgreSQL concurrency tests, webhook failure tests, and Compose demo as milestones add them. |
| `staging` | Production-equivalent PostgreSQL, web, worker, and private n8n on isolated staging resources. | Secret-manager values, least-privilege staging accounts, and non-production data. | Migrations, health/readiness, end-to-end smoke tests, restart and rollback checks. |
| `production` | PostgreSQL, web, worker, and required private services with restricted networking, persistence, monitoring, and backups. | Secret-manager values and least-privilege production identities. No local `.env` deployment. | Promotion only after staging evidence and the applicable milestone exit gates pass. |

`ABAP_ENVIRONMENT` must be one of these four exact values. Configuration
loaders added in later milestones must reject unknown values and unsafe
production defaults rather than silently falling back.

## Worker contract (Milestone 1)

| Variable | Contract |
| --- | --- |
| `ABAP_WORKER_ENABLED` | Explicit boolean gate; defaults to `false`. Enabling it never bypasses database readiness or migrations. |
| `ABAP_WORKER_POLL_SECONDS` | Positive interval between due-schedule polls; example `5`. |
| `ABAP_WORKER_CLAIM_LIMIT` | Positive maximum occurrences considered per poll; example `25`. |
| `ABAP_WORKER_LEASE_SECONDS` | Positive claim lease long enough for one bounded attempt; example `120`. |
| `ABAP_WORKER_MAX_ATTEMPTS` | Total bounded attempts including the first; example `5`. |
| `ABAP_WORKER_RETRY_BASE_SECONDS` | Positive initial exponential-backoff delay; example `5`. |
| `ABAP_WORKER_RETRY_MAX_SECONDS` | Maximum retry delay; example `300`, never below the base delay. |
| `ABAP_WORKER_STALE_AFTER_SECONDS` | Age after which recovery may evaluate an unfinished run; example `900`. Recovery must preserve idempotency. |
| `ABAP_WORKER_SHUTDOWN_GRACE_SECONDS` | Bounded graceful-shutdown window; example `30`. |

The worker and web process use the same database contract, but remain separate
processes. Worker configuration validates safe numeric bounds and fails closed.

## Webhook and n8n contract (Milestones 2 and 3)

| Variable | Secret | Contract |
| --- | --- | --- |
| `ABAP_N8N_BASE_URL` | No | Day 156 accepts a clean HTTPS origin with a public DNS hostname matching the allowlist. Private n8n networking needs a separately verified policy in Milestone 3. |
| `ABAP_N8N_WORKFLOW_PATH` | No | Root-relative, version-controlled webhook path; it must not contain credentials or query-string secrets. |
| `ABAP_INTEGRATION_ALLOWED_HOSTS` | No | Comma-separated exact hostnames allowed for outbound delivery. Redirects must not escape the allowlist. Wildcards are forbidden. |
| `ABAP_WEBHOOK_CONNECT_TIMEOUT_SECONDS` | No | Positive bounded connection timeout; example `3`. |
| `ABAP_WEBHOOK_READ_TIMEOUT_SECONDS` | No | Positive bounded response timeout; example `15`. |
| `ABAP_WEBHOOK_MAX_REQUEST_BYTES` | No | Hard serialized outbound/inbound payload limit; example `262144`. |
| `ABAP_WEBHOOK_MAX_RESPONSE_BYTES` | No | Hard response-read limit; example `262144`. |
| `ABAP_WEBHOOK_SIGNATURE_TTL_SECONDS` | No | Allowed signed timestamp age; example `300`. Replay protection must also store a unique event ID or nonce. |
| `ABAP_WEBHOOK_MAX_ATTEMPTS` | No | Bounded immediate delivery attempts for one signed event; example `3`, maximum `10`. |
| `ABAP_OUTBOUND_WEBHOOK_SECRET` | Yes | Signs ABAP-to-n8n messages. Must be random, stable during rotation overlap, and different from the inbound secret. |
| `ABAP_INBOUND_WEBHOOK_SECRET` | Yes | Verifies n8n-to-ABAP callbacks. Must be random, stable during rotation overlap, and different from the outbound secret. |

The future implementation must use versioned schemas, strict JSON content
types, authenticated signatures over canonical request data, constant-time
verification, bounded bodies and responses, destination validation before each
request, safe redirect handling, idempotency keys, replay rejection, sanitized
errors, and audited delivery state. Configuration values never prove that an
external service is reachable or correctly configured.

Day 156 added `integration_config.py`. When `ABAP_INTEGRATIONS_ENABLED=false`,
the loader exposes no destination or secret. Enabling it requires distinct
inbound/outbound secrets, a clean allowlisted HTTPS origin, a root-relative
workflow path, and bounded numeric settings. The loader makes no network
request; the sender must revalidate DNS results, redirects, and destinations
at connection time. No webhook delivery or callback is implemented yet.

Day 157 added `webhook_contract.py`. Its only accepted content type is
`application/json`. Every message has schema version `abap.webhook.v1`, a
canonical UUID event ID, correlation ID, event type, UTC timestamp, and JSON
object data. HMAC-SHA256 signs the schema version, Unix timestamp, event ID,
and exact canonical JSON bytes. Verification uses the inbound secret,
constant-time comparison, a bounded timestamp window, strict shape parsing,
and the configured request-size limit. Replay persistence, delivery, and HTTP
routes are not implemented yet.

Day 158 added durable replay and delivery metadata. A verified inbound event ID
is inserted once with its expiry time before any future callback handler can
use it. The same transaction records an accepted inbound delivery. Outbound
records begin pending and retain only IDs, event type, status, retry timing,
response status, and a short safe failure code. Webhook bodies, response
bodies, destinations, private configuration, and secrets are never stored.

Day 159 added outbound HTTPS delivery. Each attempt resolves the allowlisted
hostname again, rejects any non-public address, connects to that verified IP
while validating the original TLS hostname, sends the Day 157 signature, and
rejects redirects. Requests and responses stay within configured byte limits.
Transient network, timeout, and 5xx responses retry immediately with bounded
backoff. Delivery records retain only status, attempt count, response status,
and safe failure code. The outbound body remains in memory only.

## External provider contract (Milestone 6)

`ABAP_INTEGRATIONS_ENABLED=false` is the fail-closed default.
`ABAP_EXTERNAL_PROVIDER=disabled` means no external adapter may be constructed.
Later provider adapters must define their own allowlisted endpoints, timeout and
rate-limit behavior, credential variable names, scopes, rotation procedure, and
deterministic test substitute before being advertised as available.

## Validation and ownership

- Application startup owns environment validation; business services receive
  validated settings instead of reading arbitrary environment values.
- Production and staging deployments own secret injection. Compose files may
  reference variable names but may not contain their values.
- Automated tests own generated test secrets and isolated destinations.
- Operators own rotation and must preserve separate inbound and outbound keys.
- Readiness may report a capability as unavailable, but must never expose a
  secret or raw private configuration detail.
