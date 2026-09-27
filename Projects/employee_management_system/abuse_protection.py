"""Bounded process-local circuit breakers for public and provider work."""

from __future__ import annotations

import hashlib
import math
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass


WEBHOOK_SOURCE_REQUESTS_PER_WINDOW = 60
WEBHOOK_PROCESS_REQUESTS_PER_WINDOW = 300
WEBHOOK_WINDOW_SECONDS = 60
WEBHOOK_MAX_TRACKED_SOURCES = 1024

AI_USER_REQUESTS_PER_WINDOW = 10
AI_USER_WINDOW_SECONDS = 60
AI_PROCESS_CONCURRENCY = 4
AI_MAX_TRACKED_USERS = 1024


def _retry_after(oldest: float, now: float, window_seconds: int) -> int:
    return max(1, math.ceil(oldest + window_seconds - now))


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    retry_after: int = 0


class WebhookCircuitBreaker:
    """Bound callback work by visible peer and across the whole process."""

    def __init__(
        self,
        *,
        source_limit: int = WEBHOOK_SOURCE_REQUESTS_PER_WINDOW,
        process_limit: int = WEBHOOK_PROCESS_REQUESTS_PER_WINDOW,
        window_seconds: int = WEBHOOK_WINDOW_SECONDS,
        max_sources: int = WEBHOOK_MAX_TRACKED_SOURCES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if min(source_limit, process_limit, window_seconds, max_sources) < 1:
            raise ValueError("Webhook circuit-breaker limits must be positive.")
        self.source_limit = source_limit
        self.process_limit = process_limit
        self.window_seconds = window_seconds
        self.max_sources = max_sources
        self._clock = clock
        self._process_requests: deque[float] = deque()
        self._source_requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def tracked_source_count(self) -> int:
        with self._lock:
            return len(self._source_requests)

    def check(self, peer: str) -> LimitDecision:
        """Record an allowed request or return a generic retry interval."""
        now = self._clock()
        cutoff = now - self.window_seconds
        peer_key = hashlib.sha256(peer.encode("utf-8", "replace")).hexdigest()
        with self._lock:
            while self._process_requests and self._process_requests[0] <= cutoff:
                self._process_requests.popleft()
            if len(self._process_requests) >= self.process_limit:
                return LimitDecision(
                    False,
                    _retry_after(
                        self._process_requests[0], now, self.window_seconds
                    ),
                )

            source_requests = self._source_requests.get(peer_key)
            if source_requests is not None:
                while source_requests and source_requests[0] <= cutoff:
                    source_requests.popleft()
                if len(source_requests) >= self.source_limit:
                    self._source_requests.move_to_end(peer_key)
                    return LimitDecision(
                        False,
                        _retry_after(
                            source_requests[0], now, self.window_seconds
                        ),
                    )
            else:
                self._discard_expired_sources(cutoff)
                while len(self._source_requests) >= self.max_sources:
                    self._source_requests.popitem(last=False)
                source_requests = deque()
                self._source_requests[peer_key] = source_requests

            source_requests.append(now)
            self._source_requests.move_to_end(peer_key)
            self._process_requests.append(now)
            return LimitDecision(True)

    def _discard_expired_sources(self, cutoff: float) -> None:
        for key, requests in tuple(self._source_requests.items()):
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if not requests:
                del self._source_requests[key]


class ProviderAbuseProtection:
    """Share per-user rate and process concurrency limits across AI routes."""

    def __init__(
        self,
        key_secret: str,
        *,
        user_limit: int = AI_USER_REQUESTS_PER_WINDOW,
        window_seconds: int = AI_USER_WINDOW_SECONDS,
        concurrency_limit: int = AI_PROCESS_CONCURRENCY,
        max_users: int = AI_MAX_TRACKED_USERS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not key_secret or min(
            user_limit, window_seconds, concurrency_limit, max_users
        ) < 1:
            raise ValueError("Provider abuse-protection settings are invalid.")
        self.user_limit = user_limit
        self.window_seconds = window_seconds
        self.concurrency_limit = concurrency_limit
        self.max_users = max_users
        self._key_secret = hashlib.sha256(key_secret.encode("utf-8")).digest()
        self._clock = clock
        self._user_requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._active_requests = 0
        self._lock = threading.Lock()

    @property
    def tracked_user_count(self) -> int:
        with self._lock:
            return len(self._user_requests)

    @property
    def active_request_count(self) -> int:
        with self._lock:
            return self._active_requests

    def user_key(self, user_id: int | str) -> str:
        """Return a keyed, non-reversible identifier for limiter state."""
        stable_user_id = str(user_id)
        return hashlib.blake2b(
            stable_user_id.encode("utf-8", "strict"),
            key=self._key_secret,
            digest_size=16,
            person=b"abap-ai-limit",
        ).hexdigest()

    def acquire(self, user_id: int | str) -> LimitDecision:
        now = self._clock()
        cutoff = now - self.window_seconds
        key = self.user_key(user_id)
        with self._lock:
            requests = self._user_requests.get(key)
            if requests is not None:
                while requests and requests[0] <= cutoff:
                    requests.popleft()
                if len(requests) >= self.user_limit:
                    self._user_requests.move_to_end(key)
                    return LimitDecision(
                        False,
                        _retry_after(requests[0], now, self.window_seconds),
                    )

            if self._active_requests >= self.concurrency_limit:
                return LimitDecision(False, 1)

            if requests is None:
                self._discard_expired_users(cutoff)
                while len(self._user_requests) >= self.max_users:
                    self._user_requests.popitem(last=False)
                requests = deque()
                self._user_requests[key] = requests

            requests.append(now)
            self._user_requests.move_to_end(key)
            self._active_requests += 1
            return LimitDecision(True)

    def release(self) -> None:
        with self._lock:
            if self._active_requests < 1:
                raise RuntimeError("Provider limiter release was not acquired.")
            self._active_requests -= 1

    def _discard_expired_users(self, cutoff: float) -> None:
        for key, requests in tuple(self._user_requests.items()):
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if not requests:
                del self._user_requests[key]
