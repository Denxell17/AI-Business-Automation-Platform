# Remaining acceptance — cached startup and existing evidence

Prepared after the accepted security deployment (`062bbb3`). No security scans,
dependency reviews, retrievals, backup jobs or successful tests are repeated.

## Smallest necessary privileged operation (not executed)

`deploy/hosthatch/finish-application-startup-once.py` reuses the checksum-pinned
recovery engine and the successful restore-only diagnostic's Docker access,
private dump reader and production-state comparison. Six new admission and
redaction tests passed. It does not invoke either helper's command-line entrypoint.

Required inputs already identified on the VPS:

- Retained `/var/backups/abap/recovery-cache/database.dump`, 72,058 bytes,
  SHA-256 `25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761`.
- Cached exact rollback image `sha256:e9b09e43f818fc10081f87fb5ccc1646174e7cafe4cbe241d3054d78faa5b8b9`.
- Cached PostgreSQL 18 image `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`.

The earlier restored database was deliberately cleaned up. One load of the
retained dump into a fresh disposable database is therefore a prerequisite for
the missing application startup check, rather than a repeated restore diagnostic.
No B2 request, image import, private-daemon reconstruction or backup is required.
The readiness check explicitly uses TCP loopback, so an initialization-only Unix
socket cannot satisfy readiness before the final server used by web is available.
This is a startup admission safeguard, not a claim about the old unknown failure.

With separate approval, create exactly two labelled containers on the existing
Docker daemon. No production container, image, network, volume or configuration
is changed. PostgreSQL has network `none`; web shares only that disposable
loopback namespace. Both have read-only roots, bounded tmpfs/CPU/memory/process
limits, no published ports or production mounts and no restart policy. Web uses
a fresh read-only database role and fresh session secret. All external settings
are excluded by the existing environment allowlist, workers/integrations/AI/RAG
are disabled, and no migration runner starts. Run only startup, schema and
health/readiness/login checks needed for this missing acceptance evidence.

Configuration artifact authentication was previously verified; this continuation
reuses that evidence. It supplies image defaults and explicit isolation overrides,
not a newly restored copy of the configuration archive. It does not prove full
host reconstruction, TLS/proxy recovery or invoice-file payload restoration.

Save a root-only single-use receipt, retain sanitized failed-stage diagnostics,
clean up only identity-verified disposable containers, and independently compare
production state after success or failure. The retained dump is never removed.
No automatic retry is permitted.

## Recurring n8n qualification

Existing successful captures and both offline recovery drills are reused. The
installed backup refuses an existing staging directory; the approved one-off
backup deliberately retained its nonempty staging. The recurring script also
calls full-repository raw-data statistics twice. Neither deleting protected
staging nor blindly enabling the disabled timer is acceptable.

The same privileged operation reads only actual service/timer state, executable
paths (without arguments), installed script hashes, staging directory metadata
and bounded journal error categories. It makes no repository call, starts no
backup, changes no service and exposes no secret values. Actual installed unit
identity and failure evidence are needed before selecting the minimum repair.
Any installation or timer enablement requires a separately reviewed change.

## Linked demonstration and portfolio

Existing evidence establishes CRM conversion, protected invoice/PDF and linked
manual workflow runs; separate signed n8n/scheduler tests establish callbacks,
deduplication and stored delivery outcomes. `output/final-gates/roundtrip-results.json`
also records duplicate confirmation 409, one execution/event, duplicate callback
and rejected expired callback. These separate passes do not establish one linked
production demonstration.

Read only aggregate counts of existing lead → customer → invoice → workflow
execution links and completed signed outbound/inbound deliveries. The query uses
a read-only transaction and short timeouts, and prints no IDs, names, amounts,
payloads or customer data. Nonzero counts identify reusable evidence; they do
not alone prove scheduling, HTTPS display or that records are synthetic. Do not
create records, activate workflows or dispatch a canary as part of this operation.
If linked evidence is absent, the remaining action is one explicitly approved
synthetic demonstration using the existing protected integration, not new code
or unrestricted integration enablement. The final tag remains withheld until
the documented exit gates pass.

## Reviewed staging receipt

Staged without execution at
`/tmp/abap-final-acceptance.pdbGncEs/finish-application-startup-once.py`.
Controller SHA-256:
`f9ce4730b0f1075d03386c07b1f96e54beebbc874d854a74de8e28224c1cb40e`.
The existing core and restore diagnostic hashes match their reviewed versions
(`30ab84e8…` and `4306de30…`). Local/remote controller hashes match, and all three
uploaded files passed syntax parsing without execution. No privileged operation,
backup, database query, restoration or application startup has been performed by
this preparation. One explicit authenticated approval is still required.
