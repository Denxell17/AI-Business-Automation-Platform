#!/usr/bin/env bash
set -Eeuo pipefail

mapfile -t containers < <(
  docker ps -a --filter label=com.docker.compose.project=n8n \
    --filter label=com.docker.compose.service=n8n --format '{{.ID}}'
)
(( ${#containers[@]} == 1 )) || {
  printf 'CRITICAL: exactly one standalone production n8n service is required.\n' >&2
  exit 1
}

container="${containers[0]}"
if [[ "$(docker inspect --format '{{.State.Running}}' "$container")" != true ]]; then
  printf 'CRITICAL: standalone n8n is not running; automatic lifecycle changes are prohibited.\n' >&2
  exit 1
fi
printf 'N8N_STATE_OK: standalone n8n is running; no lifecycle action performed.\n'
