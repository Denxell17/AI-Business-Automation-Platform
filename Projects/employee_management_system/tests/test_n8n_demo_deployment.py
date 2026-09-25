import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = PROJECT_ROOT / "compose.n8n-demo.yaml"
WORKFLOW_FILE = PROJECT_ROOT / "Notes" / "n8n" / "abap-signed-workflow.json"


class TestN8nDemoDeployment(unittest.TestCase):
    def test_private_profile_has_persistent_n8n_and_no_published_ports(self):
        compose = COMPOSE_FILE.read_text(encoding="utf-8")

        self.assertIn("  n8n:", compose)
        self.assertIn('profiles: ["n8n-demo"]', compose)
        self.assertIn("n8n_demo_data:/home/node/.n8n", compose)
        self.assertIn("ABAP_N8N_PRIVATE_DEVELOPMENT_NETWORK: \"true\"", compose)
        self.assertIn("ABAP_N8N_BASE_URL: http://n8n:5678", compose)
        self.assertNotIn("ports:", compose)
        self.assertIn("  demo-provider:", compose)
        self.assertIn("  webhook-retry-worker:", compose)

    def test_exported_workflow_verifies_then_calls_private_provider_and_callbacks(self):
        workflow = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
        nodes = {node["name"]: node for node in workflow["nodes"]}

        verify = nodes["Verify signed ABAP request"]["parameters"]["jsCode"]
        callback = nodes["Build signed ABAP callback"]["parameters"]["jsCode"]
        self.assertTrue(workflow["active"])
        self.assertEqual(workflow["id"], "abapM3Demo000001")
        self.assertEqual(
            nodes["Receive signed ABAP request"]["webhookId"],
            "abap-m3-workflow-hook",
        )
        self.assertIn("timingSafeEqual", verify)
        self.assertIn("ABAP_OUTBOUND_WEBHOOK_SECRET", verify)
        self.assertEqual(
            nodes["Run deterministic demo action"]["parameters"]["url"],
            "http://demo-provider:8090/demo-action",
        )
        self.assertEqual(
            nodes["Run deterministic demo action"]["parameters"]["contentType"],
            "raw",
        )
        self.assertIn("ABAP_INBOUND_WEBHOOK_SECRET", callback)
        self.assertEqual(
            nodes["Send signed ABAP callback"]["parameters"]["url"],
            "={{ $env.ABAP_CALLBACK_URL }}",
        )


if __name__ == "__main__":
    unittest.main()
