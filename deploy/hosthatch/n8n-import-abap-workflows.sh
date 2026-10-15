#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

readonly N8N_IMAGE="sha256:240eaa2a3d491adac5817aa4c3f1c521bb18ec79f6e448517158d5220ee0f37b"
readonly N8N_VOLUME="n8n_n8n_data"
readonly WORKFLOW_DIR="${ABAP_N8N_WORKFLOW_DIR:-/opt/abap/app/examples/n8n}"
readonly TOKEN_FILE="${ABAP_N8N_PROVIDER_TOKEN_FILE:?Set the protected provider-token file path}"
readonly SHARED_LOCK="/run/lock/abap-production-backup.lock"

[[ "$EUID" -eq 0 ]] || { printf 'ERROR: import must run as root.\n' >&2; exit 1; }
[[ -f "$TOKEN_FILE" && ! -L "$TOKEN_FILE" ]] || { printf 'ERROR: unsafe token file.\n' >&2; exit 1; }
(( (8#$(stat -c '%a' "$TOKEN_FILE") & 8#077) == 0 )) || {
  printf 'ERROR: token file permissions are too broad.\n' >&2
  exit 1
}
for file in build-demo-credential.mjs abap-signed-workflow.json abap-signed-processor.json; do
  [[ -r "$WORKFLOW_DIR/$file" ]] || { printf 'ERROR: missing import artifact: %s\n' "$file" >&2; exit 1; }
done

mapfile -t containers < <(docker ps --filter label=com.docker.compose.service=n8n --format '{{.ID}}')
(( ${#containers[@]} == 1 )) || { printf 'ERROR: exactly one running n8n service is required.\n' >&2; exit 1; }
readonly n8n_container="${containers[0]}"
exec 9>"$SHARED_LOCK"
flock -n 9 || { printf 'ERROR: a backup or maintenance operation is running.\n' >&2; exit 1; }

stopped=false
finish() {
  local status=$?
  if [[ "$stopped" == true ]]; then
    docker start "$n8n_container" >/dev/null || status=1
  fi
  exit "$status"
}
trap finish EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

stopped=true
docker stop --time 30 "$n8n_container" >/dev/null
docker run --rm --network none --read-only \
  --mount "type=volume,src=$N8N_VOLUME,dst=/home/node/.n8n" \
  --mount "type=bind,src=$WORKFLOW_DIR,dst=/workflows,readonly" \
  --mount "type=bind,src=$TOKEN_FILE,dst=/run/secrets/abap_n8n_provider_token,readonly" \
  --tmpfs /run/abap-bootstrap:rw,noexec,nosuid,nodev,size=16m,uid=1000,gid=1000,mode=0700 \
  --entrypoint /bin/sh "$N8N_IMAGE" -c '
    node /workflows/build-demo-credential.mjs /run/secrets/abap_n8n_provider_token /run/abap-bootstrap/credential.json &&
    n8n import:credentials --input=/run/abap-bootstrap/credential.json >/dev/null &&
    rm -f /run/abap-bootstrap/credential.json &&
    n8n import:workflow --input=/workflows/abap-signed-workflow.json >/dev/null &&
    n8n import:workflow --input=/workflows/abap-signed-processor.json >/dev/null &&
    n8n unpublish:workflow --id=abapM3Demo000001 >/dev/null &&
    n8n unpublish:workflow --id=abapM3Demo000002 >/dev/null
  '

python3 - /var/lib/docker/volumes/n8n_n8n_data/_data/database.sqlite <<'PY'
import sqlite3, sys
db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
db.execute("PRAGMA query_only=ON")
rows = db.execute(
    "SELECT id, active FROM workflow_entity WHERE id IN (?, ?) ORDER BY id",
    ("abapM3Demo000001", "abapM3Demo000002"),
).fetchall()
if rows != [("abapM3Demo000001", 0), ("abapM3Demo000002", 0)]:
    raise SystemExit("ERROR: imported ABAP workflows are not present and inactive.")
PY

docker start "$n8n_container" >/dev/null
stopped=false
printf 'N8N_IMPORT_OK: ABAP workflows imported and explicitly left inactive.\n'
