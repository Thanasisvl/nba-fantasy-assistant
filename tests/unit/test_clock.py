from datetime import UTC, date, datetime, timedelta

import pytest

from nfa import clock


def test_now_is_utc_aware() -> None:
    current = clock.now()
    assert current.utcoffset() == timedelta(0)


def test_nba_today_uses_eastern_date() -> None:
    assert clock.nba_today(datetime(2026, 10, 21, 3, 0, tzinfo=UTC)) == date(2026, 10, 20)


def test_nba_today_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        clock.nba_today(datetime(2026, 10, 21, 3, 0))
