# Domain types (sketch)

Code-level sketch of the core types and the recommendation object. **`docs/ARCHITECTURE.md` is authoritative** for the interfaces (§5) and the entity list (§6); the interface sketch at the end of this file is superseded by §5 and kept only as an illustration. When they differ, follow the architecture doc and update this file.

## Core types

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import NewType

PlayerId = NewType("PlayerId", str)        # internal, stable
LeagueKey = NewType("LeagueKey", str)      # e.g. "yahoo:466.l.12345"
TeamKey = NewType("TeamKey", str)

class Direction(Enum):
    HIGHER_IS_BETTER = "higher"
    LOWER_IS_BETTER = "lower"

@dataclass(frozen=True)
class Category:
    code: str                       # "PTS", "FG%", "TO"
    direction: Direction
    numerator: str | None = None    # ratio categories: "FGM"
    denominator: str | None = None  # ratio categories: "FGA"

    @property
    def is_ratio(self) -> bool:
        return self.numerator is not None

@dataclass(frozen=True)
class LeagueSettings:
    league: LeagueKey
    season: str                         # "2026-27"
    teams: int
    categories: tuple[Category, ...]
    active_slots: tuple[str, ...]       # ("PG","SG","G","SF","PF","F","C","C","Util","Util")
    bench_slots: int
    il_slots: int
    max_weekly_adds: int | None
    week_starts: tuple[date, ...]       # start date of each scoring week
    playoff_weeks: tuple[int, ...]

@dataclass(frozen=True)
class StatLine:                         # one player, one game
    player: PlayerId
    game_date: date
    minutes: float
    stats: dict[str, float]             # raw stats incl. makes/attempts: {"PTS": 22, "FGM": 8, "FGA": 15, ...}

@dataclass(frozen=True)
class Projection:
    player: PlayerId
    as_of: datetime
    window: tuple[date, date]
    games: float                        # expected games played in window (probability-weighted)
    per_game: dict[str, float]          # includes makes/attempts
    variance: dict[str, float]          # per game
    model_version: str
```

## Recommendation

```python
class Action(Enum):
    ADD = "add"; DROP = "drop"; START = "start"; BENCH = "bench"; PUNT = "punt"; ALERT = "alert"

@dataclass(frozen=True)
class Reason:
    text: str            # "4 usable games (3 on light days)"
    impact: float        # contribution to the score, for ordering
    supports: bool = True  # False for counter-reasons

@dataclass(frozen=True)
class Recommendation:
    id: str
    as_of: datetime
    league: LeagueKey
    team: TeamKey
    action: Action
    players: tuple[PlayerId, ...]      # e.g. (add, drop)
    expected_gain: float               # e.g. Δ expected categories won this week
    confidence: float                  # 0..1
    reasons: tuple[Reason, ...]
    snapshot_id: str
    model_version: str
```

## Interfaces

```python
from typing import Protocol

class FantasyPlatform(Protocol):
    def my_leagues(self, season: str) -> list[LeagueKey]: ...
    def settings(self, league: LeagueKey) -> LeagueSettings: ...
    def my_teams(self, league: LeagueKey) -> list[TeamKey]: ...
    def roster(self, team: TeamKey, on: date) -> "Roster": ...
    def matchup(self, team: TeamKey, week: int) -> "Matchup": ...
    def available_players(self, league: LeagueKey, limit: int) -> list["AvailablePlayer"]: ...
    def player_ids(self, league: LeagueKey) -> list["PlatformPlayer"]: ...   # for the crosswalk

class StatsSource(Protocol):
    def game_logs(self, season: str, since: date | None = None) -> list[StatLine]: ...
    def schedule(self, season: str) -> list["ScheduledGame"]: ...
    def players(self, season: str) -> list["SourcePlayer"]: ...

class ScoringFormat(Protocol):
    def player_values(self, projections: list[Projection], settings: LeagueSettings,
                      weights: dict[str, float] | None = None) -> dict[PlayerId, float]: ...
    def matchup_outlook(self, mine: "WeekState", theirs: "WeekState",
                        settings: LeagueSettings) -> "MatchupOutlook": ...

class Notifier(Protocol):
    def send(self, subject: str, html: str, text: str) -> None: ...

class Store(Protocol):
    def save_frame(self, name: str, frame, fetched_at: datetime, source: str) -> None: ...
    def load_frame(self, name: str) -> tuple[object, datetime | None]: ...
    def log_recommendations(self, recs: list[Recommendation]) -> None: ...
    def record_run(self, run_key: str, step: str, ok: bool, detail: str = "") -> None: ...
```

Notes:
- `Roster`, `Matchup`, `WeekState`, `MatchupOutlook`, `AvailablePlayer`, `ScheduledGame` and the player records are small frozen dataclasses defined alongside these.
- `WeekState` = accumulated stats so far + remaining projected player-games in active slots.
- `as_of` flows through every call that depends on time.
