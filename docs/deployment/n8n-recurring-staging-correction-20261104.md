# Recurring n8n backup correction — November 4

## Confirmed remaining fault

The approved startup receipt confirms both production n8n targets retain the
reviewed executables. `n8n-backup.service` is historically failed; its correct
executables are `/usr/local/sbin/n8n-backup` and
`/usr/local/sbin/n8n-ensure-running`. The timer is disabled/inactive. Journal
classification supports a historical state-checker failure; it does not establish
the exact historical error. The current refusal is independently demonstrated:
`/var/backups/n8n/staging` exists and is nonempty, while the installed script
rejects any existing staging directory. Earlier capture and offline recovery
results for both targets remain valid and must not be repeated.

## Minimum local correction

The backup uses a new root-private UUID directory under `/var/backups/n8n/runs`
for each invocation. It never reuses, moves or deletes the protected legacy
staging. New cleanup requires the exact run path, matching root-owned private
marker, unique run identity, expected directory contents and successful checks
of both capture manifests before deleting only that new run. Incomplete runs
are retained. The shared backup lock, projects, volumes, online consistent capture,
credentials, encryption, repository, snapshots and retention settings are preserved.

One existing preflight repository-budget read remains; the duplicate final full
metadata read is removed. The final budget check reuses the conservative
pre-write upper bound (current referenced bytes + staged size + existing overhead)
under the shared lock. No total-budget guard is replaced with an undersized
latest-snapshot estimate. This reduces scans from two to one per future backup;
it does not eliminate normal Restic metadata traffic or bypass provider caps.

Seven new disposable staging/cleanup tests and six new installer tests passed,
plus shell syntax. Tests used synthetic tmpfs files in network-disabled local
containers; no backups, repository reads, source captures or earlier regression
tests were run. The new installer tests cover exact payload hashes, exclusive
original-file preservation, ownership/permissions, atomic replacement, two-file
rollback, symlink/writable-target refusal and explicit approval admission.

## Installation boundary — not executed

`install-n8n-recurring-staging-fix.py` installs only the backup script and state
helper after verifying their pinned installed hashes, correct disabled unit
identity, current web image, lock availability, resource headroom and both target
key/volume checks. It saves and verifies root-private originals before replacing
either file, preserves ownership/permissions, verifies installed bytes/syntax,
and restores originals after a failed installation. It preserves the prior
staging directory and all production containers/unit state. A single-use receipt
records sanitized results. No jobs, timers, service restarts, retention changes,
repository requests, recovery drills or application changes are included.

Timer activation remains a separate production boundary. Do not blindly start
the persistent timer: activation can trigger a missed run immediately. Actual
service-context execution or the next approved scheduled run has not passed for
this corrected version. Do not label the recurring-production gate complete on
the strength of fixtures or installation alone.

## Remaining linked demonstration

The startup receipt found zero lead/customer → invoice → workflow links and zero
completed signed round trips for such links. Portfolio instructions are ready,
but no single linked production demonstration exists. Closing this gate requires
an explicitly approved synthetic-record demonstration and an approved narrow
integration path; existing assistant activation does not authorize live workflow
execution or global integration enablement. The legacy production canary script
targets an old release and changes shared web/worker settings and n8n publication;
it must not be run unchanged against the current deployed assistant.

## Reviewed upload and executed installation — PASS

Installer: `/tmp/abap-n8n-recurring.mxuadNx4/install-n8n-recurring-staging-fix.py`.
SHA-256: `5b9749e6dc2845bfeff31b435ebbda529d5fa7d4d1d63a9c0ca380b416160f52`.
Backup script: `9fd130ea7fd55d07219c8ea6fd51b30647d0e5aa851749b02e2e3e8f87159077`.
State helper: `1f53303333b264cbc6c3d884ca8fc67155952465e8544909543dbd3359643808`.
All remote hashes match local reviewed bytes; uploaded shell syntax passed.
The inventory helper is unchanged at `4306de30…`.

The owner executed the approved installation November 4 at 14:26 UTC.
Receipt `approved-n8n-recurring-staging-install-20261104-1` returned
`PASS-two-files-installed-timer-still-disabled`. Installed hashes match those
above. Originals were verified before replacement and are preserved under
`/var/backups/abap/n8n-recurring-before-20261104T142635Z-89bb779b`.
Protected staging, production state and unit configuration were preserved.
No backup, repository request, timer change or service restart occurred.
The installation command is consumed and must not be rerun.
