"""The only module that reads the real time. Everything else takes `as_of` explicitly."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def now() -> datetime:
    return datetime.now(UTC)


def nba_today(at: datetime | None = None) -> date:
    """The NBA day (US/Eastern calendar date) at `at`, default now."""
    moment = now() if at is None else at
    if moment.tzinfo is None:
        raise ValueError("nba_today needs a timezone-aware datetime")
    return moment.astimezone(ET).date()
