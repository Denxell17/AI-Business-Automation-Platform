# HostHatch backup, restore, and monitoring

This runbook implements the production-operations gate that follows the
HostHatch HTTPS rollout. It is repository-side guidance and templates only.
Nothing in this file authorizes changing the live host without a separately
reviewed execution step.

The production Compose project remains `abap-deploy`. Never run `docker
compose down -v`, never copy the live PostgreSQL data directory, and never
restore over the production database or production volumes.

## Architecture and recovery objectives

- PostgreSQL is captured with `pg_dump --format=custom`, then validated with
  `pg_restore --list` inside the pinned database container.
- Activity logs receive a bounded, best-effort copy into root-only staging
  before Restic reads them. This gives Restic stable staged files but is not a
  filesystem-atomic point-in-time snapshot of a log that is still being written.
- Invoice PDFs are immutable and are read directly from the exact
  `abap-deploy_invoice_documents` volume.
- Essential runtime configuration is copied from an explicit allowlist.
- Restic encrypts and authenticates the snapshot locally before sending it to
  a private Backblaze B2 bucket through B2's S3-compatible API.
- Daily backups provide an initial recovery-point objective of 24 hours.
  Recovery time depends on B2 download speed and the restore drill, but should
  be measured and recorded during every quarterly drill.

The scheduled policy is:

| Operation | Schedule / policy |
| --- | --- |
| Backup | Daily at 02:15 UTC |
| Retention | 14 daily, 8 weekly, 12 monthly |
| Metadata check | Weekly after retention and pruning |
| Full repository read | First day of each month at 04:30 UTC |
| Restore drill | Quarterly and after any backup-system change |
| Release snapshot | Manually before significant deployments or migrations |

Snapshots tagged `release` are protected from the normal retention policy.
Remove that tag only after a later release and restore point have been
verified; thresholds never delete snapshots.

## Exact backup boundary

The Restic command receives exactly two source paths:

1. `/var/backups/abap/staging`
2. `/var/lib/docker/volumes/abap-deploy_invoice_documents/_data`

Staging contains:

- `database.dump`: the verified custom-format PostgreSQL dump.
- `activity-logs/`: a bounded, best-effort copy of the activity-log volume.
- `config/production.env`: the root-only production environment, protected by
  Restic encryption.
- Available copies of the installed Caddyfile, ABAP logrotate rule, Docker
  daemon configuration, non-secret operations configuration, and ABAP systemd
  units.
- `RECOVERY-MANIFEST.txt`, `SHA256SUMS`, and
  `INVOICE-DOCUMENTS.sha256`.

The following are deliberately excluded:

- `/var/lib/docker/volumes/abap-deploy_database_data/_data`; PostgreSQL is
  backed up only through `pg_dump`.
- `/var/lib/docker` as a directory, all other Docker volumes, images, build
  cache, container writable layers, and overlay filesystems.
- `/`, `/opt`, `/etc`, and every unrelated host file.
- `/app/exports`, because its outputs are reproducible.
- Caddy's data directory, private keys, and certificates; Caddy reissues them.
- `/etc/abap/credentials`; the Restic password and B2 key needed to open the
  repository must be recoverable independently from the owner's password
  manager.
- n8n data and credentials. Production n8n is not part of this deployment.

Do not broaden the Restic source list. Add a new production data source only
after its ownership, consistency model, restore procedure, and storage growth
have been reviewed.

## Live-deployment assumptions to verify

The templates deliberately encode the production state proved by the
HostHatch deployment. Stop before installation if any assumption is false:

- Ubuntu uses systemd with `LoadCredential=`, util-linux `findmnt` with
  PID-targeted mount-namespace selection, and GNU `find`, `date`, `du`, `head`,
  `sort`, `stat`, and `xargs` behavior.
- Docker's root remains `/var/lib/docker`; the Compose project remains
  `abap-deploy`; services remain `database`, `migrate`, `web`, and `worker`;
  and the three named-volume paths match `operations.conf` exactly.
