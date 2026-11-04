# Controlled public linked demonstration — approved, corrected execution pending

## First execution: blocked before any demonstration changes

The owner ran the approved controller on November 5 Shanghai time. It returned
`BLOCKED-before-demonstration / baseline_public_smoke_failed`, before creating
the receipt, workspace, containers or temporary route. Read-only diagnosis found
Cloudflare returned 403 to the VPS's automated public requests for health,
readiness and login. The exact Cloudflare rule is not established. All three
application endpoints returned 200 locally; origin HTTPS certificate/hostname
verification also passed. No application outage is inferred from the edge 403.

The minimum correction uses the existing origin at loopback with the real public
hostname and default trusted TLS verification for operational health and anonymous
origin-gate checks. It follows no redirects and never disables certificate or
hostname verification. Cloudflare settings remain unchanged. **Actual public
acceptance still requires the three signed-in browser page reads through HTTPS.**
Origin checks are labeled explicitly, never reported as public-browser evidence.

Three new focused tests passed: default TLS trust/SNI and no redirect following,
fail-closed invalid certificates, and exact failed health endpoint reporting.
The corrected function was executed read-only on the VPS: all three verified-TLS
checks returned 200. No privileged demonstration was repeated. The existing
approval covers the same bounded operation; authenticated sudo execution is still
required. Do not rerun the superseded command.

The owner requires the secured public-application demonstration; isolated-only
acceptance was explicitly declined. The complete private CRM → customer → invoice
and PDF → scheduled worker → real n8n action → signed callback → authenticated
result chain has passed locally using the exact deployed image. This procedure
does not claim that the public acceptance gate has already passed.

## Exact production scope

Run one disposable four-container synthetic stack on the VPS from cached pinned
application, PostgreSQL 18 and n8n images. All services stay on a new owned internal
network with no published ports. The host Caddy service can reach the owned private
web IP. No existing container/network membership is changed, and no existing n8n
workflow or business database is used or modified. Fresh fixture credentials and
an explicit unique database alias prevent use of production data or credentials.
Initializing the empty disposable schema is not a production migration.

Temporarily load one GET-only route under an unpredictable
`https://app.dennisbasadre.com/portfolio-demo-<run>/…` prefix. It first checks the
existing production Advanced Assistant login/permission gate. Only then does it
delegate to the private synthetic account. The real browser cookie is never
forwarded to the fixture; fixture cookies never replace the production cookie.
Responses use `private, no-store`. No new authentication feature is installed in
the application. Caddy's on-disk configuration and process are preserved; only
its running configuration is gracefully loaded and restored.

After the VPS chain passes, the terminal prints the three public customer,
invoice and workflow links. **Keep the terminal open and visit all three links in
the same browser where the existing ABAP account is signed in.** No password or
cookie is requested in chat. The protected backend records only successful
gateway-authenticated reads of those exact synthetic pages. Verification gives
a ten-second viewing grace period, then automatically restores the original
proxy configuration and deletes only the identity-verified disposable resources.
Timeout after ten minutes, interruption and catchable errors also attempt cleanup.
There is no automatic retry. If a proxy rollback cannot be verified, preserve the
owned resources for operator recovery and report BLOCKED rather than overwrite
unrelated configuration or falsely report cleanup.

No application deployment/rebuild, shared service restart, timer change, B2
request, backup, recovery, AI request or private n8n public endpoint is included.
The production assistant, existing ABAP services, real records, n8n workflows,
public RAG and free-model safeguards remain unchanged.

## Preparation evidence

- Nine new focused unit checks passed: route restoration/concurrent-change
  preservation, injection/admission guards, explicit isolated DB naming, HTML URL
  prefix behavior, private-network-only addressing and diagnostic redaction.
- Cached local Caddy passed anonymous denial, forged-fixture-cookie denial,
  authenticated delegation/prefix handling and production-cookie preservation.
- Live Caddy configuration load/readback/restoration passed in a disposable fixture.
- Host-to-owned-internal-backend access passed with no published ports. An initial
  local attempt to publish loopback on an internal network was rejected by its
  fixture assertion; the reviewed procedure uses private bridge IP access instead.
- The no-store response policy parsed successfully in cached Caddy.
- Existing VPS metadata confirmed the authoritative host Caddy, expected loopback
  app upstream, compatible unit network policy, available resources and Compose
  availability without registry credentials. No production change was made.

## Reviewed package, staged without execution

Controller: `/tmp/abap-public-demo-origin.SXEIXURE/run-public-linked-demonstration-once.py`.
SHA-256: `300742cadd30c9ecc695b3efa045ceaa96432c79b767ca99dbdf81b668864456`.
Manifest SHA-256: `1bc12adeec721cfb0d1a5055913196714e92170cc7e304bf064b74f64c724cd1`.
Package SHA-256: `ff47c1aee5c8ddc9fd1dc27069610d2af62b00792bab6828a8057bc2b4318c96`.
Local/remote hashes and syntax match. This resumes the already approved scope;
no privilege bypass or automatic rerun is performed. The sanitized root-only receipt will be
`/var/backups/abap/approved-public-linked-demonstration-20261104-1.json`.
