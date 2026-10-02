from datetime import UTC, datetime

from nfa.adapters.platforms.yahoo.auth import REDIRECT_URI, YahooAuth
from nfa.adapters.secrets import get_secret, set_secret
from nfa.domain.raw import FetchRequest, RawResponse
from nfa.jobs.login import main
from tests.adapters.test_yahoo_auth import FakePost, ok

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


class FakeFetcher:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.requests: list[FetchRequest] = []

    def fetch(self, request: FetchRequest) -> RawResponse:
        self.requests.append(request)
        return RawResponse(request=request, fetched_at=NOW, status=self.status, payload=b"{}")


def run(pasted: str, fetcher: FakeFetcher) -> tuple[int, list[str]]:
    lines: list[str] = []
    auth = YahooAuth(post=FakePost(ok()), now=lambda: NOW)
    code = main(
        auth=auth,
        fetcher_factory=lambda _a: fetcher,
        read_hidden=lambda _p: pasted,
        out=lines.append,
    )
    return code, lines


def test_login_stores_tokens_and_checks_with_one_call() -> None:
    set_secret("yahoo_client_id", "cid")
    set_secret("yahoo_client_secret", "csecret")
    fetcher = FakeFetcher()
    code, lines = run(f"{REDIRECT_URI}?code=abc123", fetcher)
    assert code == 0
    assert "acc-2" in get_secret("yahoo_tokens")
    assert len(fetcher.requests) == 1
    assert not any("abc123" in line or "acc-2" in line for line in lines)


def test_login_fails_cleanly_on_bad_paste() -> None:
    set_secret("yahoo_client_id", "cid")
    set_secret("yahoo_client_secret", "csecret")
    code, lines = run("https://evil.example/?code=abc123", FakeFetcher())
    assert code == 1
    assert not any("abc123" in line for line in lines)


def test_login_explains_missing_client_credentials() -> None:
    code, lines = run(f"{REDIRECT_URI}?code=abc123", FakeFetcher())
    assert code == 2
    assert any("security add-generic-password -U" in line for line in lines)
