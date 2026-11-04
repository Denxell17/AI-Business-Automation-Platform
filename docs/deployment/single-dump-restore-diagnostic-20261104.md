# Single-dump retrieval and restore-only diagnostic — PASS

The owner approved retrieving only the previously authenticated 72,058-byte
`database.dump`, retaining it securely, and executing the unused restore-only
diagnostic once. No configuration archive, image import, full application
rehearsal, backup, service change or unrelated test is included.

`deploy/hosthatch/retrieve-one-dump-and-diagnose-once.py` invokes only the reviewed
retrieval helper's single-read function, narrowed to snapshot
`ac2dae86ca8f5106bfcb4c08a57aa8e1afec77496ab0cfb3e010fd087cd55e45`,
path `/var/backups/abap/staging/database.dump`, exact size 72,058 and SHA-256
`25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761`.
Existing repository/encryption/cache/caps remain unchanged. A fresh observed
capacity proof is required only if an authenticated local copy is absent.
There is at most one retrieval invocation, with the existing five-minute bound
and no controller retry, listing, stats, repository check, prune or image read.

The complete verified file is published without overwriting any prior artifact
at `/var/backups/abap/recovery-cache/database.dump`: root-owned file 0600 inside
root-owned directory 0700, file/directory fsync. It is deliberately retained on
success and failure. The diagnostic receives this local copy and never deletes
it. Its previously reviewed six-boundary-check implementation is unchanged.

The wrapper checks the cached PostgreSQL image, resources, trusted existing
backup dependencies and unused diagnostic receipt before any retrieval. It
preserves the source and all old receipts; its own exclusive single-use receipt
is `/var/backups/abap/approved-one-dump-diagnostic-20261104-1.json`.
Only safe statuses, artifact metadata and the diagnostic's sanitized PostgreSQL
error categories/SQLSTATE are printed. No live production services are modified.

Seven new wrapper checks passed: immutable helper pins, corrupted input rejection,
private/no-overwrite file publication, exactly one approved read and diagnostic,
retention on diagnostic failure, no retry after retrieval failure, existing-copy
reuse and quota rejection before network access. Six mocked checks passed in
the initial local run; the POSIX ownership fixture then passed separately with
root UID inside a disposable local network-isolated container. No successful
existing test, database startup or recovery was repeated.

## Executed operator result

The owner executed the checksum/proof-bound command on November 4. Status:
`PASS-retrieval-and-restore-only-diagnostic`. Exactly one file was retrieved and
one restore attempted. `pg_restore` exited **0**, with **zero stderr bytes**.
The exact 72,058-byte dump remains verified at the private cache path above.
Owned-container cleanup and independent production preservation both passed.
No image import, application startup, full rehearsal, production change or
additional repository operation was performed. Both operation receipts are now
consumed; do not rerun them.

Server SQLSTATE `57P03` was classified as startup/readiness output. It does not
indicate that this restore failed, and does not establish the earlier failure's
cause. The empty-stderr `unclassified_postgresql_error` field is a generic
sanitizer placeholder, not an actual PostgreSQL error. No speculative restore
correction or repeat test is justified. Application startup against this restored
database was outside the diagnostic scope and is not claimed verified.

Detailed sanitized receipts remain private under
`output/project-completion-20261104/`.
