from datetime import UTC, datetime

import pytest
import requests

from nfa.adapters import http
from nfa.adapters.http import AuthError, FetchError, Throttle
from nfa.domain.raw import FetchRequest
from tests.fakes import FakeResponse, FakeSession, no_wait_throttle

REQ = FetchRequest(source="yahoo", dataset="league_settings", key="466.l.1")
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


def call(session: FakeSession, sleeps: list[float] | None = None, **kwargs):
    recorded = sleeps if sleeps is not None else []
    return http.get(
        REQ,
        "https://example.test/x",
        session=session,
        throttle=no_wait_throttle(),
        sleep=recorded.append,
        now=lambda: NOW,
        jitter=lambda: 0.0,
        **kwargs,
    )


def test_returns_raw_response_on_200() -> None:
    raw = call(FakeSession([FakeResponse(200, b'{"a":1}')]))
    assert (raw.status, raw.payload, raw.fetched_at, raw.request) == (200, b'{"a":1}', NOW, REQ)


def test_timeout_always_passed() -> None:
    session = FakeSession([FakeResponse(200)])
    call(session)
    assert session.calls[0]["timeout"] == 20.0


@pytest.mark.parametrize("status", [500, 503, 429])
def test_retries_retryable_status_then_succeeds(status: int) -> None:
    session = FakeSession([FakeResponse(status), FakeResponse(200)])
    sleeps: list[float] = []
    raw = call(session, sleeps)
    assert raw.status == 200
    assert len(session.calls) == 2
    assert sleeps == [1.0]


def test_backoff_doubles() -> None:
    session = FakeSession([FakeResponse(503)] * 3 + [FakeResponse(200)])
    sleeps: list[float] = []
    call(session, sleeps)
    assert sleeps == [1.0, 2.0, 4.0]


def test_gives_up_after_three_retries_with_last_response() -> None:
    session = FakeSession([FakeResponse(503)] * 4)
    with pytest.raises(FetchError) as excinfo:
        call(session)
    assert len(session.calls) == 4
    assert excinfo.value.response is not None and excinfo.value.response.status == 503


@pytest.mark.parametrize("status", [401, 403])
def test_auth_errors_are_not_retried(status: int) -> None:
    session = FakeSession([FakeResponse(status)])
    with pytest.raises(AuthError) as excinfo:
        call(session)
    assert len(session.calls) == 1
    assert excinfo.value.response is not None and excinfo.value.response.status == status


def test_retries_timeouts_and_connection_errors() -> None:
    session = FakeSession([requests.Timeout(), requests.ConnectionError(), FakeResponse(200)])
    assert call(session).status == 200


def test_non_retryable_error_status_is_returned() -> None:
    session = FakeSession([FakeResponse(404, b"not found")])
    raw = call(session)
    assert raw.status == 404 and len(session.calls) == 1


def test_authorization_header_not_kept_in_raw() -> None:
    session = FakeSession([FakeResponse(200)])
    raw = call(session, headers={"Authorization": "Bearer secret-token"})
    assert session.calls[0]["headers"] == {"Authorization": "Bearer secret-token"}
    assert "secret-token" not in repr(raw)


def test_throttle_spaces_calls_per_source() -> None:
    times = iter([0.0, 0.3, 1.0, 5.0, 5.0])
    sleeps: list[float] = []
    throttle = Throttle({"yahoo": 1.0}, sleep=sleeps.append, monotonic=lambda: next(times))
    throttle.wait("yahoo")  # first call: no wait; last = 0.0
    throttle.wait("yahoo")  # elapsed 0.3 → wait 0.7; last = 1.0
    throttle.wait("espn")  # different source: no wait; last[espn] = 5.0
    assert sleeps == [pytest.approx(0.7)]


def test_yahoo_rate_limit_999_backs_off_slowly() -> None:
    session = FakeSession([FakeResponse(999), FakeResponse(999), FakeResponse(200)])
    sleeps: list[float] = []
    assert call(session, sleeps).status == 200
    assert sleeps == [30.0, 60.0]
