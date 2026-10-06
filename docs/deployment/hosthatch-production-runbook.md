# HostHatch production deployment

This runbook applies the HostHatch-specific production layer on top of the
provider-neutral `Dockerfile` and `compose.deploy.yaml`. It is designed for the
existing `abap-deploy` Compose project and its existing named volumes. Do not
change the Compose project name and never use `docker compose down -v`.

The initial public release runs PostgreSQL, the migration job, ABAP web, and
the workflow worker. Caddy runs on the host. n8n and production integrations
remain disabled until the HTTPS and backup/restore gates pass.

## Repository configuration decisions

- `compose.deploy.yaml` remains the provider-neutral base.
- `compose.hosthatch.yaml` explicitly selects the production environment,
  disables integrations, gives the long-running containers conservative CPU,
  memory, and PID limits, and configures Uvicorn to trust only the exact Docker
  bridge gateway used by host Caddy.
- The existing `abap-deploy_database_data`, `abap-deploy_activity_logs`, and
  `abap-deploy_invoice_documents` volumes remain authoritative. The overlay
  neither renames nor recreates them.
- `/app/exports` is not persistent. The public employee CSV download is built
  in memory. The CLI-only `employee_report.csv` is reproducible output rather
  than authoritative data. Add a volume only if production starts using that
  CLI artifact as a retained record.
- The application activity log uses a long-lived file handle. Host logrotate
  therefore uses `copytruncate`; no application change or restart is needed.
- Docker stdout/stderr rotation remains the host daemon's responsibility. The
  verified `10m`/three-file daemon policy is intentionally not duplicated here.

The steady-state container limits total 1.95 CPU and 3.75 GiB RAM. The
migration job can temporarily use another 0.50 CPU and 768 MiB, but exits
before web and worker are admitted by their dependency rules. This leaves
headroom in an 8 GiB VPS for Ubuntu, Docker, Caddy, filesystem cache, backup
operations, and the existing 2 GiB emergency swap. Swap is not normal working
memory; sustained swap use is an alert condition.

## 1. Preserve the current deployment

Run these commands as the existing non-root sudo user. Keep the current
deployment running; do not run `down`.

```bash
cd /opt/abap/app
sudo install -d -o root -g root -m 0700 /var/backups/abap
sudo docker compose --env-file .env.deploy -f compose.deploy.yaml exec -T database \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  | sudo tee /var/backups/abap/pre-hosthatch-overlay.dump >/dev/null
sudo tar --acls --xattrs -C /var/lib/docker/volumes -czf \
  /var/backups/abap/pre-hosthatch-overlay-files.tar.gz \
  abap-deploy_activity_logs/_data \
  abap-deploy_invoice_documents/_data
sudo sha256sum /var/backups/abap/pre-hosthatch-overlay.*
```

Copy both backup files and their recorded checksums to encrypted off-server
storage before changing the public edge. A backup is not accepted until its
restore is tested later in an isolated database/volume set.

Confirm that the protected resources still exist:

```bash
sudo docker volume inspect \
  abap-deploy_database_data \
  abap-deploy_activity_logs \
  abap-deploy_invoice_documents >/dev/null
sudo docker compose --env-file .env.deploy -f compose.deploy.yaml ps
```

## 2. Move configuration outside the checkout

Copy the existing environment file without printing or changing any value.
In particular, retain the existing database password and
`ABAP_SESSION_SECRET` so the database and signed sessions remain valid.

```bash
sudo install -d -o root -g root -m 0750 /etc/abap
sudo install -o root -g root -m 0600 \
  /opt/abap/app/.env.deploy /etc/abap/production.env
sudo stat -c '%U %G %a %n' /etc/abap /etc/abap/production.env
```

Do not `cat`, echo, paste into shell history, or commit this file. Use
`sudoedit /etc/abap/production.env` for later changes. It must retain the
existing values required by `compose.deploy.yaml`, including:

