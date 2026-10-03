# M0 findings

Status: in progress. NBA probe run 2026-10-02; Yahoo blocked pending Fantasy API approval (see Yahoo); ESPN verified as the fallback platform (see Alternative platforms); crosswalk measured on ESPN rosters 2026-10-03 (see Crosswalk).
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

First sample 2026-10-02 (preseason, one game on the latest report). The comparison continues on game days; Yahoo joins after Fantasy API approval.

| Source | Players with status | First to show changes | Name matching | Parse effort | Notes |
|---|---|---|---|---|---|
| Official NBA report | 5 (BOS@DET, 10/01 12:56 PM ET) | (needs more runs) | "Last, First" incl. suffixes ("Cenac Jr., Christopher") | Medium: positioned-text PDF, not a table; parse words by header column x-position; reasons can wrap onto lines above/below the player row | Game-specific statuses incl. Questionable and Rest; report time in the header and file name |
| ESPN JSON | 59 (45 Day-To-Day, 14 Out) | (needs more runs) | "First Last" display names | Low: plain JSON with status, note and date | Listed **none** of the 5 official-report players; some entries are stale (Summer League notes from July still Day-To-Day) |
| Yahoo status | blocked (Fantasy API approval pending) | | Yahoo player keys | Low (comes with roster/player data) | |

- Official report URL: the new season's listing page (`official.nba.com/nba-injury-report-2026-27-season/`) returns 404 before the season; the previous season's page links to the latest PDF (`ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMPM.pdf`). Only the latest PDF is linked.
- Evidence: `nba_injury_report/report/2026-10-02/113123-Injury-Report_2026-10-01_12_45PM.pdf.pdf.gz`, `espn/injuries/2026-10-02/113125-nba.json.gz`, `data/spike/injury_comparison.csv`.

**Provisional choice:** the **official NBA report** as the primary `InjuryFeed` (complete game-day statuses), with ESPN as a secondary source for notes and long-term injuries (filtered by date). Confirm after a week of regular-season runs (target end of comparison: 2026-10-27), including Yahoo once approved.

## Alternative platforms (Yahoo contingency)

Checked 2026-10-02 because Yahoo Fantasy API access is pending. **Decision rule:** if Yahoo has not approved by **2026-10-16**, M1 uses ESPN for league data; NBA stats and injuries are recorded from day one either way.

| Platform | Access | H2H categories | Verdict |
|---|---|---|---|
| **ESPN** | Unofficial JSON API (`lm-api-reads.fantasy.espn.com`); private leagues need the user's `espn_s2` + `SWID` cookies | Yes (each category / most categories) | **Fallback.** Verified end to end (below). |
| Fantrax | Small semi-official read API (`/fxea/general/...`): player IDs, ADP, league info by ID work without login; matchups/free agents need the unofficial logged-in route | Yes (most customizable) | Second fallback, mainly for the family league |
| Sleeper | Official, free, read-only, no auth (`api.sleeper.app`) | **No for season-long leagues as tested**: test league "The League that Tests" (6 teams) has points scoring only (`scoring_settings` pts/reb/ast/…, no FG%/FT%); 9-cat appears only in the Ring Chaser mini-game | Rejected: wrong format. Useful extras: injury status, other sites' IDs (incl. `yahoo_id`, `espn_id`), undocumented season stats and projections endpoints |
| CBS Sports | Deprecated API; 406 without a token | Yes | Rejected |

### ESPN verification

Test league **"The League that Tests"** (ID `1377295221`, ESPN season `2027` = NBA 2026-27, 6 teams, private), read with cookies from the Keychain (accounts `espn_s2`, `espn_swid`).

- **Settings (`view=mSettings`):** `scoringType: H2H_CATEGORY`; 9 categories after adding TO: PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO (`isReverseItem: true`). Stat IDs: 0 PTS, 1 BLK, 2 STL, 3 AST, 6 REB, 11 TO, 13/14 FGM/FGA, 15/16 FTM/FTA, 17 3PM, 19 FG%, 20 FT%. Lineup slots (ids): PG 0, SG 1, SF 2, PF 3, C 4, G 5, F 6, UTIL 11 (×3), bench 12 (×3), IR 13 (×1). `lineupLocktimeType: INDIVIDUAL_GAME`. Schedule: 19 weekly matchup periods, 4 playoff teams, 2-week playoff rounds, 167 scoring periods (days). `matchupTieRule: NONE`.
- **Acquisitions:** `acquisitionLimit: -1` (season unlimited), `matchupAcquisitionLimit: 1` with `matchupLimitPerScoringPeriod: true` (most likely 1 add per day), traditional waivers 24 h, `waiverProcessDays: ["SUNDAY"]` at 08:00, `isBenchUnlimited: true` (conflicts with 3 bench slots; to check in the UI).
- **Players (`view=kona_player_info` + `x-fantasy-filter` header):** 200 free agents sorted by % owned; per player `ownership.percentOwned` and `percentStarted`, `injuryStatus` (ACTIVE / DAY_TO_DAY / OUT), `draftRanksByRankType` (STANDARD, ROTO), `seasonOutlook`, `lastNewsDate`, actual stats (2025-26, 2026-27 splits) and **projections for 2026-27 including FGM/FGA, FTM/FTA and TO**. ESPN player IDs only (no NBA.com ID).
- **League views:** `mRoster` (6 teams), `mMatchup` (57 scheduled matchups), `mTransactions2` all respond; empty before the draft.
- **After the drafts (2026-10-03):** both ESPN leagues are drafted and fully readable with my cookies, including every team's roster (not only mine):
  - Family league `1377295221`: 6 teams × 13, 9-cat.
  - Public league "Phoenix Beginner H2H Categories League" (`1187400599`):
    - 10 teams × 13, snake draft, 4 playoff teams
    - **8-cat (no TO)**, same lineup slots as the family league
  - The fan endpoint lists both; its `abbrev` is upper case (`FBA`).
