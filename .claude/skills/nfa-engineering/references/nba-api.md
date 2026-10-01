# nba_api notes

`nba_api` is an unofficial Python client for stats.nba.com and the cdn.nba.com live data. Free, no key, personal use. Items marked (verify) must be confirmed in the M0 spike; update this file with findings.

## Endpoints we need

| Need | Endpoint (module in `nba_api.stats.endpoints`) | Notes |
|---|---|---|
| All players + IDs | `commonallplayers.CommonAllPlayers(season=..., is_only_current_season=1)` | NBA `PERSON_ID`, team, roster status |
| Player game logs (bulk) | `playergamelogs.PlayerGameLogs(season_nullable="2026-27", season_type_nullable="Regular Season")` | One call for the whole league; includes MIN, FGM, FGA, FTM, FTA, FG3M, PTS, REB, AST, STL, BLK, TOV, GAME_DATE |
| League game log | `leaguegamelog.LeagueGameLog(season="2026-27", player_or_team_abbreviation="P")` | Alternative bulk source |
| Season schedule | `scheduleleaguev2.ScheduleLeagueV2(season="2026-27")` | All games with dates (verify columns) |
| Box score of one game | `boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=...)` | For gaps or corrections |
| Today's games, live | `nba_api.live.nba.endpoints.scoreboard.ScoreBoard()` | cdn.nba.com, lighter, current day only |

- Prefer **bulk** endpoints (whole-league game logs) over per-player calls: one request instead of 500.
- Season strings look like `"2026-27"`. Season type `"Regular Season"`; decide explicitly whether Play-In and NBA Cup games count (Cup group games are regular-season games; the Cup final is not).

## Throttling and failures

- stats.nba.com is sensitive to request rate and headers and blocks many cloud/datacenter IPs. From a home IP it generally works.
- Set `timeout=60`, pause ~0.6–1s between calls, retry with backoff on timeouts and connection resets, and give up after a few tries (the cache keeps the tool usable).
- `nba_api` sends browser-like headers by default; if requests start failing, check the library version first (upstream changes are common) before adding custom headers.
- Columns change occasionally between endpoint versions (V2 → V3). Map columns explicitly in the adapter and fail with a clear message on missing columns.

## Data handling

- `MIN` can be a string `"MM:SS"` or a float depending on endpoint; normalize to float minutes.
- DNP games may be absent or present with 0 minutes; treat absence and 0 minutes consistently (a DNP is not a 0-stat game for per-game averages, but it matters for probability of playing).
- Game dates are Eastern; keep them as Eastern dates.
- `PERSON_ID` (a.k.a. `PLAYER_ID`) is the NBA ID used in the crosswalk.

## Fallbacks

- If stats.nba.com is down or blocked: Yahoo player stats by date (`type=date`) can rebuild recent game lines for rostered and top available players, with fewer columns.
- Schedule fallback: cdn.nba.com schedule JSON (verify the current URL in M0) or a cached copy; the schedule rarely changes after release apart from postponements.
- Injury report: the NBA's official injury report (published several times a day) or ESPN's injuries page; decide in M0 which is easier to parse reliably.
