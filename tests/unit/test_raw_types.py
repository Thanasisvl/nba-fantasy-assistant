import dataclasses
from datetime import UTC, datetime

import pytest

from nfa.domain.raw import FetchRequest, RawResponse

REQ = FetchRequest(source="yahoo", dataset="league_settings", key="466.l.1")


def test_raw_response_requires_aware_datetime() -> None:
    with pytest.raises(ValueError):
        RawResponse(request=REQ, fetched_at=datetime(2026, 10, 21), status=200, payload=b"{}")


@pytest.mark.parametrize(("status", "ok"), [(200, True), (204, True), (404, False), (503, False)])
def test_ok_reflects_2xx(status: int, ok: bool) -> None:
    raw = RawResponse(request=REQ, fetched_at=datetime.now(UTC), status=status, payload=b"")
    assert raw.ok is ok


def test_types_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        REQ.key = "x"  # type: ignore[misc]
