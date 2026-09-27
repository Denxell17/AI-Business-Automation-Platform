import unittest

from login_rate_limiter import LoginRateLimiter


class _Clock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class TestLoginRateLimiter(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = _Clock()
        self.limiter = LoginRateLimiter(
            "test-secret",
            clock=self.clock,
            source_failure_limit=3,
            source_window_seconds=60,
            account_failure_limit=4,
            account_window_seconds=120,
            cooldown_seconds=30,
            maximum_tracked_identities=20,
        )

    def test_repeated_failures_from_one_source_are_limited(self):
        self.assertEqual(self.limiter.record_failure("10.0.0.1", "alice"), 0)
        self.assertEqual(self.limiter.record_failure("10.0.0.1", "bob"), 0)
        self.assertEqual(self.limiter.record_failure("10.0.0.1", "carol"), 30)
        self.assertEqual(self.limiter.retry_after("10.0.0.1", "other"), 30)

    def test_distributed_failures_against_one_account_are_limited(self):
        for source in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
            self.assertEqual(self.limiter.record_failure(source, "alice"), 0)
        self.assertEqual(self.limiter.record_failure("10.0.0.4", "ALICE"), 30)
        self.assertEqual(self.limiter.retry_after("10.0.0.5", " alice "), 30)

    def test_success_clears_only_the_account_failure_state(self):
        self.limiter.record_failure("10.0.0.1", "alice")
        self.limiter.record_failure("10.0.0.1", "bob")
        self.limiter.record_failure("10.0.0.1", "carol")
        self.limiter.record_success("Alice")

        self.assertEqual(self.limiter.retry_after("10.0.0.2", "alice"), 0)
        self.assertEqual(self.limiter.retry_after("10.0.0.1", "alice"), 30)

    def test_cooldown_expires(self):
        for _ in range(3):
            self.limiter.record_failure("10.0.0.1", "alice")
        self.clock.advance(31)
        self.assertEqual(self.limiter.retry_after("10.0.0.1", "alice"), 0)

    def test_tracking_state_is_bounded(self):
        for index in range(30):
            self.limiter.record_failure(f"10.0.0.{index}", f"user-{index}")
        self.assertLessEqual(len(self.limiter._states), 20)


if __name__ == "__main__":
    unittest.main()
