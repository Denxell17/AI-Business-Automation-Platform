#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
readonly N8N_IMAGE="sha256:240eaa2a3d491adac5817aa4c3f1c521bb18ec79f6e448517158d5220ee0f37b"
readonly RUN_ID="$(date -u +%Y%m%d%H%M%S)"
readonly ROOT="/var/backups/n8n/preflight-$RUN_ID"
readonly VOLUME="abap_n8n_restore_$RUN_ID"
readonly CONTAINER="abap-n8n-restore-$RUN_ID"

[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
source "$OPERATIONS_LIB"
operations_load_config
operations_configure_restic
readonly N8N_RESTIC_HOST="${ABAP_RESTIC_HOST}-n8n"
[[ "$EUID" -eq 0 ]] || { operations_fail "The restore drill must run as root."; exit 1; }

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  [[ "$ROOT" == /var/backups/n8n/preflight-* ]] && rm -rf -- "$ROOT"
}
trap cleanup EXIT
install -d -o root -g root -m 0700 "$ROOT"
exec 9>/run/lock/abap-production-backup.lock
flock -n 9 || { operations_fail "A backup or maintenance operation is running."; exit 1; }

restic restore latest --host "$N8N_RESTIC_HOST" --tag n8n-production --target "$ROOT"
readonly SOURCE="$ROOT/var/lib/docker/volumes/n8n_n8n_data/_data"
readonly DATABASE="$SOURCE/database.sqlite"
[[ -s "$DATABASE" && -s "$SOURCE/config" ]] || {
  operations_fail "The restored n8n database or config is missing."
  exit 1
}

# Scan definitions in memory and print only counts and workflow IDs.
python3 - "$DATABASE" <<'PY'
import sqlite3, sys
db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
db.execute("PRAGMA query_only=ON")
columns = {row[1] for row in db.execute("PRAGMA table_info(workflow_entity)")}
scan = [name for name in ("nodes", "connections", "settings", "staticData", "pinData") if name in columns]
rows = db.execute(f"SELECT id, {', '.join(scan)} FROM workflow_entity").fetchall()
needles = ("$env", "process.env")
matches = sorted(str(row[0]) for row in rows if any(
    needle in str(value) for value in row[1:] for needle in needles
))
credential_count = db.execute("SELECT COUNT(*) FROM credentials_entity").fetchone()[0]
print(f"workflow_count={len(rows)}")
print(f"credential_count={credential_count}")
print(f"environment_access_match_count={len(matches)}")
for workflow_id in matches:
    print(f"environment_access_workflow_id={workflow_id}")
if matches:
    raise SystemExit("BLOCKER: existing workflows require environment access.")
PY

# Disable only the disposable copy before any n8n process opens it.
python3 - "$DATABASE" <<'PY'
import sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.execute("UPDATE workflow_entity SET active = 0 WHERE active <> 0")
db.commit()
PY

docker volume create "$VOLUME" >/dev/null
docker run --rm --network none --user 0:0 \
  --mount "type=bind,src=$SOURCE,dst=/source,readonly" \
  --mount "type=volume,src=$VOLUME,dst=/home/node/.n8n" \
  --entrypoint /bin/sh "$N8N_IMAGE" \
  -c 'cp -a /source/. /home/node/.n8n/ && chown -R 1000:1000 /home/node/.n8n'

# A decrypted export into private tmpfs proves that the restored encryption key
# can decrypt every credential. The export is never printed or persisted.
docker run --rm --network none --read-only \
  --mount "type=volume,src=$VOLUME,dst=/home/node/.n8n" \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,uid=1000,gid=1000,mode=0700 \
  --entrypoint /bin/sh "$N8N_IMAGE" \
  -c 'n8n export:credentials --all --decrypted --output=/tmp/credentials.json >/dev/null && rm -f /tmp/credentials.json'

docker run -d --name "$CONTAINER" --network none --read-only \
  --mount "type=volume,src=$VOLUME,dst=/home/node/.n8n" \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m,uid=1000,gid=1000,mode=0700 \
  --cpus 0.50 --memory 512m --pids-limit 128 \
  "$N8N_IMAGE" >/dev/null
sleep 10
[[ "$(docker inspect --format '{{.State.Running}}' "$CONTAINER")" == true ]] || {
  operations_fail "The isolated restored n8n container did not remain running."
  exit 1
}
printf 'N8N_RESTORE_OK: isolated restore and credential decryption succeeded.\n'
