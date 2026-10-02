"""Polite GET: timeout, per-source throttle, retries with backoff. Returns RawResponse.

Request headers (including Authorization) are never stored: RawResponse has no headers.
"""

import random
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, Protocol

import requests

from nfa import clock
from nfa.domain.raw import FetchRequest, RawResponse

RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504, 999})
AUTH_STATUSES = frozenset({401, 403})


class FetchError(Exception):
    def __init__(self, message: str, response: RawResponse | None = None) -> None:
        super().__init__(message)
        self.response = response


class AuthError(FetchError):
    pass


class HttpSession(Protocol):
    def get(
        self,
        url: str,
        *,
        params: Mapping[str, str] | None,
        headers: Mapping[str, str] | None,
        timeout: float,
    ) -> Any: ...


class Throttle:
    """Keeps a minimum interval between calls to the same source."""

    def __init__(
        self,
        intervals_s: Mapping[str, float],
        *,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        default_s: float = 1.0,
    ) -> None:
        self._intervals = dict(intervals_s)
        self._sleep = sleep
        self._monotonic = monotonic
        self._default_s = default_s
        self._last: dict[str, float] = {}

    def wait(self, source: str) -> None:
        last = self._last.get(source)
        if last is not None:
            remaining = self._intervals.get(source, self._default_s) - (self._monotonic() - last)
            if remaining > 0:
                self._sleep(remaining)
        self._last[source] = self._monotonic()


def get(
    request: FetchRequest,
    url: str,
    *,
    session: HttpSession,
    throttle: Throttle,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_s: float = 20.0,
    max_retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = clock.now,
    jitter: Callable[[], float] = random.random,
    rate_limit_backoff_s: float = 30.0,
) -> RawResponse:
    """Retries 5xx/429/999 and network errors. Yahoo's 999 is a rate-limit block that lasts
    minutes, so it backs off from `rate_limit_backoff_s` instead of 1 second."""
    label = f"{request.source}/{request.dataset} {request.key}"
    attempt = 0
    while True:
        base_s = 1.0
        throttle.wait(request.source)
        try:
            response = session.get(url, params=params, headers=headers, timeout=timeout_s)
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt >= max_retries:
                raise FetchError(
                    f"{label}: {type(exc).__name__} after {attempt + 1} attempts"
                ) from exc
        else:
            raw = RawResponse(
                request=request,
                fetched_at=now(),
                status=response.status_code,
                payload=response.content,
            )
            if response.status_code in AUTH_STATUSES:
                raise AuthError(f"{label}: credentials rejected (HTTP {response.status_code})", raw)
            if response.status_code not in RETRYABLE_STATUSES:
                return raw
            if response.status_code == 999:
                base_s = rate_limit_backoff_s
            if attempt >= max_retries:
                raise FetchError(
                    f"{label}: HTTP {response.status_code} after {attempt + 1} attempts", raw
                )
        sleep(base_s * 2**attempt + jitter())
        attempt += 1
