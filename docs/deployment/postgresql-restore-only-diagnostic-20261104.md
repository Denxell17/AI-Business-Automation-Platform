# PostgreSQL restore-only diagnostic — prepared, not executed

The completed retrieval authenticated both approved files, image import passed,
and PostgreSQL 18 started. Only `restore_postgresql_archive` failed, exit 1.
The old core captured `pg_restore` stderr in process memory and persisted only
`pg_restore_error`/231 bytes. Successful owned-container/daemon/workspace/RAM
cleanup removed the remaining private log sources. An ordinary SSH metadata
check cannot access the root-only paths; their actual remaining contents have
not been claimed inspected. The exact original cause remains UNKNOWN.

Prepared script: `deploy/hosthatch/diagnose-existing-postgresql-restore.py`.
Staged file:
`/tmp/abap-restore-only.WXxaDbXX/diagnose-existing-postgresql-restore.py`.
SHA-256: `4306de307731a5e9ac9d6403bebbb9da1f7776588fc3685393230ef57f093746`.
Local/remote syntax and checksums passed; six local boundary/redaction tests
passed. No script execution or privileged action occurred.

`--inspect-existing` reads only the listed old workspace log paths and four
explicit dump locations. No recursive scan, Docker call, write or restore occurs.
The `recovery-cache/database.dump` location is an optional explicit offline-copy
location, not a claim that a recovered copy exists there.

`--approved-restore-if-local` first performs that same inspection. If it finds an
actionable retained restore error, it reports only sanitized categories/codes
and performs no restore. If no local dump matches exactly 72,058 bytes and
SHA-256 `25839dda140bcf066cc687296a2a1fb45d52239e84827a549635f975f9de5761`,
it stops without creating resources. No retrieval fallback exists.

Only with separate approval and an exact local match, it uses the existing VPS
Docker daemon to create one newly labelled disposable PostgreSQL 18 container
from the already cached immutable image. This differs from the prior private-
daemon rehearsal: it adds/removes only its own diagnostic container. No image
import/pull, production container modification, persistent volume, published
port, outbound network route, application startup, migration or integration is
included. All database/log writes are bounded container RAM; credentials are
fresh isolated values. It invokes the original restore command exactly once.

Stderr and verbose server errors remain private in memory/RAM. Only fixed error
categories, SQLSTATE codes, statement verbs, exit status and byte counts enter
the root-only sanitized receipt. No SQL, identifiers, row values, tokens or raw
errors are printed. The diagnostic removes only its identity-verified container,
compares existing production state, preserves the source dump and uses an
exclusive single-use receipt. There is no automatic retry.

Prepared inspection and conditional command files are stored locally under
`output/project-completion-20261104/`; neither has been executed. Approval is
required before any sudo inspection or conditional diagnostic. If the exact
dump is unavailable, that missing local input is the blocker under the current
no-B2 restriction; do not launch another retrieval or full rehearsal.
