import pytest

from nfa.adapters.platforms.yahoo.fetch import BASE_URL, YahooFetcher, yahoo_request
from nfa.domain.raw import FetchRequest
from tests.fakes import FakeResponse, FakeSession, no_wait_throttle


class StaticToken:
    def access_token(self) -> str:
        return "tok"


def test_builds_url_query_and_bearer_header() -> None:
    session = FakeSession([FakeResponse(200, b'{"fantasy_content":{}}')])
    fetcher = YahooFetcher(StaticToken(), no_wait_throttle(), session)
    request = yahoo_request("league_settings", "466.l.1", "league/466.l.1/settings")
    raw = fetcher.fetch(request)
    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == BASE_URL + "league/466.l.1/settings"
    assert call["params"] == {"format": "json"}
    assert call["headers"] == {"Authorization": "Bearer tok"}
    assert raw.request == request and raw.status == 200


def test_rejects_requests_for_other_sources() -> None:
    fetcher = YahooFetcher(StaticToken(), no_wait_throttle(), FakeSession([]))
    with pytest.raises(ValueError):
        fetcher.fetch(FetchRequest("espn", "injuries", "all"))


def test_session_has_no_write_methods_used() -> None:
    session = FakeSession([FakeResponse(200)])
    YahooFetcher(StaticToken(), no_wait_throttle(), session).fetch(
        yahoo_request("games", "nba", "games;game_keys=nba")
    )
    assert {c["method"] for c in session.calls} == {"GET"}