- `ABAP_IMAGE_TAG=prod`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL` using the private Compose hostname `database`
- the unchanged `ABAP_SESSION_SECRET`
- any already-approved optional AI and worker settings

The overlay sets `ABAP_ENVIRONMENT=production` and
`ABAP_INTEGRATIONS_ENABLED=false` directly, so integration destinations and
secrets are neither required nor activated for this release.

Find the exact gateway that host Caddy will use when it reaches the loopback
published port:

```bash
sudo docker network inspect abap-deploy_default \
  --format '{{(index .IPAM.Config 0).Gateway}}'
```

Add the returned single IP to `/etc/abap/production.env` with `sudoedit`:

```text
ABAP_FORWARDED_ALLOW_IPS=<the exact abap-deploy_default gateway IP>
```

Do not use `*`, a broad private CIDR, or a Cloudflare address range. Caddy is
the immediate trusted proxy; Cloudflare is not the process connecting to the
container. Re-check this value if the Compose network is ever intentionally
deleted and recreated.

## 3. Install and stage Caddy

Use Caddy's official stable Ubuntu/Debian package. The package creates and
starts the `caddy` systemd service.

```bash
sudo apt install --yes debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install --yes caddy
sudo install -o root -g root -m 0644 \
  deploy/hosthatch/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

Caddy supplies automatic HTTPS and redirects public HTTP to HTTPS. Do not add
HSTS until the hostname, certificate renewal, and any required subdomains have
been verified. The Caddy origin certificate is publicly trusted and therefore
works with Cloudflare Full (strict).

## 4. Install activity-log rotation

First verify that Docker uses `/var/lib/docker`:

```bash
sudo docker info --format '{{.DockerRootDir}}'
```

If the output differs, update only the path in the logrotate template before
installing it. With the verified default path:

```bash
sudo install -o root -g root -m 0644 \
  deploy/hosthatch/abap-activity-logrotate.conf \
  /etc/logrotate.d/abap-activity
sudo logrotate --debug /etc/logrotate.d/abap-activity
```

The debug command must identify the ABAP log without reporting unsafe
permissions or configuration errors. Do not force a rotation during rollout.

## 5. Validate the merged deployment before applying it

After the reviewed repository commit is available, update the checkout using
the normal fast-forward workflow. Confirm the exact approved commit and a
clean tree before continuing.

```bash
cd /opt/abap/app
git fetch origin
git status --short --branch
git pull --ff-only origin main
git rev-parse HEAD
git status --short
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  config --quiet
```

Review the non-secret structural fields without rendering the environment
mapping. The expected public bindings are Caddy on 80/443 and ABAP on host
loopback only; PostgreSQL must have no host port.

```bash
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  config --services
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  config --volumes
```

Expected services are `database`, `migrate`, `web`, and `worker`. Expected
volumes are `database_data`, `activity_logs`, and `invoice_documents`. Do not
use a different `-p`/project name.

## 6. Apply the overlay without removing data

Compose may recreate containers, but it must reuse the existing named volumes.
Do not run `down`, `down -v`, `volume rm`, admin setup, or a separate concurrent
migration command.

```bash
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  up -d --build --wait
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  ps -a
curl --fail --silent --show-error http://127.0.0.1:8000/health
curl --fail --silent --show-error http://127.0.0.1:8000/ready
```

The migration job must be `Exited (0)`; database, web, and worker must be
healthy. Confirm the web binding is still exactly `127.0.0.1:8000->8000`, the
database has no published port, and the three original volume names still
exist. Do not rerun administrator setup.

## 7. Publish HTTPS in a controlled order

1. In Cloudflare DNS, create/update the `A` record for
   `app.dennisbasadre.com` to the HostHatch IPv4 address. Start as **DNS only**
   while Caddy obtains and verifies its public certificate.
