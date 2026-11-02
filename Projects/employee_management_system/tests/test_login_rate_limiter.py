import math
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

    def test_fractional_clock_cooldown_never_exceeds_configured_duration(self):
        for source_limit, account_limit in ((2, 50), (50, 2)):
            with self.subTest(source_limit=source_limit, account_limit=account_limit):
                self.clock.value = 4.0002
                limiter = LoginRateLimiter(
                    "fractional-clock-test-secret",
                    clock=self.clock,
                    source_failure_limit=source_limit,
                    account_failure_limit=account_limit,
                    cooldown_seconds=60,
                )
                self.assertEqual(limiter.record_failure("source", "alice"), 0)
                self.assertEqual(limiter.record_failure("source", "alice"), 60)
                self.assertEqual(limiter.retry_after("source", "alice"), 60)
                self.clock.advance(0.25)
                self.assertEqual(limiter.retry_after("source", "alice"), 60)
                self.clock.advance(1.0)
                self.assertEqual(limiter.retry_after("source", "alice"), 59)

    def test_fractional_clock_enforces_deadline_through_last_instant(self):
        self.clock.value = 4.0002
        deadline = self.clock.value + 60
        limiter = LoginRateLimiter(
            "deadline-test-secret", clock=self.clock,
            source_failure_limit=1, cooldown_seconds=60,
        )
        limiter.record_failure("source", "alice")
        self.clock.value = math.nextafter(deadline, -math.inf)
        self.assertEqual(limiter.retry_after("source", "alice"), 1)
        self.clock.value = deadline
        self.assertEqual(limiter.retry_after("source", "alice"), 0)
        self.clock.value = math.nextafter(deadline, math.inf)
        self.assertEqual(limiter.retry_after("source", "alice"), 0)

    def test_tracking_state_is_bounded(self):
        for index in range(30):
            self.limiter.record_failure(f"10.0.0.{index}", f"user-{index}")
        self.assertLessEqual(len(self.limiter._states), 20)


if __name__ == "__main__":
    unittest.main()