- `/opt/abap/app`, `/etc/abap/production.env`, Caddy on host ports 80/443,
  and ABAP on `127.0.0.1:8000` remain unchanged.
- The database container includes compatible `pg_dump` and `pg_restore`
  binaries. The custom dump plus copied activity logs must fit within the 2 GB
  plaintext staging ceiling while preserving 3 GB of host free space and a
  separate 500 MB allowance for Restic cache growth.
- The installed Restic release supports JSON `stats`, `--keep-tag`, S3
  repositories, and `check --read-data`. Pin and record the reviewed version.
- The host can make outbound HTTPS connections to B2 and Better Stack and can
  resolve the public ABAP hostname.
- The B2 account's 10 GB free allowance is still current, account-wide usage
  leaves sufficient room, and the chosen console caps actually prevent
  unintended billing.

The operations service runs as root because Docker access and the named-volume
paths are root-equivalent capabilities. Its unit is hardened, but anyone able
to alter the installed scripts, units, configuration, credential files, or
Docker socket must already be treated as a host administrator.

## Free-tier storage safeguards

All size thresholds use decimal bytes to match Backblaze's GB accounting:

- Early warning: `7,000,000,000` bytes.
- Critical/pre-upload block: `8,500,000,000` bytes.
- Free-tier reference ceiling: `10,000,000,000` bytes.

Before creating a snapshot, the backup script asks Restic for `stats
--mode raw-data --json`. It then conservatively adds the full current staging
size, full invoice-volume size, and 100 MB overhead, assuming no deduplication
or compression. If that projection reaches 8.5 GB, the upload is blocked and
the failure heartbeat is sent. At 7 GB it emits an early warning. After a
snapshot is confirmed, the script measures and reports Restic raw data again;
a warning or critical result reports the job as needing attention even though
the new snapshot is safely retained.

These safeguards do not prune merely because storage is high. Only the fixed
14-daily/8-weekly/12-monthly policy deletes snapshots.

The 7 GB and 8.5 GB thresholds are Restic-side warning and upload-control
limits. They do not, by themselves, guarantee zero Backblaze charges.

`restic stats --mode raw-data` measures referenced Restic data, not the exact
number of bytes billed by B2. It can omit hidden object versions, abandoned
multipart uploads, and unreferenced data pending prune. Therefore it is a
local safety estimate, not authoritative billing evidence. The authoritative
check is Backblaze's account Usage view or its daily usage report
`stored_gb`. Review it weekly and after every maintenance change. Configure
Backblaze account storage/spending caps and usage alerts so the account cannot
silently begin billing; verify the current console behavior when creating the
account instead of assuming that a zero-dollar cap works in a particular UI.

For this dedicated Restic bucket and repository prefix, configure the B2
lifecycle to keep only the latest object version, permanently delete hidden
or noncurrent versions after the shortest reviewed delay, and cancel unfinished
multipart uploads after one day. B2's S3 delete behavior can otherwise retain
hidden versions and grow billed storage after pruning. Do not enable
bucket-default Object Lock until it has been proven in a disposable Restic
repository; it can prevent Restic from removing temporary locks and expired
packs.

Likely storage-growth causes are:

- PostgreSQL table/index growth and high daily database churn.
- New invoice PDFs, which are intentionally immutable and accumulate.
- Activity logs approaching their full fourteen-rotation allowance.
- Release snapshots retained indefinitely.
- Failed or skipped weekly pruning.
- B2 hidden versions or abandoned multipart uploads.
- Accidentally changing the source paths or Restic host/path grouping.

At the current small ABAP scale, daily dumps, deduplicated configuration/logs,
and small PDFs should remain far below 7 GB. Do not treat that qualitative
estimate as a capacity measurement: record the first snapshot size and use
the first four weeks of growth to calculate a real monthly trend.

