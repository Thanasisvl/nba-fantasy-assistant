"""Raw responses as received from a source, before any parsing (ADR 0008)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import NewType

RawFileId = NewType("RawFileId", str)


@dataclass(frozen=True)
class FetchRequest:
    source: str  # "yahoo", "nba_api", "cdn_nba", "espn", "nba_injury_report"
    dataset: str  # "league_settings", "rosters", "game_logs", ...
    key: str  # e.g. "466.l.12345.t.3;date=2026-10-21"
    params: Mapping[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True)
class RawResponse:
    request: FetchRequest
    fetched_at: datetime  # timezone-aware
    status: int
    payload: bytes  # body as received

    def __post_init__(self) -> None:
        if self.fetched_at.tzinfo is None:
            raise ValueError("fetched_at must be timezone-aware")

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300
