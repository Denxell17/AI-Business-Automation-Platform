#!/usr/bin/env bash
set -Eeuo pipefail
umask 0077

readonly OPERATIONS_LIB="${ABAP_OPERATIONS_LIB:-/usr/local/lib/abap/abap-operations-lib.sh}"
readonly POSTGRES_IMAGE="sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280"
readonly RUN_ID="$(date -u +%Y%m%d%H%M%S)"
readonly ROOT="/var/backups/abap/n8n-rehearsal-$RUN_ID"
readonly NETWORK="abap-n8n-rehearsal-$RUN_ID"
readonly VOLUME="abap_n8n_rehearsal_$RUN_ID"
readonly DATABASE_CONTAINER="abap-n8n-db-$RUN_ID"
readonly MIGRATION_DIR="${ABAP_MIGRATION_DIR:-/opt/abap/app/Projects/employee_management_system/migrations/postgresql}"

[[ -r "$OPERATIONS_LIB" ]] || { printf 'ERROR: operations library is unavailable.\n' >&2; exit 1; }
source "$OPERATIONS_LIB"
operations_load_config
operations_configure_restic
[[ "$EUID" -eq 0 ]] || { operations_fail "The migration rehearsal must run as root."; exit 1; }
for migration in 010_add_workflow_n8n_outbox_controls.sql 011_add_n8n_demo_event_acceptance.sql 012_move_n8n_callback_authority.sql; do
  [[ -r "$MIGRATION_DIR/$migration" ]] || { operations_fail "Missing migration: $migration"; exit 1; }
done

cleanup() {
  docker rm -f "$DATABASE_CONTAINER" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  [[ "$ROOT" == /var/backups/abap/n8n-rehearsal-* ]] && rm -rf -- "$ROOT"
}
trap cleanup EXIT
install -d -o root -g root -m 0700 "$ROOT"
exec 9>/run/lock/abap-production-backup.lock
flock -n 9 || { operations_fail "A backup or maintenance operation is running."; exit 1; }

restic restore latest --host "$ABAP_RESTIC_HOST" --tag abap-production --target "$ROOT"
dump_file="$(find "$ROOT" -type f -name database.dump -print -quit)"
[[ -n "$dump_file" && -s "$dump_file" ]] || { operations_fail "Restored PostgreSQL dump is missing."; exit 1; }

password="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker network create --internal "$NETWORK" >/dev/null
docker volume create "$VOLUME" >/dev/null
docker run -d --name "$DATABASE_CONTAINER" --network "$NETWORK" \
  --mount "type=volume,src=$VOLUME,dst=/var/lib/postgresql" \
  -e POSTGRES_DB=abap_rehearsal -e POSTGRES_USER=abap_rehearsal \
  -e POSTGRES_PASSWORD="$password" --shm-size 256m \
  --cpus 0.70 --memory 1536m --pids-limit 256 "$POSTGRES_IMAGE" >/dev/null
for _ in $(seq 1 30); do
  docker exec "$DATABASE_CONTAINER" pg_isready -U abap_rehearsal -d abap_rehearsal >/dev/null 2>&1 && break
  sleep 2
done
docker exec "$DATABASE_CONTAINER" pg_isready -U abap_rehearsal -d abap_rehearsal >/dev/null
docker exec -i "$DATABASE_CONTAINER" pg_restore -U abap_rehearsal -d abap_rehearsal --no-owner --no-privileges <"$dump_file"

started="$(date +%s%3N)"
for migration in 010_add_workflow_n8n_outbox_controls.sql 011_add_n8n_demo_event_acceptance.sql 012_move_n8n_callback_authority.sql; do
  docker cp "$MIGRATION_DIR/$migration" "$DATABASE_CONTAINER:/tmp/$migration"
done
{
  printf "\\i /tmp/010_add_workflow_n8n_outbox_controls.sql\n"
  printf "INSERT INTO schema_migrations (migration_name) VALUES ('010_add_workflow_n8n_outbox_controls.sql');\n"
  printf "\\i /tmp/011_add_n8n_demo_event_acceptance.sql\n"
  printf "INSERT INTO schema_migrations (migration_name) VALUES ('011_add_n8n_demo_event_acceptance.sql');\n"
  printf "\\i /tmp/012_move_n8n_callback_authority.sql\n"
  printf "INSERT INTO schema_migrations (migration_name) VALUES ('012_move_n8n_callback_authority.sql');\n"
} | docker exec -i -e PGOPTIONS='-c lock_timeout=5s -c statement_timeout=60s' "$DATABASE_CONTAINER" \
  psql -X -v ON_ERROR_STOP=1 -U abap_rehearsal -d abap_rehearsal -1 >/dev/null
elapsed="$(( $(date +%s%3N) - started ))"

docker exec "$DATABASE_CONTAINER" psql -X -v ON_ERROR_STOP=1 -U abap_rehearsal -d abap_rehearsal -Atc \
  "SELECT (SELECT count(*) FROM workflows WHERE n8n_enabled), to_regclass('public.n8n_demo_events') IS NOT NULL;" \
  | grep -Fx '0|t' >/dev/null

# The currently deployed web image represents the application rollback target.
web_id="$(docker ps --filter label=com.docker.compose.service=web --format '{{.ID}}' | head -n 1)"
[[ -n "$web_id" ]] || { operations_fail "The current ABAP web image was not found."; exit 1; }
web_image="$(docker inspect --format '{{.Image}}' "$web_id")"
docker run --rm --network "$NETWORK" \
  -e ABAP_ENVIRONMENT=production -e ABAP_INTEGRATIONS_ENABLED=false \
  -e ABAP_SESSION_SECRET=synthetic-rehearsal-session-secret-123456 \
  -e DATABASE_BACKEND=postgresql \
  -e "DATABASE_URL=postgresql://abap_rehearsal:$password@$DATABASE_CONTAINER:5432/abap_rehearsal" \
  "$web_image" python -c 'from deployment import create_application; create_application()' >/dev/null

printf 'MIGRATION_REHEARSAL_OK: migrations_ms=%s rollback_image=%s\n' "$elapsed" "$web_image"
