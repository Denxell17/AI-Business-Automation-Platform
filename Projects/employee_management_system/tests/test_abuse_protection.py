import unittest

from abuse_protection import ProviderAbuseProtection, WebhookCircuitBreaker


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestWebhookCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()

    def test_source_limit_and_window_expiration(self):
        limiter = WebhookCircuitBreaker(
            source_limit=2,
            process_limit=10,
            window_seconds=10,
            max_sources=4,
            clock=self.clock,
        )

        self.assertTrue(limiter.check("192.0.2.1").allowed)
        self.assertTrue(limiter.check("192.0.2.1").allowed)
        rejected = limiter.check("192.0.2.1")
        self.assertFalse(rejected.allowed)
        self.assertEqual(rejected.retry_after, 10)

        self.clock.advance(10)
        self.assertTrue(limiter.check("192.0.2.1").allowed)

    def test_process_limit_stops_rotating_sources(self):
        limiter = WebhookCircuitBreaker(
            source_limit=5,
            process_limit=2,
            window_seconds=60,
            max_sources=10,
            clock=self.clock,
        )

        self.assertTrue(limiter.check("192.0.2.1").allowed)
        self.assertTrue(limiter.check("192.0.2.2").allowed)
        rejected = limiter.check("192.0.2.3")
        self.assertFalse(rejected.allowed)
        self.assertEqual(rejected.retry_after, 60)

    def test_source_state_is_bounded(self):
        limiter = WebhookCircuitBreaker(
            source_limit=2,
            process_limit=20,
            max_sources=2,
            clock=self.clock,
        )

        for address in ("192.0.2.1", "192.0.2.2", "192.0.2.3"):
            self.assertTrue(limiter.check(address).allowed)

        self.assertEqual(limiter.tracked_source_count, 2)


class TestProviderAbuseProtection(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()

    def limiter(self, **overrides):
        return ProviderAbuseProtection(
            "test-limiter-key-secret",
            user_limit=overrides.get("user_limit", 2),
            window_seconds=overrides.get("window_seconds", 10),
            concurrency_limit=overrides.get("concurrency_limit", 2),
            max_users=overrides.get("max_users", 4),
            clock=self.clock,
        )

    def test_per_user_limit_is_shared_and_separate_users_are_independent(self):
        limiter = self.limiter(user_limit=1)

        first = limiter.acquire("USR-ONE")
        self.assertTrue(first.allowed)
        limiter.release()

        same_user_other_operation = limiter.acquire("USR-ONE")
        self.assertFalse(same_user_other_operation.allowed)
        self.assertEqual(same_user_other_operation.retry_after, 10)

        second_user = limiter.acquire("USR-TWO")
        self.assertTrue(second_user.allowed)
        limiter.release()

        self.clock.advance(10)
        self.assertTrue(limiter.acquire("USR-ONE").allowed)
        limiter.release()

    def test_global_concurrency_and_release_after_success_or_exception(self):
        limiter = self.limiter(concurrency_limit=1)

        self.assertTrue(limiter.acquire("USR-ONE").allowed)
        rejected = limiter.acquire("USR-TWO")
        self.assertFalse(rejected.allowed)
        self.assertEqual(rejected.retry_after, 1)
        self.assertEqual(limiter.active_request_count, 1)

        try:
            raise RuntimeError("provider failed")
        except RuntimeError:
            pass
        finally:
            limiter.release()

        self.assertEqual(limiter.active_request_count, 0)
        self.assertTrue(limiter.acquire("USR-TWO").allowed)
        limiter.release()
        self.assertEqual(limiter.active_request_count, 0)

    def test_user_keys_are_non_reversible_and_state_is_bounded(self):
        limiter = self.limiter(max_users=2)
        self.assertNotIn("USR-PRIVATE", limiter.user_key("USR-PRIVATE"))

        for user_id in ("USR-ONE", "USR-TWO", "USR-THREE"):
            self.assertTrue(limiter.acquire(user_id).allowed)
            limiter.release()

        self.assertEqual(limiter.tracked_user_count, 2)


if __name__ == "__main__":
    unittest.main()
