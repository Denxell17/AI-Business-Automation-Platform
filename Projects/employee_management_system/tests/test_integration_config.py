import unittest

from integration_config import load_integration_settings


VALID = {
    "ABAP_INTEGRATIONS_ENABLED": "true",
    "ABAP_N8N_BASE_URL": "https://automation.example.test",
    "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
    "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
    "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-test-secret-1234567890",
    "ABAP_INBOUND_WEBHOOK_SECRET": "inbound-test-secret-1234567890",
}


class TestIntegrationConfig(unittest.TestCase):
    def test_disabled_by_default_without_secrets_or_destination(self):
        settings = load_integration_settings({})
        self.assertFalse(settings["enabled"])
        self.assertIsNone(settings["base_url"])
        self.assertIsNone(settings["outbound_secret"])

    def test_valid_enabled_settings_use_separate_secrets_and_bounded_defaults(self):
        settings = load_integration_settings(VALID)
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["base_url"], VALID["ABAP_N8N_BASE_URL"])
        self.assertEqual(settings["allowed_hosts"], ("automation.example.test",))
        self.assertNotEqual(settings["outbound_secret"], settings["inbound_secret"])
        self.assertEqual(settings["connect_timeout_seconds"], 3)
        self.assertEqual(settings["max_request_bytes"], 262144)

    def test_enabled_flag_is_strict(self):
        with self.assertRaisesRegex(ValueError, "ABAP_INTEGRATIONS_ENABLED"):
            load_integration_settings({"ABAP_INTEGRATIONS_ENABLED": "yes"})

    def test_unknown_runtime_environment_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ABAP_ENVIRONMENT"):
            load_integration_settings({"ABAP_ENVIRONMENT": "prod-ish"})

    def test_required_enabled_fields_are_rejected_when_missing(self):
        for name in (
            "ABAP_N8N_BASE_URL", "ABAP_N8N_WORKFLOW_PATH",
            "ABAP_INTEGRATION_ALLOWED_HOSTS", "ABAP_OUTBOUND_WEBHOOK_SECRET",
            "ABAP_INBOUND_WEBHOOK_SECRET",
        ):
            with self.subTest(name=name):
                config = dict(VALID)
                config[name] = " "
                with self.assertRaises(ValueError):
                    load_integration_settings(config)

    def test_same_secret_is_rejected_without_echoing_secret(self):
        config = dict(VALID)
        config["ABAP_INBOUND_WEBHOOK_SECRET"] = config["ABAP_OUTBOUND_WEBHOOK_SECRET"]
        with self.assertRaises(ValueError) as captured:
            load_integration_settings(config)
        self.assertNotIn(config["ABAP_OUTBOUND_WEBHOOK_SECRET"], str(captured.exception))

    def test_unsafe_urls_are_rejected(self):
        for url in (
            "http://automation.example.test",
            "https://localhost",
            "https://127.0.0.1",
            "https://10.0.0.1",
            "https://[::1]",
            "https://user:password@automation.example.test",
            "https://automation.example.test.evil.test",
            "https://automation.example.test/path",
            "https://automation.example.test?token=private",
            "https://automation.example.test#fragment",
            "https://automation.example.test:0",
            "https://automation.example.test\\@evil.test",
        ):
            with self.subTest(url=url):
                config = dict(VALID)
                config["ABAP_N8N_BASE_URL"] = url
                with self.assertRaises(ValueError):
                    load_integration_settings(config)

    def test_unsafe_allowlist_entries_are_rejected(self):
        for host in ("*", "localhost", "n8n", "127.0.0.1", "10.1.2.3", "x.local", ""):
            with self.subTest(host=host):
                config = dict(VALID)
                config["ABAP_INTEGRATION_ALLOWED_HOSTS"] = host
                with self.assertRaises(ValueError):
                    load_integration_settings(config)

    def test_workflow_path_cannot_contain_query_credentials_or_control_characters(self):
        for path in ("webhook/v1", "//evil.test/hook", "/hook?token=private", "/hook#x", "/hook\nX: y"):
            with self.subTest(path=path):
                config = dict(VALID)
                config["ABAP_N8N_WORKFLOW_PATH"] = path
                with self.assertRaises(ValueError):
                    load_integration_settings(config)

    def test_numeric_limits_reject_invalid_values_even_while_disabled(self):
        maximums = {
            "ABAP_WEBHOOK_CONNECT_TIMEOUT_SECONDS": 30,
            "ABAP_WEBHOOK_READ_TIMEOUT_SECONDS": 120,
            "ABAP_WEBHOOK_MAX_REQUEST_BYTES": 1048576,
            "ABAP_WEBHOOK_MAX_RESPONSE_BYTES": 1048576,
            "ABAP_WEBHOOK_SIGNATURE_TTL_SECONDS": 900,
            "ABAP_WEBHOOK_MAX_ATTEMPTS": 10,
        }
        for name, maximum in maximums.items():
            for value in ("0", "-1", "slow", str(maximum + 1)):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        load_integration_settings({name: value})


if __name__ == "__main__":
    unittest.main()
