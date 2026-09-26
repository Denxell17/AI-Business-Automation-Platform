# ABAP Compose Deployment Runbook

## Scope

This runbook documents the repository's Compose deployment package. It is a
reproducible portfolio/development package, not a claim that ABAP is publicly
hosted or production-operated. A deployer is responsible for TLS, ingress,
backups, monitoring, and the secret-management environment.

The package uses `Dockerfile`, `compose.deploy.yaml`, and
`Projects/employee_management_system/deployment.py`. It runs the application
as an unprivileged user with PostgreSQL, persistent activity logs, and
HTTPS-only session cookies. `compose.yaml` remains the local PostgreSQL
development setup.

## Configure the environment

Copy `.env.example` to an ignored `.env.deploy` file. Set a dedicated
PostgreSQL database, user, and random password, then set:

```text
DATABASE_BACKEND=postgresql
DATABASE_URL=postgresql://abap_user:PASSWORD@database:5432/abap?connect_timeout=5
ABAP_SESSION_SECRET=<a separate random secret of at least 32 characters>
```

URL-encode special password characters. Generate a session secret with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep the session secret stable across restarts and replicas. Leave
`OPENAI_API_KEY` and `AI_ASSISTANT_MODEL` empty unless deliberately enabling
the optional AI capability; probes, migrations, and automated tests do not
need AI calls.

Never commit an environment file, send it in image build arguments, or share
rendered Compose configuration containing secrets. A hosting platform should
inject the same values through its secret manager.

## Build and start

From the repository root, with Docker and Docker Compose installed:

```powershell
docker compose --env-file .env.deploy -f compose.deploy.yaml config --quiet
docker compose --env-file .env.deploy -f compose.deploy.yaml build
docker compose --env-file .env.deploy -f compose.deploy.yaml up -d --wait
docker compose --env-file .env.deploy -f compose.deploy.yaml ps -a
docker compose --env-file .env.deploy -f compose.deploy.yaml exec web python admin_setup.py
```

The database must be healthy before the one-shot migration service runs; the
web service starts only after migrations succeed. The administrator command
prompts for a password and creates an account only when no accounts exist.
Do not seed default credentials.

For a non-Compose host, set the same environment, run `python -m deployment`
once as a release step from the application directory, then start:

```text
python -m uvicorn deployment:create_application --factory --host 0.0.0.0 --port 8000 --no-proxy-headers
```

Do not run concurrent migration jobs. Development reload is not enabled.
Use a dedicated database and restrict database-network and credential access.

## HTTPS and health checks

The Compose web port binds to host loopback at `127.0.0.1:8000`; PostgreSQL
has no published host port. Put a reverse proxy or platform ingress with valid
TLS in front of the web service and redirect public HTTP to HTTPS. Do not
expose port 8000 directly. TLS provisioning is an operator prerequisite and is
not bundled with this repository.

Production cookies use `Secure`, `HttpOnly`, and `SameSite=Lax`. Forwarded
headers are disabled by default; if an ingress needs them, configure
`--proxy-headers` and `--forwarded-allow-ips` for its exact trusted addresses.

- `GET /health` is a database-independent liveness check.
- `GET /ready` returns `200` only with a usable core schema; otherwise it
  returns a safe `503`.
- Compose checks `/ready` every 15 seconds with a five-second request timeout,
  three retries, and a 20-second startup grace period.

```powershell
curl.exe --fail http://127.0.0.1:8000/health
curl.exe --fail http://127.0.0.1:8000/ready
docker compose --env-file .env.deploy -f compose.deploy.yaml logs --tail 100 migrate web
```

See [Docker Compose startup ordering](https://docs.docker.com/compose/how-tos/startup-order/)
and [Uvicorn deployment guidance](https://www.uvicorn.org/deployment/) for
the underlying behavior.

## Verification and operations

```powershell
docker run --rm abap:day154 python -m unittest discover -s tests -p test_deployment.py -v
docker run --rm abap:day154 python run_tests.py
```

Run live PostgreSQL integration tests only against a dedicated disposable
database after migrations. Set `ABAP_TEST_DATABASE_URL` and run
`python -m unittest discover -s tests -p test_postgresql_integration.py -v`
inside the image on that database's network. Never target production.

Use PostgreSQL-native tools for backups and prove a restore to a separate
database. Preserve the `database_data` and `activity_logs` volumes. `down`
stops services while retaining volumes; do not use `down -v` where retained
data matters. Migrations have no automatic downgrade, so retain the previous
image and plan rollback around schema compatibility or a tested restore.

## Private n8n demonstration

`compose.n8n-demo.yaml` is an integration-test/development overlay, not a
production deployment. It adds pinned n8n, a private persistent volume, a
deterministic provider, and the webhook retry worker. Neither n8n nor the
provider publishes a host port.

Use a disposable Compose project with synthetic values in an ignored
environment file. Alongside the PostgreSQL and session configuration, set
distinct random `ABAP_OUTBOUND_WEBHOOK_SECRET` and
`ABAP_INBOUND_WEBHOOK_SECRET`, plus `ABAP_N8N_ENCRYPTION_KEY`. Then run:

```powershell
docker compose --env-file .env.n8n-demo -p abap_n8n_demo -f compose.deploy.yaml -f compose.n8n-demo.yaml --profile n8n-demo up -d --wait
docker compose --env-file .env.n8n-demo -p abap_n8n_demo -f compose.deploy.yaml -f compose.n8n-demo.yaml --profile n8n-demo ps
```

The overlay is limited to synthetic `local` or `integration-test` use. Its
internal n8n address is not an authorization substitute for a future
production integration.
