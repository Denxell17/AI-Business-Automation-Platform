import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = PROJECT_ROOT / "compose.deploy.yaml"


class TestWorkerDeployment(unittest.TestCase):
    def test_worker_starts_after_migrations_with_private_database_access(self):
        compose = COMPOSE_FILE.read_text(encoding="utf-8")

        self.assertIn("  worker:", compose)
        self.assertIn('command: ["python", "-m", "workflow_worker"]', compose)
        self.assertIn("ABAP_WORKER_ENABLED: \"true\"", compose)
        self.assertIn("condition: service_completed_successfully", compose)
        self.assertIn('"workflow_worker", "--check"', compose)


if __name__ == "__main__":
    unittest.main()
