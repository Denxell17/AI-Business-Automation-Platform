import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = PROJECT_ROOT / "compose.n8n-demo.yaml"
INGRESS_FILE = PROJECT_ROOT / "examples" / "n8n" / "abap-signed-workflow.json"
PROCESSOR_FILE = PROJECT_ROOT / "examples" / "n8n" / "abap-signed-processor.json"
CREDENTIAL_FILE = PROJECT_ROOT / "examples" / "n8n" / "build-demo-credential.mjs"


class TestN8nDemoDeployment(unittest.TestCase):
    def setUp(self):
        self.compose = COMPOSE_FILE.read_text(encoding="utf-8")
        self.ingress = json.loads(INGRESS_FILE.read_text(encoding="utf-8"))
        self.processor = json.loads(PROCESSOR_FILE.read_text(encoding="utf-8"))

    def test_private_profile_pins_n8n_2423_and_publishes_no_ports(self):
        self.assertIn("n8nio/n8n:2.42.3@sha256:", self.compose)
        self.assertIn('profiles: ["n8n-demo"]', self.compose)
        self.assertIn("n8n_demo_data:/home/node/.n8n", self.compose)
        self.assertIn("ABAP_N8N_PRIVATE_DEVELOPMENT_NETWORK: \"true\"", self.compose)
        self.assertNotIn("ports:", self.compose)
        self.assertIn("  demo-provider:", self.compose)
        self.assertIn('N8N_BLOCK_ENV_ACCESS_IN_NODE: "true"', self.compose)
        self.assertIn("n8n publish:workflow --id=abapM3Demo000001", self.compose)
        self.assertIn("n8n publish:workflow --id=abapM3Demo000002", self.compose)
        self.assertIn("abap_n8n_private:", self.compose)
        self.assertIn("internal: true", self.compose)
        self.assertIn("cpus: 0.15", self.compose)
        self.assertIn("mem_limit: 256m", self.compose)
        self.assertIn("pids_limit: 64", self.compose)

    def test_ingress_preserves_raw_body_then_acknowledges_durable_acceptance(self):
        nodes = {node["name"]: node for node in self.ingress["nodes"]}
        preserve = nodes["Preserve raw signed request"]["parameters"]["jsCode"]
        accept = nodes["Authenticate and durably accept"]

        self.assertFalse(self.ingress["active"])
        self.assertEqual(self.ingress["id"], "abapM3Demo000001")
        self.assertTrue(nodes["Receive signed ABAP request"]["parameters"]["options"]["rawBody"])
        self.assertIn("item.binary?.data?.data", preserve)
        self.assertIn("x-abap-event-id", preserve)
        self.assertEqual(accept["parameters"]["url"], "http://demo-provider:8090/accept")
        self.assertEqual(accept["parameters"]["options"]["timeout"], 3000)
        self.assertEqual(accept["parameters"]["authentication"], "genericCredentialType")
        self.assertEqual(accept["parameters"]["genericAuthType"], "httpHeaderAuth")
        self.assertNotIn("$env", accept["parameters"]["jsonHeaders"])
        self.assertIn("Acknowledge durable acceptance", nodes)

    def test_processor_reports_only_scoped_event_outcome_to_private_service(self):
        nodes = {node["name"]: node for node in self.processor["nodes"]}
        action = nodes["Run deterministic synthetic action"]
        outcome = nodes["Report synthetic outcome"]

        self.assertFalse(self.processor["active"])
        self.assertEqual(self.processor["id"], "abapM3Demo000002")
        self.assertEqual(nodes["Claim durable event"]["parameters"]["url"], "http://demo-provider:8090/claim")
        self.assertEqual(nodes["Run deterministic synthetic action"]["parameters"]["url"], "http://demo-provider:8090/demo-action")
        self.assertIn("event_id", action["parameters"]["body"])
        self.assertNotIn("workflow_id", action["parameters"]["body"])
        self.assertEqual(outcome["parameters"]["url"], "http://demo-provider:8090/outcome")
        self.assertIn("result_status", outcome["parameters"]["body"])
        self.assertNotIn("callback", outcome["parameters"]["body"])
        for name in ("Claim durable event", "Run deterministic synthetic action", "Report synthetic outcome"):
            self.assertEqual(nodes[name]["parameters"]["genericAuthType"], "httpHeaderAuth")

    def test_n8n_has_no_callback_signing_authority_or_environment_access(self):
        n8n_section = self.compose.split("  n8n:\n", 1)[1].split("  demo-provider:\n", 1)[0]
        exports = (
            INGRESS_FILE.read_text(encoding="utf-8") + PROCESSOR_FILE.read_text(encoding="utf-8")
        )
        for forbidden in ("ABAP_INBOUND_WEBHOOK_SECRET", "ABAP_OUTBOUND_WEBHOOK_SECRET", "ABAP_CALLBACK_URL"):
            self.assertNotIn(forbidden, n8n_section)
            self.assertNotIn(forbidden, exports)
        self.assertNotIn("X-ABAP-Signature", exports)
        self.assertNotIn("createHmac", exports)
        self.assertNotIn("$env", exports)
        self.assertNotIn("NODE_FUNCTION_ALLOW_BUILTIN", n8n_section)
        self.assertIn("ABAP_INBOUND_WEBHOOK_SECRET", self.compose.split("  demo-provider:\n", 1)[1])
        credential_builder = CREDENTIAL_FILE.read_text(encoding="utf-8")
        self.assertIn("httpHeaderAuth", credential_builder)
        self.assertNotIn("ABAP_INBOUND_WEBHOOK_SECRET", credential_builder)

    def test_provider_token_is_file_mounted_and_never_an_environment_value(self):
        bootstrap_section = self.compose.split("  n8n-credential-bootstrap:\n", 1)[1].split("  n8n:\n", 1)[0]
        n8n_section = self.compose.split("  n8n:\n", 1)[1].split("  demo-provider:\n", 1)[0]
        provider_section = self.compose.split("  demo-provider:\n", 1)[1].split("\nvolumes:", 1)[0]
        credential_builder = CREDENTIAL_FILE.read_text(encoding="utf-8")
        self.assertNotIn("ABAP_N8N_INTERNAL_TOKEN", self.compose)
        self.assertIn("/run/secrets/abap_n8n_provider_token", bootstrap_section)
        self.assertIn("network_mode: none", bootstrap_section)
        self.assertNotIn("abap_n8n_provider_token", n8n_section)
        self.assertIn("- abap_n8n_provider_token", provider_section)
        self.assertIn("readFileSync(tokenFile", credential_builder)
        self.assertNotIn("process.env", credential_builder)
        exports = INGRESS_FILE.read_text(encoding="utf-8") + PROCESSOR_FILE.read_text(encoding="utf-8")
        self.assertNotIn("provider-token", exports)


if __name__ == "__main__":
    unittest.main()