As a deliberately pessimistic sizing model, the retention rules select at
most roughly 34 routine restore points before overlap and deduplication are
considered. If every PostgreSQL dump were entirely unique, a 50 MB dump would
contribute about 1.7 GB, a 100 MB dump about 3.4 GB, and a 200 MB dump about
6.8 GB. Configuration is negligible, the rotated activity-log source is
normally below roughly 150 MB before Restic compression, and each immutable
invoice PDF is stored only once through deduplication. Release snapshots and
B2 hidden object versions sit outside that simple model and must be counted
separately.

## Backblaze B2 preparation

Perform these steps in the Backblaze console; no repository script creates
cloud resources.

1. Enable MFA on the Backblaze account.
2. Create one private bucket dedicated to ABAP production backups.
3. Record its S3 endpoint and replace `REGION` and `BUCKET_NAME` in the copied
   operations configuration.
4. Create a standard application key restricted to this bucket. Restic needs
   list, read, write, and delete capability for normal lock handling, retention,
   and pruning. Never use the master key.
5. Configure the dedicated bucket lifecycle to keep only the latest object
   version, delete hidden/noncurrent versions after the shortest reviewed
   delay, and cancel unfinished multipart uploads after one day. Scope any
   custom rule to the Restic repository prefix and verify its displayed rule.
6. Configure account usage alerts and the strictest available storage/spending
   cap compatible with the 10 GB free allowance. If the account can remain in
   a non-billing state, prefer that over relying on an assumed zero-dollar cap.
7. Before repository initialization or the first production upload, confirm
   the account-wide Usage view starts at the expected amount and verify the
   configured protections are active. The free 10 GB allowance is account-wide,
   not guaranteed to be dedicated to this bucket.

Restic currently recommends the B2 S3-compatible API instead of its native B2
backend. Keep the repository private; bucket names and object metadata must
not contain employee, customer, invoice, or other sensitive identifiers.

## Secret handling

Create these root-owned files on the VPS with mode `0400`. Enter their values
with `sudoedit` or another method that does not place them in shell history:

```text
/etc/abap/credentials/restic_password
/etc/abap/credentials/b2_key_id
/etc/abap/credentials/b2_application_key
/etc/abap/credentials/heartbeat_backup_url
/etc/abap/credentials/heartbeat_maintenance_url
/etc/abap/credentials/heartbeat_full_check_url
/etc/abap/credentials/heartbeat_operations_url
```

Each file contains only its value and one final newline. The Restic password
must be long and randomly generated. Store an independent copy in the owner's
password manager; losing it makes the repository unrecoverable.

The scripts reject a symlinked or non-root-owned operations configuration and
reject configuration or fallback credential files with any group/world access.
Do not weaken those ownership or mode requirements to work around a startup
failure; correct the installed file instead.

The systemd units use `LoadCredential=`. At runtime, systemd makes temporary,
read-only credential files available through `CREDENTIALS_DIRECTORY`. Scripts
read B2 values into their environment, give Restic the password file path, and
feed Better Stack's secret URL to curl through standard input. No secret is
embedded in Git, a unit, an argument, or normal journal output.

Do not back up `/etc/abap/credentials` into the same repository. Do not alter
`/etc/abap/production.env`; it is only read and copied into the encrypted
snapshot.

## Install the reviewed repository artifacts

These commands are examples for the later approved VPS change. Confirm the
reviewed commit and a clean checkout first.

