import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from nfa.adapters.http import AuthError
from nfa.adapters.platforms.yahoo.auth import (
    AUTHORIZE_URL,
    REDIRECT_URI,
    TOKEN_URL,
    Tokens,
    YahooAuth,
    authorize_url,
    code_from_redirect,
)
from nfa.adapters.secrets import get_secret, set_secret

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


@dataclass
class FakeTokenResponse:
    status_code: int
    body: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self.body


class FakePost:
    def __init__(self, *responses: FakeTokenResponse) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, url: str, *, auth: tuple[str, str], data: dict[str, str], timeout: float):
        self.calls.append({"url": url, "auth": auth, "data": dict(data), "timeout": timeout})
        return self.responses.pop(0)


def ok(access: str = "acc-2", refresh: str | None = "ref-2", expires_in: int = 3600):
    body: dict[str, Any] = {"access_token": access, "expires_in": expires_in}
    if refresh is not None:
        body["refresh_token"] = refresh
    return FakeTokenResponse(200, body)


@pytest.fixture(autouse=True)
def client_credentials() -> None:
    set_secret("yahoo_client_id", "cid")
    set_secret("yahoo_client_secret", "csecret")


def store_tokens(expires_at: datetime) -> None:
    set_secret("yahoo_tokens", Tokens("acc-1", "ref-1", expires_at).to_json())


def make(post: FakePost) -> YahooAuth:
    return YahooAuth(post=post, now=lambda: NOW)


def test_authorize_url() -> None:
    url = authorize_url("cid")
    parts = urlsplit(url)
    assert url.startswith(AUTHORIZE_URL)
    assert parse_qs(parts.query) == {
        "client_id": ["cid"],
        "redirect_uri": [REDIRECT_URI],
        "response_type": ["code"],
        "scope": ["fspt-r"],
    }


def test_code_from_redirect() -> None:
    assert code_from_redirect(f"{REDIRECT_URI}?code=abc123") == "abc123"
    assert code_from_redirect(f"{REDIRECT_URI}?state=x&code=abc123&extra=1") == "abc123"


def test_code_from_redirect_tolerates_whitespace_and_quotes() -> None:
    assert code_from_redirect(f'  "{REDIRECT_URI}?code=abc123"\n') == "abc123"


@pytest.mark.parametrize(
    "pasted",
    [
        f"{REDIRECT_URI}?state=x",
        "https://evil.example/callback?code=SECRETCODE",
        "http://localhost:8765/callback?code=SECRETCODE",
        "https://localhost:9999/callback?code=SECRETCODE",
        "not a url",
    ],
)
def test_code_from_redirect_rejects_bad_input_without_echo(pasted: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        code_from_redirect(pasted)
    assert "SECRETCODE" not in str(excinfo.value)


def test_exchange_code_stores_tokens() -> None:
    post = FakePost(ok())
    tokens = make(post).exchange_code("abc123")
    call = post.calls[0]
    assert call["url"] == TOKEN_URL and call["auth"] == ("cid", "csecret")
    assert call["data"] == {
        "grant_type": "authorization_code",
        "code": "abc123",
        "redirect_uri": REDIRECT_URI,
    }
    stored = json.loads(get_secret("yahoo_tokens"))
    assert stored["access_token"] == "acc-2" and stored["refresh_token"] == "ref-2"
    assert tokens.expires_at == NOW + timedelta(seconds=3600)


def test_access_token_without_refresh_when_fresh() -> None:
    store_tokens(NOW + timedelta(minutes=30))
    post = FakePost()
    auth = make(post)
    assert auth.access_token() == "acc-1"
    assert post.calls == [] and auth.refreshed_at is None


def test_access_token_refreshes_within_five_minutes() -> None:
    store_tokens(NOW + timedelta(minutes=4))
    post = FakePost(ok())
    auth = make(post)
    assert auth.access_token() == "acc-2"
    assert post.calls[0]["data"]["grant_type"] == "refresh_token"
    assert post.calls[0]["data"]["refresh_token"] == "ref-1"
    assert auth.refreshed_at == NOW


def test_access_token_refreshes_long_expired_tokens() -> None:
    store_tokens(NOW - timedelta(days=3))
    assert make(FakePost(ok())).access_token() == "acc-2"


def test_refresh_keeps_old_refresh_token_when_omitted() -> None:
    store_tokens(NOW - timedelta(minutes=1))
    make(FakePost(ok(refresh=None))).access_token()
    assert json.loads(get_secret("yahoo_tokens"))["refresh_token"] == "ref-1"


def test_failed_refresh_raises_auth_error() -> None:
    store_tokens(NOW - timedelta(minutes=1))
    with pytest.raises(AuthError) as excinfo:
        make(FakePost(FakeTokenResponse(400, {"error": "invalid_grant"}))).access_token()
    assert "nfa.jobs.login" in str(excinfo.value)


def test_missing_tokens_raise_auth_error() -> None:
    with pytest.raises(AuthError):
        make(FakePost()).access_token()


def test_tokens_repr_hides_values() -> None:
    text = repr(Tokens("acc-secret", "ref-secret", NOW))
    assert "acc-secret" not in text and "ref-secret" not in text


def test_code_from_redirect_tolerates_whitespace_inside_quotes() -> None:
    assert code_from_redirect(f'" {REDIRECT_URI}?code=abc123 "') == "abc123"


def test_keychain_read_once_across_many_calls() -> None:
    store_tokens(NOW + timedelta(minutes=30))
    reads: list[str] = []

    def counting_get(account: str) -> str:
        reads.append(account)
        return get_secret(account)

    auth = YahooAuth(get_secret=counting_get, post=FakePost(), now=lambda: NOW)
    for _ in range(3):
        assert auth.access_token() == "acc-1"
    assert reads == ["yahoo_tokens"]


def test_refresh_uses_cached_client_credentials_after_first_read() -> None:
    store_tokens(NOW - timedelta(minutes=1))
    reads: list[str] = []

    def counting_get(account: str) -> str:
        reads.append(account)
        return get_secret(account)

    clock_values = iter(
        [
            NOW,
            NOW,
            NOW,
            NOW + timedelta(hours=2),
            NOW + timedelta(hours=2),
            NOW + timedelta(hours=2),
        ]
    )
    auth = YahooAuth(
        get_secret=counting_get,
        post=FakePost(ok(), ok(access="acc-3")),
        now=lambda: next(clock_values),
    )
    auth.access_token()
    auth.access_token()
    assert reads.count("yahoo_client_id") == 1 and reads.count("yahoo_client_secret") == 1