- **Which team is mine:** the team whose `owners` contains my `SWID`. Every other team is an opponent, so no "my teams" setting is needed.
- **Auth behaviour:** the 401 `AUTH_LEAGUE_NOT_VISIBLE` body is identical for no cookies, a bad `espn_s2` or a single cookie. The fan endpoint (`fan.api.espn.com/apis/v2/fans/{SWID}`) lists the user's leagues with only a valid `SWID`, which is a useful check of the league ID.

### ESPN vs Yahoo: what the design must handle

| Area | Yahoo | ESPN | Requirement |
|---|---|---|---|
| Add limits | usually per week | per day and/or per matchup, plus per season | Read the limit type; the streaming ranker must not assume weekly |
| Injured slots | IL and IL+ (IL+ accepts Day-to-Day) | IR | Read which statuses each slot accepts |
| Ties | ties possible | `matchupTieRule` | Win probabilities apply the league's tie rule |
| Injury note | text note | status only in this view (news separate) | Notes come from the injury feed |
| History | roster by date | roster by scoring period (day) | Map day ↔ scoring period in the adapter |
| % owned / projections | % owned; projections unverified | % owned + % started; projections with makes/attempts | ESPN projections can serve as the platform baseline (ADR 0010) |
| Access | official OAuth after approval | unofficial; session cookies expire, logout may invalidate them | Health page shows "ESPN cookies need refreshing" on 401 |

## Crosswalk

**Measured on ESPN** (2026-10-03), because Yahoo is blocked. Yahoo will be measured once approved.
- **Method:** the `crosswalk_probe` normalisation (accents, Jr./III suffixes, punctuation, case) matches names against `CommonAllPlayers` for 2026-27 (620 players). The team is used only to break ties.
- **Rostered ESPN players, both leagues:** 130 unique. **Auto-matched: 129 (99.2%)**. Ambiguous: 0. The family league alone matched 78/78.
- **Unmatched:** Russell Westbrook. ESPN shows him with team `FA` (unsigned), and he is not on the NBA current-player list. This is not a name problem.
- **Recommendation:**
  - The rule-based matching is enough; the 98% exit criterion is met on ESPN.
  - Treat unsigned players as their own state: matched once they sign, never silently dropped, and listed on the health page meanwhile.
  - Match against the full player list (`is_only_current_season=0`) or keep previously matched IDs, so a player who becomes unsigned keeps his NBA ID.

## Tooling notes

- `security add-generic-password ... -w` silently truncates the typed value to **128 characters**. `espn_s2` is about 316 characters, so it must be stored through Python instead: `uv run python -c "import getpass, keyring; keyring.set_password('nba-fantasy-assistant', 'espn_s2', getpass.getpass('espn_s2 (hidden): ').strip())"`. Yahoo client ID/secret and `SWID` are under 128.
- If `SSL_CERT_FILE` points at a custom CA bundle, `uv` and `gh` fail with certificate errors; run them as `env -u SSL_CERT_FILE …`.
- **Intermittent TLS errors from stats.nba.com (2026-10-03).** For a while, calls to stats.nba.com failed, with these symptoms:
  - "self-signed certificate in certificate chain" with the default certificates
  - a read timeout with a custom CA bundle

  Minutes later the normal certificate (DigiCert) was back and `nba_api` answered in 0.5 s. ESPN was unaffected.
  - `requests` ignores `SSL_CERT_FILE`; it uses `REQUESTS_CA_BUNDLE` or certifi.
  - A bare `requests` call to stats.nba.com without `nba_api`'s browser-like headers hangs until it times out.
  - **Consequence for M1:** the recorder must expect intermittent source failures. It retries later in the day, catches up missed days on the next run, and records gaps on the health page.

## Doc changes needed (from findings so far)

- PLAN: Yahoo approval risk and the 2026-10-16 decision rule; ESPN as fallback platform (new ADR).
- PLAN FR-D2/FR-E3 and the domain skill: H2H **Each Category** optimizes expected categories won; **Most Categories** optimizes the probability of winning the majority.
- PLAN/ARCHITECTURE: add-limit types (per day / per matchup / per season), injured-slot eligibility per platform, league tie rule.
- ADR 0009: injury feed provisional choice (official report primary, ESPN secondary).
- M1: `http.get` should raise `AuthError` only for authenticated sources.
- M1: recorder retries and catch-up of missed days after intermittent failures (Tooling notes).
- ARCHITECTURE (crosswalk): unsigned players as an explicit state; keep known NBA IDs when a player becomes unsigned.
- ARCHITECTURE (platform adapters): "my team" is the team owned by the logged-in account. Categories are read per league (8-cat and 9-cat in use).

## Doc changes made
