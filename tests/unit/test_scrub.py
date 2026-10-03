import json

import pytest

from nfa.devtools.scrub import Json, Scrubber, UnsafeFixtureError, check_safe, scrub_payload


def test_manager_fields_get_consistent_placeholders() -> None:
    data: Json = [
        {"manager": {"nickname": "Aunt May", "guid": "G1", "email": "may@example.com"}},
        {"manager": {"nickname": "Aunt May", "guid": "G1"}},
        {"manager": {"nickname": "Uncle Ben", "guid": "G2"}},
    ]
    assert Scrubber().scrub(data) == [
        {"manager": {"nickname": "nickname-1", "guid": "guid-1", "email": "email-1"}},
        {"manager": {"nickname": "nickname-1", "guid": "guid-1"}},
        {"manager": {"nickname": "nickname-2", "guid": "guid-2"}},
    ]


def test_team_names_in_yahoo_list_form_are_replaced_but_stat_names_kept() -> None:
    team: Json = [[{"team_key": "466.l.1.t.2"}, {"team_id": "2"}, {"name": "May's Mayhem"}]]
    stat: Json = {"stat": {"stat_id": 5, "name": "Field Goal Percentage"}}
    assert Scrubber().scrub({"team": team, "stats": [stat]}) == {
        "team": [[{"team_key": "466.l.1.t.2"}, {"team_id": "2"}, {"name": "team-1"}]],
        "stats": [stat],
    }


def test_urls_are_replaced() -> None:
    long_url = "https://s.yimg.com/iu/api/res/1.2/" + "Ab9_-" * 20 + "/x.png"
    out = Scrubber().scrub({"headshot": {"url": long_url, "size": "small"}})
    assert out == {"headshot": {"url": "url-1", "size": "small"}}


def test_secret_keys_are_refused() -> None:
    with pytest.raises(UnsafeFixtureError):
        Scrubber().scrub({"access_token": "x"})


def test_forbidden_value_rejected_without_echo() -> None:
    with pytest.raises(UnsafeFixtureError) as excinfo:
        check_safe('{"error": "bad client cid-123"}', ["cid-123"])
    assert "cid-123" not in str(excinfo.value)


def test_token_like_strings_are_refused() -> None:
    with pytest.raises(UnsafeFixtureError):
        check_safe('{"x": "' + "A" * 80 + '"}', [])


def test_scrub_payload_round_trip() -> None:
    payload = json.dumps({"manager": {"nickname": "Aunt May"}}).encode()
    assert json.loads(scrub_payload(payload, [])) == {"manager": {"nickname": "nickname-1"}}


def test_non_json_payload_is_refused() -> None:
    with pytest.raises(UnsafeFixtureError):
        scrub_payload(b"%PDF-1.7", [])
