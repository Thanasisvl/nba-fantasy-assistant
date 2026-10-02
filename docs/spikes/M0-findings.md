# M0 findings

Status: in progress. NBA probe run 2026-10-02; Yahoo blocked pending Fantasy API approval (see Yahoo).
Spec: `docs/superpowers/specs/2026-10-02-m0-spike-design.md`

Each item: **Answer**, **Evidence** (raw file IDs, numbers), **Recommendation**.

## Yahoo

**Blocker found 2026-10-02.** Login works (code exchange returns tokens), but every Fantasy API call returns HTTP 403 `"This application is not authorized to perform this action"`. Since 2026-07-22 Yahoo requires apps to be approved for Fantasy API access through https://sports.yahoo.com/developer/access/ ([yfpy issue #84](https://github.com/uberfastman/yfpy/issues/84)); ticking "Fantasy Sports – Read" on developer.yahoo.com is no longer enough. Personal and single-league use is allowed; access is read-only by default.
- Application submitted 2026-10-02 (individual, personal, read-only, existing App ID). Yahoo's stated turnaround: 1–2 weeks.
- The authorize URL now requests `scope=fspt-r` explicitly; harmless now, likely needed once approved.
- **Recommendation:** M1 records NBA and injury data from day one; Yahoo league state joins as soon as access is granted. Record this as a risk in PLAN.

### Login and refresh
### Redirect handling
### Player ID stable across seasons?
### Settings fields (categories, roster positions, add limits, lock rule, weeks, playoffs)
### Roster slots and IL / IL+ eligibility in our leagues
### Player status codes
### Free-agent paging and % owned
### Ranks and projections endpoints
### Transactions and daily rosters reconstruct my decisions?
### Rate limits and error codes seen
### Scoring weeks longer than 7 days

## NBA data (`nba_api`, cdn.nba.com)
### Works from home connection? Timing and row counts
**Answer:** yes (2026-10-02, home connection, `nba_api` 1.11.4).
- `PlayerGameLogs` 2025-26 regular season: 26,651 rows in 3.3 s. Columns include `PLAYER_ID`, `TEAM_ABBREVIATION`, `GAME_ID`, `GAME_DATE`, `MIN`, `FGM`, `FGA`, `FTM`, `FTA`, `FG3M`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `PTS` (all 9-cat inputs, makes and attempts).
- `CommonAllPlayers` 2026-27 current: 618 players in 0.5 s; `PERSON_ID`, `DISPLAY_FIRST_LAST`, `TEAM_ABBREVIATION`, `ROSTERSTATUS`.
- Evidence: `nba_api/game_logs/2026-10-02/112758-2025-26.json.gz`, `nba_api/nba_players/2026-10-02/112759-2026-27.json.gz`.
**Recommendation:** `nba_api` stays the primary stats source (ADR 0004); one full-season pull is cheap enough for a nightly refresh.

### Schedule endpoint and columns
**Answer:** `ScheduleLeagueV2(season="2026-27")` works (2.6 s): 1,274 games on 174 dates from 2026-10-03 (preseason) to 2027-04-11, of which 1,206 are regular-season (`gameId` prefix `002`). 30 × 82 / 2 = 1,230, so 24 regular-season games are not yet scheduled (NBA Cup knockout-round slots are set during the season). Per game: `gameId`, `gameDateEst`, `gameDateTimeEst`/`UTC`, `gameStatus`, `homeTeam`/`awayTeam` (tricodes), `gameLabel` (Preseason, Emirates NBA Cup, …), `weekNumber`, `postponedStatus`.
- cdn.nba.com `scheduleLeagueV2.json` returned **403** to our client (blocks non-browser clients). Not needed.
- Evidence: `nba_api/schedule/2026-10-02/112802-2026-27.json.gz`.
**Recommendation:** schedule from `ScheduleLeagueV2`, refreshed at least weekly (Cup games and postponements change it); filter regular season by `gameId` prefix `002`; use `gameDateEst` as the NBA day.

**Code finding:** `http.get` raises `AuthError` for any 401/403, but for unauthenticated sources (cdn.nba.com) a 403 is a block, not bad credentials. M1: raise `AuthError` only for sources that authenticate; treat other 403s as `FetchError`.

## Injury source comparison
| Source | Players with status | First to show changes | Name matching | Parse effort | Notes |
|---|---|---|---|---|---|
| Official NBA report | | | | | |
| ESPN JSON | | | | | |
| Yahoo status | | | | | |

**Choice:**

## Crosswalk
- Rostered Yahoo players:
- Auto-matched (rate):
- Ambiguous / unmatched and proposed overrides:

## Doc changes made
