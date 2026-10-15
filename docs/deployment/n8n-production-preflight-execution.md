# ABAP-n8n production preflight execution

This is the approved preflight only. It installs the independent backup job,
runs one n8n-only backup window, and uses disposable restore resources. It does
not deploy the provider, import workflows, change PostgreSQL, or enable the
integration.

## Prerequisite

Preferably provision a dedicated Better Stack heartbeat URL at
`/etc/abap/credentials/heartbeat_n8n_backup_url` using the existing protected
credential procedure. It must be root-owned, mode `0600`, and must never be
printed or entered in shell history. It may be deferred for the supervised
initial manual preflight: the backup then reports through its exit status and
systemd journal, and the timer is deliberately left disabled. The credential
is mandatory before enabling the unattended daily schedule.

## Consolidated Windows PowerShell procedure

Run from the repository root. Review all output; any error stops the sequence.

```powershell
param([switch]$ResumeSuccessfulBackup)

$ErrorActionPreference = 'Stop'
$upload = "abap-n8n-preflight-$([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))"
$remoteHome = (ssh abap-prod 'printf %s "$HOME"').Trim()
if ($LASTEXITCODE -ne 0 -or $remoteHome -notmatch '^/[A-Za-z0-9._/-]+$') {
  throw 'Could not determine a safe remote home directory.'
}
$remote = "$remoteHome/$upload"
$localProcedure = Join-Path $env:TEMP "$upload.sh"

ssh abap-prod "umask 077; mkdir -p '$remote'"
if ($LASTEXITCODE -ne 0) { throw 'Could not create the protected remote staging directory.' }

$files = @(
  'deploy/hosthatch/n8n-backup.sh',
  'deploy/hosthatch/n8n-ensure-running.sh',
  'deploy/hosthatch/n8n-preflight-restore.sh',
  'deploy/hosthatch/abap-n8n-migration-rehearsal.sh',
  'deploy/hosthatch/systemd/n8n-backup.service',
  'deploy/hosthatch/systemd/n8n-backup.timer',
  'Projects/employee_management_system/migrations/postgresql/010_add_workflow_n8n_outbox_controls.sql',
  'Projects/employee_management_system/migrations/postgresql/011_add_n8n_demo_event_acceptance.sql',
  'Projects/employee_management_system/migrations/postgresql/012_move_n8n_callback_authority.sql'
)
scp $files "abap-prod:${remote}/"
if ($LASTEXITCODE -ne 0) { throw 'Could not upload all preflight files.' }

$procedure = @'
set -Eeuo pipefail
upload="$1"
mode="${2:-new}"
[[ "$upload" == "$HOME"/abap-n8n-preflight-* && -d "$upload" ]]
[[ "$mode" == new || "$mode" == resume ]]
upload_name="${upload##*/}"
migration_stage="/var/lib/abap-n8n-preflight/$upload_name"

check_live_n8n() {
  mapfile -t ids < <(sudo docker ps -a --filter label=com.docker.compose.service=n8n --format '{{.ID}}')
  (( ${#ids[@]} == 1 )) || { printf 'ERROR: exactly one n8n container is required.\n' >&2; return 1; }
  [[ "$(sudo docker inspect --format '{{.State.Running}}' "${ids[0]}")" == true ]] || {
    printf 'ERROR: n8n is not running.\n' >&2
    return 1
  }
  curl --fail --silent --show-error --max-time 15 http://127.0.0.1:5678/healthz >/dev/null || {
    printf 'ERROR: n8n health endpoint failed.\n' >&2
    return 1
  }
  printf 'N8N_LIVE_HEALTH_OK\n'
}

check_abap_ready() {
  sudo bash -c '
    set -Eeuo pipefail
    source /usr/local/lib/abap/abap-operations-lib.sh
    operations_load_config
    docker compose \
      --env-file "$ABAP_ENV_FILE" \
      -f "$ABAP_COMPOSE_BASE_FILE" \
      -f "$ABAP_COMPOSE_OVERLAY_FILE" \
      exec -T web python -c \
      "import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:8000/ready\", timeout=10)"
  ' >/dev/null
  printf 'ABAP_READY_OK\n'
}

finish() {
  status=$?
  trap - EXIT
  if ! check_live_n8n; then status=1; fi
  exit "$status"
}
trap finish EXIT
heartbeat_ready=false
heartbeat_path=/etc/abap/credentials/heartbeat_n8n_backup_url
if sudo test -e "$heartbeat_path" || sudo test -L "$heartbeat_path"; then
  if ! sudo test -f "$heartbeat_path" || sudo test -L "$heartbeat_path" || \
     ! sudo test "$(sudo stat -c '%U:%a' "$heartbeat_path")" = root:600; then
    printf 'ERROR: existing n8n heartbeat credential is not a root-owned mode-0600 regular file.\n' >&2
    exit 1
  fi
  if sudo test -s "$heartbeat_path"; then
    heartbeat_ready=true
  else
    printf 'N8N_BACKUP_MONITORING_DEFERRED: existing empty placeholder; timer will remain disabled.\n'
  fi
else
  printf 'N8N_BACKUP_MONITORING_DEFERRED: supervised run only; timer will remain disabled.\n'
fi

sudo bash -n \
  "$upload/n8n-backup.sh" \
  "$upload/n8n-ensure-running.sh" \
  "$upload/n8n-preflight-restore.sh" \
  "$upload/abap-n8n-migration-rehearsal.sh"
for migration in \
  010_add_workflow_n8n_outbox_controls.sql \
  011_add_n8n_demo_event_acceptance.sql \
  012_move_n8n_callback_authority.sql; do
  [[ -s "$upload/$migration" ]] || { printf 'ERROR: missing or empty migration: %s\n' "$migration" >&2; exit 1; }
done
grep -Fq -- '--tag n8n-production' "$upload/n8n-backup.sh"
if grep -Fq -- '--tag abap-production' "$upload/n8n-backup.sh" || \
   grep -Fq -- '--prune' "$upload/n8n-backup.sh"; then
  printf 'ERROR: n8n backup retention is not isolated.\n' >&2
  exit 1
fi
sha256sum "$upload"/*

check_abap_ready
check_live_n8n

n8n_image='sha256:240eaa2a3d491adac5817aa4c3f1c521bb18ec79f6e448517158d5220ee0f37b'
postgres_image='sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280'
sudo docker image inspect "$n8n_image" >/dev/null
sudo docker image inspect "$postgres_image" >/dev/null
live_n8n_id="$(sudo docker ps --filter label=com.docker.compose.service=n8n --format '{{.ID}}')"
[[ -n "$live_n8n_id" ]]
live_n8n_image_id="$(sudo docker inspect --format '{{.Image}}' "$live_n8n_id")"
expected_n8n_image_id="$(sudo docker image inspect --format '{{.Id}}' "$n8n_image")"
[[ "$live_n8n_image_id" == "$expected_n8n_image_id" ]] || {
  printf 'ERROR: live n8n is not using the pinned preflight image.\n' >&2
  exit 1
}
printf 'PREFLIGHT_IMAGES_OK\n'

sudo install -d -o root -g root -m 0700 /var/backups/n8n
sudo install -o root -g root -m 0750 "$upload/n8n-backup.sh" /usr/local/sbin/n8n-backup
sudo install -o root -g root -m 0750 "$upload/n8n-ensure-running.sh" /usr/local/sbin/n8n-ensure-running
sudo install -o root -g root -m 0750 "$upload/n8n-preflight-restore.sh" /usr/local/sbin/n8n-preflight-restore
sudo install -o root -g root -m 0750 "$upload/abap-n8n-migration-rehearsal.sh" /usr/local/sbin/abap-n8n-migration-rehearsal
sudo systemd-analyze verify \
  "$upload/n8n-backup.service" \
  "$upload/n8n-backup.timer"
sudo install -o root -g root -m 0644 "$upload/n8n-backup.service" /etc/systemd/system/n8n-backup.service
sudo install -o root -g root -m 0644 "$upload/n8n-backup.timer" /etc/systemd/system/n8n-backup.timer
sudo install -d -o root -g root -m 0700 "$migration_stage"
for migration in \
  010_add_workflow_n8n_outbox_controls.sql \
  011_add_n8n_demo_event_acceptance.sql \
  012_move_n8n_callback_authority.sql; do
  sudo install -o root -g root -m 0600 "$upload/$migration" "$migration_stage/$migration"
done

sudo systemctl daemon-reload
sudo systemctl disable --now n8n-backup.timer >/dev/null 2>&1 || true
if [[ "$heartbeat_ready" != true ]]; then
  if ! sudo test -e "$heartbeat_path"; then
    sudo install -o root -g root -m 0600 /dev/null "$heartbeat_path"
  fi
fi
if [[ "$mode" == new ]]; then
  backup_started_at="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"
  set +e
  sudo systemctl start n8n-backup.service
  service_start_exit=$?
  set -e
else
  service_start_exit=0
  backup_started_at="$(date -u -d "$(sudo systemctl show n8n-backup.service \
    --property=ExecMainStartTimestamp --value)" +'%Y-%m-%d %H:%M:%S UTC')"
  printf 'N8N_BACKUP_REUSE_REQUESTED: no additional n8n stop will occur.\n'
fi
service_result="$(sudo systemctl show n8n-backup.service --property=Result --value)"
service_exit="$(sudo systemctl show n8n-backup.service --property=ExecMainStatus --value)"
[[ "$service_start_exit" == 0 && "$service_result" == success && "$service_exit" == 0 ]] || {
  printf 'ERROR: n8n backup service start=%s result=%s exit=%s.\n' \
    "$service_start_exit" "$service_result" "$service_exit" >&2
  exit 1
}
new_run_tag="$(sudo journalctl -u n8n-backup.service --since "$backup_started_at" -o cat --no-pager \
  | sed -n 's/.*\(run-[0-9]\{8\}T[0-9]\{6\}Z\).*/\1/p' | tail -n 1)"
[[ "$new_run_tag" =~ ^run-[0-9]{8}T[0-9]{6}Z$ ]] || {
  printf 'ERROR: the new n8n snapshot tag could not be identified.\n' >&2
  exit 1
}
printf 'N8N_BACKUP_SERVICE_OK: result=success exit=0 tag=%s\n' "$new_run_tag"
check_live_n8n
printf 'N8N_BACKUP_TIMER_READY_NOT_ENABLED: activation requires the next approval gate.\n'

sudo /usr/local/sbin/n8n-preflight-restore
sudo ABAP_MIGRATION_DIR="$migration_stage" \
  /usr/local/sbin/abap-n8n-migration-rehearsal

check_abap_ready
sudo docker ps --filter label=com.docker.compose.service=n8n \
  --format 'n8n={{.Status}} image={{.Image}}'
sudo bash -c '
  source /usr/local/lib/abap/abap-operations-lib.sh
  operations_load_config
  operations_configure_restic
  restic snapshots --host "${ABAP_RESTIC_HOST}-n8n" --tag "$1" --json
' bash "$new_run_tag" | python3 -c '
import datetime, json, sys
snapshots = json.load(sys.stdin)
if len(snapshots) != 1:
    raise SystemExit("ERROR: expected exactly one newly tagged n8n snapshot.")
snapshot = snapshots[0]
tags = set(snapshot.get("tags") or [])
required = {"n8n-production", sys.argv[2]}
if not required <= tags:
    raise SystemExit("ERROR: the new snapshot does not contain both required tags.")
created = datetime.datetime.fromisoformat(str(snapshot.get("time", "")).replace("Z", "+00:00"))
started = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d %H:%M:%S UTC").replace(
    tzinfo=datetime.timezone.utc
)
if created < started or created > datetime.datetime.now(datetime.timezone.utc):
    raise SystemExit("ERROR: the snapshot timestamp is outside this execution window.")
print("N8N_NEW_SNAPSHOT_OK: id=%s time=%s" % (
    str(snapshot.get("short_id") or snapshot.get("id", ""))[:12],
    snapshot.get("time", ""),
))
' "$backup_started_at" "$new_run_tag"

[[ "$migration_stage" == /var/lib/abap-n8n-preflight/abap-n8n-preflight-* ]]
sudo rm -rf -- "$migration_stage"
sudo rmdir /var/lib/abap-n8n-preflight 2>/dev/null || true
rm -rf -- "$upload"
check_live_n8n
trap - EXIT
printf 'PRODUCTION_PREFLIGHT_OK\n'
'@

[System.IO.File]::WriteAllText(
  $localProcedure,
  $procedure,
  [System.Text.UTF8Encoding]::new($false)
)
try {
  scp $localProcedure "abap-prod:${remote}/run-preflight.sh"
  if ($LASTEXITCODE -ne 0) { throw 'Could not upload the preflight runner.' }
  $mode = if ($ResumeSuccessfulBackup) { 'resume' } else { 'new' }
  ssh -t abap-prod "bash '$remote/run-preflight.sh' '$remote' '$mode'"
  if ($LASTEXITCODE -ne 0) { throw "Remote preflight failed with exit code $LASTEXITCODE." }
}
finally {
  Remove-Item -LiteralPath $localProcedure -Force -ErrorAction SilentlyContinue
}
```

The final snapshot listing must contain the new `n8n-production` snapshot, the
restore command must report `N8N_RESTORE_OK`, the migration command must report
`MIGRATION_REHEARSAL_OK`, and the last line must be
`PRODUCTION_PREFLIGHT_OK`. Do not proceed if the compatibility scan reports any
environment-access workflow IDs.
