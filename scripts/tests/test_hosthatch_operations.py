import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HOSTHATCH = REPOSITORY_ROOT / "deploy" / "hosthatch"
SYSTEMD = HOSTHATCH / "systemd"
RUNBOOK = (
    REPOSITORY_ROOT
    / "docs"
    / "deployment"
    / "hosthatch-backup-restore-monitoring-runbook.md"
)


class TestHostHatchOperationsArtifacts(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_backup_uses_native_dump_and_confirms_restic_snapshot(self):
        script = self.read(HOSTHATCH / "abap-backup.sh")

        self.assertIn("pg_dump", script)
        self.assertIn("--format=custom", script)
        self.assertIn("pg_restore --list", script)
        self.assertIn("restic snapshots", script)
        self.assertLess(
            script.index("pg_restore --list"),
            script.index("restic backup"),
        )
        self.assertLess(
            script.index("restic backup"),
            script.index("snapshot_confirmed=true"),
        )

    def test_local_capacity_gate_prevents_pg_dump_from_starting(self):
        script = self.read(HOSTHATCH / "abap-backup.sh")
        library = self.read(HOSTHATCH / "abap-operations-lib.sh")
        config = self.read(HOSTHATCH / "abap-operations.conf.example")

        capacity_gate = script.index(
            'permitted_staging_bytes="$(operations_permitted_staging_bytes'
        )
        self.assertLess(capacity_gate, script.index("pg_dump -U"))
        self.assertIn(
            "PostgreSQL dump was not started because local backup capacity is unsafe.",
            script,
        )
        self.assertIn("operations_require_local_headroom", script)
        self.assertIn("used_percent >= ABAP_DISK_CRITICAL_PERCENT", library)
        self.assertIn("ABAP_LOCAL_FREE_RESERVE_BYTES=3000000000", config)
        self.assertIn("ABAP_RESTIC_CACHE_OVERHEAD_BYTES=500000000", config)

    def test_restic_sources_are_explicit_and_exclude_database_volume(self):
        script = self.read(HOSTHATCH / "abap-backup.sh")
        backup_call = re.search(
            r"restic backup \\\n(?P<body>.*?)\n\nsnapshot_listing=",
            script,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(backup_call)
        body = backup_call.group("body")

        self.assertIn('"$STAGING_DIRECTORY"', body)
        self.assertIn('"$ABAP_INVOICE_DOCUMENTS_DIR"', body)
        self.assertNotIn('"$ABAP_ACTIVITY_LOGS_DIR"', body)
        self.assertNotIn('"$ABAP_DATABASE_DATA_DIR"', body)
        self.assertNotIn("/var/lib/docker ", body)
        self.assertNotIn(" / ", body)

    def test_free_tier_thresholds_and_no_threshold_deletion(self):
        config = self.read(HOSTHATCH / "abap-operations.conf.example")
        backup = self.read(HOSTHATCH / "abap-backup.sh")
        maintenance = self.read(HOSTHATCH / "abap-backup-maintenance.sh")

        self.assertIn("ABAP_RESTIC_WARNING_BYTES=7000000000", config)
        self.assertIn("ABAP_RESTIC_CRITICAL_BYTES=8500000000", config)
        self.assertIn("ABAP_RESTIC_FREE_TIER_BYTES=10000000000", config)
        self.assertIn("projected_raw_bytes", backup)
        self.assertNotIn("forget", backup)
        self.assertIn("--keep-daily 14", maintenance)
        self.assertIn("--keep-weekly 8", maintenance)
        self.assertIn("--keep-monthly 12", maintenance)
        self.assertIn("--keep-tag release", maintenance)
        self.assertIn("retention-dry-run", maintenance)
        self.assertIn("--dry-run", maintenance)

    def test_systemd_schedules_and_credentials(self):
        expected_schedules = {
            "abap-backup.timer": "OnCalendar=*-*-* 02:15:00 UTC",
            "abap-backup-maintenance.timer": (
                "OnCalendar=Sun *-*-* 03:30:00 UTC"
            ),
            "abap-backup-full-check.timer": (
                "OnCalendar=*-*-01 04:30:00 UTC"
            ),
            "abap-operations-check.timer": "OnUnitActiveSec=5min",
        }
        for filename, schedule in expected_schedules.items():
            with self.subTest(filename=filename):
                self.assertIn(schedule, self.read(SYSTEMD / filename))

        for service in SYSTEMD.glob("*.service"):
            text = self.read(service)
            self.assertIn("LoadCredential=", text)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY=", text)
            self.assertNotIn("RESTIC_PASSWORD=", text)
            self.assertNotRegex(text, r"https://[^/\s]+/api/v1/heartbeat/[A-Za-z0-9]")

    def test_tls_cleanup_and_trusted_file_hardening(self):
        backup = self.read(HOSTHATCH / "abap-backup.sh")
        operations = self.read(HOSTHATCH / "abap-operations-check.sh")
        library = self.read(HOSTHATCH / "abap-operations-lib.sh")

        self.assertIn('-verify_hostname "$ABAP_TLS_HOST"', operations)
        self.assertIn("findmnt -N 1 -rn -o TARGET", backup)
        self.assertIn("readlink -f --", backup)
        self.assertIn("must be owned by root", backup)
        self.assertIn("must not be group- or world-accessible", backup)
        self.assertIn("operations_require_trusted_root_file", library)
        self.assertIn('[[ -f "$file_path" && ! -L "$file_path" ]]', library)
        self.assertIn("Credential $1 must be owned by root", library)

    def test_operations_thresholds_and_required_checks_are_documented(self):
        config = self.read(HOSTHATCH / "abap-operations.conf.example")
        operations = self.read(HOSTHATCH / "abap-operations-check.sh")
        runbook = self.read(RUNBOOK)

        for setting in (
            "ABAP_DISK_WARNING_PERCENT=75",
            "ABAP_DISK_CRITICAL_PERCENT=85",
            "ABAP_TLS_WARNING_DAYS=21",
            "ABAP_TLS_CRITICAL_DAYS=7",
        ):
            self.assertIn(setting, config)

        for required_text in (
            "df -Pi",
            "free -b",
            "systemctl is-active",
            "docker inspect",
            "http://127.0.0.1:8000/health",
            "http://127.0.0.1:8000/ready",
            "port 5432",
            "port 8000",
            "openssl s_client",
        ):
            self.assertIn(required_text, operations)

        self.assertIn("not authoritative billing evidence", runbook)
        self.assertIn("stored_gb", runbook)

    def test_no_destructive_production_compose_command(self):
        artifact_paths = [
            *HOSTHATCH.glob("abap-*.sh"),
            *SYSTEMD.glob("abap-*"),
        ]
        for path in artifact_paths:
            with self.subTest(path=path.name):
                text = self.read(path)
                self.assertNotRegex(text, r"docker compose[^\n]*down\s+-v")
                self.assertNotIn("volume rm abap-deploy", text)

        runbook = self.read(RUNBOOK)
        self.assertIn("Never run `docker\ncompose down -v`", runbook)
        self.assertNotIn("sudo docker compose down -v", runbook)


if __name__ == "__main__":
    unittest.main()
