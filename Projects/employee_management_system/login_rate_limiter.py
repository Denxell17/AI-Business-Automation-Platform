"""Bounded process-local login failure limiting.

The limiter intentionally has no infrastructure dependency for ABAP's current
single-process deployment. It must be replaced or backed by shared state before
multiple web application instances are used.
"""

import hashlib
import hmac
import math
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field


SOURCE_FAILURE_LIMIT = 10
SOURCE_WINDOW_SECONDS = 5 * 60
ACCOUNT_FAILURE_LIMIT = 50
ACCOUNT_WINDOW_SECONDS = 15 * 60
COOLDOWN_SECONDS = 60
MAXIMUM_TRACKED_IDENTITIES = 10_000


@dataclass
class _FailureState:
    attempts: deque[float] = field(default_factory=deque)
    blocked_until: float = 0.0


class LoginRateLimiter:
    """Track failed logins by source and normalized account identifier."""

    def __init__(
        self,
        secret: str,
        clock: Callable[[], float] = time.monotonic,
        source_failure_limit: int = SOURCE_FAILURE_LIMIT,
        source_window_seconds: int = SOURCE_WINDOW_SECONDS,
        account_failure_limit: int = ACCOUNT_FAILURE_LIMIT,
        account_window_seconds: int = ACCOUNT_WINDOW_SECONDS,
        cooldown_seconds: int = COOLDOWN_SECONDS,
        maximum_tracked_identities: int = MAXIMUM_TRACKED_IDENTITIES,
    ) -> None:
        if not secret:
            raise ValueError("Login limiter secret is required.")
        numeric_values = (
            source_failure_limit,
            source_window_seconds,
            account_failure_limit,
            account_window_seconds,
            cooldown_seconds,
            maximum_tracked_identities,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
               for value in numeric_values):
            raise ValueError("Login limiter settings must be positive integers.")
        self._secret = secret.encode("utf-8")
        self._clock = clock
        self._source_failure_limit = source_failure_limit
        self._source_window_seconds = source_window_seconds
        self._account_failure_limit = account_failure_limit
        self._account_window_seconds = account_window_seconds
        self._cooldown_seconds = cooldown_seconds
        self._maximum_tracked_identities = maximum_tracked_identities
        self._states: OrderedDict[str, _FailureState] = OrderedDict()

    def _key(self, namespace: str, value: str) -> str:
        normalized = value.strip().casefold()
        return hmac.new(
            self._secret,
            f"{namespace}\0{normalized}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _trim(self, state: _FailureState, window: int, now: float) -> None:
        cutoff = now - window
        while state.attempts and state.attempts[0] <= cutoff:
            state.attempts.popleft()

    def _state(self, key: str) -> _FailureState:
        state = self._states.get(key)
        if state is None:
            state = _FailureState()
            self._states[key] = state
        else:
            self._states.move_to_end(key)
        while len(self._states) > self._maximum_tracked_identities:
            self._states.popitem(last=False)
        return state

    def _retry_after(self, key: str, window: int, now: float) -> int:
        state = self._states.get(key)
        if state is None:
            return 0
        self._trim(state, window, now)
        if not state.attempts and state.blocked_until <= now:
            del self._states[key]
            return 0
        self._states.move_to_end(key)
        return max(0, math.ceil(state.blocked_until - now))

    def retry_after(self, source: str, username: str) -> int:
        now = self._clock()
        return max(
            self._retry_after(self._key("source", source), self._source_window_seconds, now),
            self._retry_after(self._key("account", username), self._account_window_seconds, now),
        )

    def record_failure(self, source: str, username: str) -> int:
        now = self._clock()
        pairs = (
            (self._key("source", source), self._source_window_seconds,
             self._source_failure_limit),
            (self._key("account", username), self._account_window_seconds,
             self._account_failure_limit),
        )
        retry_after = 0
        for key, window, limit in pairs:
            state = self._state(key)
            self._trim(state, window, now)
            state.attempts.append(now)
            if len(state.attempts) >= limit:
                state.blocked_until = max(
                    state.blocked_until,
                    now + self._cooldown_seconds,
                )
            retry_after = max(
                retry_after,
                max(0, math.ceil(state.blocked_until - now)),
            )
        return retry_after

    def record_success(self, username: str) -> None:
        self._states.pop(self._key("account", username), None)