```bash
cd /opt/abap/app
sudo install -d -o root -g root -m 0755 /usr/local/lib/abap
sudo install -d -o root -g root -m 0700 /etc/abap/credentials /var/backups/abap
sudo install -o root -g root -m 0644 \
  deploy/hosthatch/abap-operations-lib.sh \
  /usr/local/lib/abap/abap-operations-lib.sh
sudo install -o root -g root -m 0755 \
  deploy/hosthatch/abap-backup.sh /usr/local/sbin/abap-backup
sudo install -o root -g root -m 0755 \
  deploy/hosthatch/abap-backup-maintenance.sh \
  /usr/local/sbin/abap-backup-maintenance
sudo install -o root -g root -m 0755 \
  deploy/hosthatch/abap-operations-check.sh \
  /usr/local/sbin/abap-operations-check
sudo install -o root -g root -m 0600 \
  deploy/hosthatch/abap-operations.conf.example \
  /etc/abap/operations.conf
sudo install -o root -g root -m 0644 \
  deploy/hosthatch/systemd/abap-*.service \
  deploy/hosthatch/systemd/abap-*.timer \
  /etc/systemd/system/
```

Edit only `/etc/abap/operations.conf` to replace the B2 endpoint placeholders.
Do not add secrets to that file. Before enabling anything:

```bash
sudo bash -n \
  /usr/local/lib/abap/abap-operations-lib.sh \
  /usr/local/sbin/abap-backup \
  /usr/local/sbin/abap-backup-maintenance \
  /usr/local/sbin/abap-operations-check
sudo systemd-analyze verify /etc/systemd/system/abap-*.service /etc/systemd/system/abap-*.timer
sudo systemctl daemon-reload
sudo systemctl list-timers --all 'abap-*'
```

Also verify `/var/backups/abap` is a real, root-owned `0700` directory and is
not a mount point. The backup refuses symlinked, mounted, non-root-owned, or
group/world-accessible staging paths and rejects nested mounts before cleanup.

Install a reviewed, pinned Restic package separately. This repository does not
install Restic or initialize a remote repository.

## Initialize and prove the repository

Repository initialization is a one-time, separately approved operation. Load
the root-only credentials into environment variables without printing them,
set `RESTIC_PASSWORD_FILE` to the password-file path, and run `restic init`
against the configured repository. Do not place keys, passwords, or the
repository password in command arguments.

Before enabling timers:

1. Recheck Backblaze's account-wide Usage view and confirm the reviewed caps,
   alerts, and non-billing protections are active.
2. Run the backup service manually with `sudo systemctl start abap-backup`.
3. Inspect `sudo systemctl --no-pager --full status abap-backup` and the journal.
4. Confirm one encrypted snapshot exists and records only the two approved
   source paths, then recheck Backblaze's account-wide Usage view.
5. Confirm staging is empty after the attempt.
6. Perform the isolated restore drill below.
7. Run the exact production retention policy without deletion and review every
   proposed keep/remove decision:

   ```bash
   sudo /usr/local/sbin/abap-backup-maintenance retention-dry-run
   ```

   It must select only the `abap-production` host/tag groups, preserve every
   `release` snapshot, and match 14 daily, 8 weekly, and 12 monthly points.
8. Induce one harmless test failure using a disposable test configuration and
   confirm Better Stack alerts. Do not damage or misconfigure production to
   test alerts.
9. Only then enable all four timers:

```bash
sudo systemctl enable --now \
  abap-backup.timer \
  abap-backup-maintenance.timer \
  abap-backup-full-check.timer \
  abap-operations-check.timer
```

Create a release snapshot before a significant deployment or migration by
running the reviewed backup executable with the non-secret `--release` flag.
Confirm the resulting snapshot has both `release` and unique run tags before
continuing the deployment.

## Better Stack configuration

Create these resources manually; repository code does not call Better Stack's
management API:

| Resource | Suggested period and grace |
| --- | --- |
| Daily backup heartbeat | 24 hours, 2-hour grace |
| Weekly maintenance heartbeat | 7 days, 6-hour grace |
| Monthly full-check heartbeat | 32 days, 3-day grace |
| Operations heartbeat | 5 minutes, 5-minute grace |
| External uptime monitor | `https://app.dennisbasadre.com/ready`, 3-minute checks |

