# Deployed ABAP image review — November 4, 2026

Scope: the preserved local archive of production web image
`sha256:bd33abea481b24b9247d5db681f769781f6ecd28c3e32fffd5e654c9d25f9b49`.
Its image configuration digest was verified against the deployed release before
review. The owner explicitly approved Docker Scout's limited package/image
metadata egress. No customer data, credentials, database or private runtime
configuration was uploaded. No production or B2 operation was performed.

## Result and minimum correction

Scout completed successfully and reported 80 advisory rules / 81 matches:
6 critical, 31 high, 16 medium and 27 low. Advisory aliases and vendored metadata
can describe the same issue; these are scanner counts, not a claim of 80
independently exploitable application vulnerabilities.

The local candidate upgrades only already installed dependencies/build tooling:
certifi 2026.10.23, Pillow 13.0.0, dnspython 2.9.2, msgpack 1.2.4,
urllib3 2.8.0, setuptools 84.2.1 and pip 26.3. The source build requirements
also pin these corrections. No ABAP source, template, model, quota, secret,
workflow, migration or production configuration changes are included in the image.

Candidate: `abap:security-20261104-1`, immutable image ID
`sha256:e4b1f0fd69637bbbf8201cc4fc3424629fea989f974d1444a88c7863e3eff78c`.
It is based on the exact existing production image and remains **not deployed**.
Environment, command, entrypoint, user, working directory, exposed ports and
healthcheck match the original image.

The new candidate scan completed: **0 critical, 2 high, 2 medium, 27 low**.
No suppression file or ignored severity was used. The remaining high entries are:

- **CVE-2025-47273 / setuptools 70.3.0:** Scout's only location is
  `pip/_vendor/bom.cdx.json`. The actual installed runtime version is 84.2.1;
  `pip/_vendor/setuptools` and its vulnerable `package_index.py` are absent.
  Record this as an inventory-metadata finding rather than an unpatched installed
  runtime distribution. The [upstream advisory](https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf)
  identifies the vulnerable PackageIndex path and fix at 78.1.1.
- **CVE-2026-85091 / Debian zlib 1.3.1:** the
  [Debian tracker](https://security-tracker.debian.org/tracker/CVE-2026-85091)
  still lists trixie as vulnerable, but describes an affected upstream range
  beginning at 1.3.1.2 and links the discussion of that discrepancy. The installed
  source version is 1.3.1. ABAP has no direct `gzwrite`, `gzprintf` or `gzvprintf`
  call. Keep this finding explicitly disputed/pending distribution resolution;
  do not claim a vendor fix, silently suppress it, or upgrade the whole OS to
  force a clean scanner count. The operator must acknowledge this residual
  finding before production promotion.

The [certifi advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)
requires removing an affected emSign trust root and recommends 2026.10.19 or later.
The [Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
and [TIFF advisory](https://github.com/python-pillow/Pillow/security/advisories/GHSA-332p-7hrc-92wf)
support the image-processing correction. Image-parser exploitability through
ABAP was not demonstrated, and no malicious inputs were sent to production.

## Focused validation

- Candidate build and `pip check` passed.
- Exact corrected dependency versions verified in a disposable container.
- Certificate bundle loaded into a verifying SSL context.
- Synthetic PNG/TIFF/JPEG round trips and thumbnail handling passed.
- Synthetic ReportLab PDF generation with an image passed.
- Application health, readiness and login returned 200 against a disposable
  SQLite database. Network disabled, read-only root filesystem, private tmpfs,
  no production mounts/secrets/provider calls. Disposable container removed.
- Existing application regression, provider and recovery tests were not repeated.

Detailed local scanner output remains under `output/project-completion-20261104/`
and is excluded from Git. The public record contains only sanitized findings.

## Required production approval

The image-only updater is prepared at
`deploy/production/apply-web-security-image-once.py`, staged without execution at
`/tmp/abap-web-security.UKdbSEWq/apply-web-security-image-once.py`.
Updater SHA-256:
`455341d5758ff095d4e97e8ef6c34b49d21357e3aa2d3d4cf3e9e0a80895602a`.
The uploaded archive is 114,463,232 bytes with SHA-256
`7d55f80f021d0e55461c33cb5beab2d157c920cdd7be374ef315a55858bc94aa`.
All uploaded checksums and syntax passed. Three new image-only boundary tests
passed; existing candidate package/startup/PDF/security results were reused.
The local candidate's full image configuration matches the original and its
base layers are preserved. The updater rejects runtime configuration/mount drift,
preserves all prior images and files, and restores the original ordered web
configuration if a deployment check fails. No privileged update has run.

Approve one image-only, web-only security update after the already-approved
recovery operation has finished. Verify the original image and configuration,
load the checksum-verified local candidate, append an image-only Compose overlay
after the existing R2 disabled/activation/validation-renewal overlays, and recreate
only web with `--no-deps --no-build --pull never`. Preserve the old image, all
environment/secrets, synthetic-only flags, free-model allowlist, proof mount,
timers, databases, n8n, workers, RAG and other services. Run one health/readiness/
login check and confirm models remain admitted without forcing AI requests.

On failure, omit the new image overlay and recreate only web from the unchanged
R2 configuration; verify its original image and health. No migrations, credential
rotation, global integration activation, backup or pruning is part of this update.
The unrelated heading fix remains undeployed.
