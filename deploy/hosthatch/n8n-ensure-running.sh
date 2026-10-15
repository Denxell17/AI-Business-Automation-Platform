#!/usr/bin/env bash
set -Eeuo pipefail

mapfile -t containers < <(
  docker ps -a --filter label=com.docker.compose.service=n8n --format '{{.ID}}'
)
(( ${#containers[@]} == 1 )) || {
  printf 'CRITICAL: exactly one n8n Compose container is required for recovery.\n' >&2
  exit 1
}

container="${containers[0]}"
if [[ "$(docker inspect --format '{{.State.Running}}' "$container")" != true ]]; then
  docker start "$container" >/dev/null
fi
printf 'N8N_RECOVERY_OK: n8n is running.\n'
