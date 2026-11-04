# Existing n8n timer activation — approval pending

The staging correction is installed and verified; recovery proofs for both n8n
targets remain valid. No further installation, backup drill or restore is needed.
The existing timer is still inactive/disabled, so recurring protection is not
yet enabled. The linked CRM/invoice automation demonstration remains separate.

## Exact proposed action

Run `activate-reviewed-n8n-timer-once.py` once with authenticated approval. It
verifies the installed correction hashes, existing unit identity, unchanged
05:30 UTC daily persistent calendar, no unit drop-ins, both production key/volume
checks, current web image and a production-state baseline. It calls only
`systemctl enable --now n8n-backup.timer` to activate the existing schedule;
no timer definition or service executable is edited.

**Persistent activation may run an overdue scheduled backup. Approval must include
that possibility.** Such a run uses the existing encryption, repository, caps,
retention and corrected non-disruptive procedure. The controller never starts a
backup service manually or retries it. No additional repository scan/check,
retrieval, recovery drill, paid operation or spending-cap change is performed.
Normal backup preflight includes the one retained budget read documented in the
correction review; activation does not bypass that safety guard.

If a calendar run is observed, monitor the existing bounded service, require
success/exit 0 and collect both snapshot IDs from sanitized journal receipts.
Otherwise report the active timer's next event and explicitly label the new
scheduled execution as not yet observed. Do not claim a backup ran on installation
or timer enablement alone. An activation/observed-job failure disables the timer
again; it never stops an application/n8n container or deletes backups/staging.
The existing service timeout remains authoritative for an already running job.

The same operation reads only four non-secret integration readiness booleans
from the current web container to prepare the missing linked demonstration.
It creates no business records, dispatches no workflow, and does not enable
shared application integration settings. Independent production-state comparison
runs after success or failure. The single-use receipt is root-private.

## Preparation evidence

Three new timer contract/admission checks passed: exact calendar admitted;
changed schedule, persistent mode, target unit or additional trigger rejected;
missing approval rejected before filesystem/unit access. No previously passed
backup, security or application test was repeated.

Controller staged unexecuted at
`/tmp/abap-n8n-timer.TNHDjAQj/activate-reviewed-n8n-timer-once.py`.
SHA-256: `c91fc4e993a09827d757754d3aaa400027b7e06e753d23156b63b8e07ced6330`.
Uploaded hash matches local bytes; inventory helper remains pinned at `4306de30…`.