2. Open only the web edge and reload the validated configuration:

   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw status numbered
   sudo systemctl reload caddy
   sudo systemctl --no-pager --full status caddy
   sudo journalctl -u caddy --since '10 minutes ago' --no-pager
   ```

3. Verify direct public HTTPS and the redirect:

   ```bash
   curl --fail --silent --show-error \
     https://app.dennisbasadre.com/health
   curl --head http://app.dennisbasadre.com/health
   curl --head https://app.dennisbasadre.com/login
   ```

   HTTP must redirect to HTTPS. HTTPS must present a certificate valid for the
   hostname. Port 8000 must remain unreachable from the internet.
4. In Cloudflare, switch SSL/TLS mode to **Full (strict)**, enable the orange
   proxy for the record, and repeat the HTTPS checks. Never use Flexible mode.

Cloudflare Full (strict) requires an unexpired certificate from a trusted CA
or Cloudflare Origin CA whose hostname matches the request. Caddy's automatic
public certificate satisfies that requirement while retaining the option to
temporarily use DNS-only mode for diagnosis.

## 8. Verify application behavior through the proxy

Use a private browser window against the public HTTPS hostname and verify:

1. An unauthenticated protected page redirects to an `https://` login URL.
2. Login succeeds with the existing administrator; do not create another.
3. The session cookie is `Secure`, `HttpOnly`, and `SameSite=Lax`.
4. Navigation, forms, static assets, and form actions remain HTTPS with no
   mixed-content warnings.
5. A valid form submission succeeds and a deliberately stale/altered CSRF
   token is rejected.
6. English/Japanese selection and light/dark themes still work.
7. An existing record remains present, proving PostgreSQL volume reuse.
8. Generate and download one invoice PDF, then record its safe filename.
9. Confirm `/docs`, `/redoc`, and `/openapi.json` return 404.

The HTTPS URL checks are also the acceptance test for
`ABAP_FORWARDED_ALLOW_IPS`. If generated links or redirect `Location` headers
use `http://`, stop and verify the exact Docker gateway rather than broadening
the trust list.

## 9. Verify persistence and limits

Recreate only the application containers through the same two-file Compose
command; never remove volumes:

```bash
sudo docker compose \
  --env-file /etc/abap/production.env \
  -f compose.deploy.yaml \
  -f compose.hosthatch.yaml \
  up -d --force-recreate --wait web worker
```

Then confirm the existing administrator can still log in, the test record and
PDF remain available, and new activity entries append to the same log. Inspect
limits and inherited Docker log rotation without printing environment values:

```bash
sudo docker inspect abap-deploy-web-1 \
  --format 'memory={{.HostConfig.Memory}} cpu={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}} log={{.HostConfig.LogConfig.Config}}'
sudo docker inspect abap-deploy-worker-1 \
  --format 'memory={{.HostConfig.Memory}} cpu={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}} log={{.HostConfig.LogConfig.Config}}'
sudo docker inspect abap-deploy-database-1 \
  --format 'memory={{.HostConfig.Memory}} cpu={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}} log={{.HostConfig.LogConfig.Config}}'
```

## 10. Rollback rule

If the overlay fails before public cutover, keep the named volumes and return
to the already-working base configuration with an in-place Compose update:

```bash
cd /opt/abap/app
sudo docker compose --env-file /etc/abap/production.env \
  -f compose.deploy.yaml up -d --build --wait
```

This removes the HostHatch resource/proxy overrides from the container
configuration without deleting database, PDF, or activity-log volumes. If a
database migration itself fails, stop and diagnose it; do not reinitialize
PostgreSQL or restore over the live database. Restoration must occur only from
the verified backup, with an explicit recovery plan.

After the HTTPS and isolated restore gates pass, schedule encrypted off-server
PostgreSQL and document-volume backups, disk-usage alerts, container health
alerts, and certificate monitoring. Only then design the separate production
n8n configuration, encryption key, authentication, resource limit, and backup
plan.