Enable email and/or push notification for each. The scripts send success only
after their complete acceptance criteria pass and send `/fail` on an explicit
failure. A dead VPS or disabled timer produces a missing-heartbeat alert.

The external `/ready` monitor covers public DNS, Cloudflare, edge TLS, Caddy,
ABAP web, and PostgreSQL readiness. The local operations check separately
validates Caddy's origin certificate because Cloudflare hides it from public
clients.

## Local operations checks

Every five minutes the operations service checks:

- Disk blocks and inodes for `/`, Docker storage, and backup staging: warning
  at 75%, critical at 85%.
- A stale plaintext staging directory older than 24 hours.
- Swap: warning after three consecutive checks at 10% or more, critical at
  50%.
- Docker and Caddy systemd services.
- All four ABAP timers.
- Healthy database, web, and worker containers and a successful migration
  container.
- Local `/health` and database-aware `/ready`.
- No PostgreSQL host port, exact loopback-only web publication, no host TCP
  listener on 5432, and no non-loopback listener on 8000.
- Both public and origin TLS: warning below 21 days, critical below 7 days.

Docker health status does not itself restart an unhealthy process. The monitor
alerts for investigation; it does not create an automatic restart loop.

The backup independently refuses to start `pg_dump` when the actual staging
filesystem is already at the critical disk threshold or cannot preserve both
the configured minimum free-space reserve and the Restic-cache allowance. It
rechecks capacity before copying activity logs and before starting Restic.

## Isolated restore drill

Run quarterly and after any backup-script, retention, credential, Restic, or
storage-provider change. Schedule a maintenance window for the drill even
though production remains online.

1. Select the exact snapshot ID and create a new root-only restore directory
   under `/var/backups/abap/restore-drill-YYYYMMDD`. Never target a production
   path.
2. Restore the selected snapshot into that directory with Restic credentials
   loaded from root-only files. Do not print the credentials.
3. Locate `RECOVERY-MANIFEST.txt`, `SHA256SUMS`, `database.dump`, the copied
   activity logs, and the restored invoice volume tree.
4. Run `sha256sum --check SHA256SUMS`. Recalculate and compare the invoice
   checksums from the restored invoice directory.
5. Run `pg_restore --list database.dump` before creating any database.
6. Create a disposable PostgreSQL container or Compose project with a unique
   non-production name, a new temporary volume, no published port, and a
   synthetic root-only environment file. Do not attach the production
   `database_data` volume or use the `abap-deploy` project name.
7. Restore the dump into the disposable database, start a disposable ABAP web
   container against it, and verify `/health`, `/ready`, representative records,
   and invoice-document hashes/downloads.
8. Record the snapshot ID, start/end time, restored sizes, test results, and
   measured recovery time without recording secrets or business data.
9. Stop and remove only the explicitly named disposable containers and
   disposable restore volume. Remove only the exact restore-drill directory
   after its evidence is recorded. Never use `docker compose down -v` against
   production and never restore over live resources.

If any step fails, preserve the last known-good off-server snapshots, alert,
and diagnose. Do not initialize PostgreSQL, rotate the production database
password, change `ABAP_SESSION_SECRET`, or overwrite a production volume.

## Expected growth and first-month review

The implementation intentionally avoids whole-host and raw-volume backups.
Configuration and activity-log chunks deduplicate well. Invoice PDFs add only
their actual immutable size. The daily custom database dump is likely to be
the largest changing object; compressed dump chunks may deduplicate less well
than ordinary files when rows or indexes change.

After the first successful backup, record:

- Staged dump, activity-log, and invoice sizes.
- Restic raw-data size.
- Backblaze authoritative `stored_gb`.

Repeat weekly for four weeks. Estimate monthly growth from the B2 values, not
from guesswork. If the trend projects 7 GB within three months, reduce growth
at its source or select a paid/alternative repository before continuing. Do
not weaken retention silently and do not wait for 8.5 GB.
