# Yahoo Fantasy Sports API notes

Working notes for the Yahoo adapter. Items marked (verify) must be confirmed in the M0 spike; update this file with what you find, including surprises.

## App registration and OAuth2

- Register an app at the Yahoo Developer Network with **Fantasy Sports: Read** permission only.
- Authorization code flow:
  - Authorize: `https://api.login.yahoo.com/oauth2/request_auth?client_id=…&redirect_uri=…&response_type=code`
  - Token: `POST https://api.login.yahoo.com/oauth2/get_token` with the code (and later the refresh token), HTTP Basic auth with client ID and secret.
- Access tokens expire after about an hour; refresh tokens are long-lived. Store both, refresh before expiry, and handle refresh failure by asking for a new login.
- Redirect URI: Yahoo is strict about redirect URIs (HTTPS; `oob` for out-of-band copy-paste has historically been supported) (verify). For a local tool, the copy-paste code flow is acceptable for a one-time login.
- Libraries such as `yahoo_oauth` / `yfpy` / `yahoo_fantasy_api` exist. Using one for auth is fine; still wrap everything behind our `FantasyPlatform` adapter so the library never leaks into services.

## Base URL and format

- Base: `https://fantasysports.yahooapis.com/fantasy/v2/`
- Responses are XML by default; append `?format=json` for JSON. The JSON is deeply nested with numbered keys (`"0"`, `"1"`, …, `"count"`) and lists of single-key dicts. Write one small normalizer and test it against fixtures instead of digging through the structure in every call.

## Keys

| Key | Shape | Example |
|---|---|---|
| Game | `nba` (current season alias) or numeric `game_id` per season | `nba`, `466` |
| League | `{game_id}.l.{league_id}` | `466.l.12345` |
| Team | `{league_key}.t.{team_id}` | `466.l.12345.t.3` |
| Player | `{game_id}.p.{player_id}` | `466.p.6014` |

- The numeric `game_id` changes every season; the `player_id` part is stable across seasons for the same player (verify). Store both the full player key and the stable ID in the crosswalk.
- Always resolve the season's `game_id` at runtime from `games;game_keys=nba`; never hardcode it.

## Useful resources

| Need | Path (append `?format=json`) |
|---|---|
| My NBA leagues | `users;use_login=1/games;game_keys=nba/leagues` |
| My teams | `users;use_login=1/games;game_keys=nba/teams` |
| League settings | `league/{league_key}/settings` |
| Standings | `league/{league_key}/standings` |
| Scoreboard / matchups | `league/{league_key}/scoreboard;week={n}` |
| Team roster on a date | `team/{team_key}/roster;date=YYYY-MM-DD` |
| Team stats for a week | `team/{team_key}/stats;type=week;week={n}` |
| Free agents | `league/{league_key}/players;status=FA;start={i};count=25` (also `status=W`, `status=A` for all available) |
| Player stats | `league/{league_key}/players;player_keys=…/stats;type=date;date=YYYY-MM-DD` (or `type=season`, `type=lastweek`) |
| Ownership | `…/players;player_keys=…/percent_owned` |
| Transactions | `league/{league_key}/transactions` |

- Sub-resources chain with `/` and filters with `;key=value`. Multiple keys are comma-separated (`player_keys=a,b,c`).
- `settings` includes `stat_categories` (id, name, display name, sort order, display-only flag), `roster_positions`, `max_weekly_adds` / acquisition limits, week dates and playoff settings (verify exact field names on the real leagues and record them here).
- Stats come back as `stat_id` → value. Map stat IDs to our categories using the league's `stat_categories`, not a hardcoded table.

## Pagination and limits

- Player collections return at most **25** per request; page with `start` and `count`.
- Rate limits are not documented. Throttle (~1 request per second to start), cache aggressively, and back off on HTTP 999 / 429 (verify the codes seen in practice).
- Free agent lists are large; fetch them sorted (e.g. `sort=AR` actual rank, or by a stat) and stop after a sensible depth (e.g. top 150–200), then fetch details only for candidates.

## Gotchas to watch for

- Percent stats: Yahoo reports FG%/FT% as values, and FGM/FGA as a display stat "made/attempted" string for some views. Always take makes and attempts.
- Dates are US/Eastern for the NBA schedule; normalize to a single timezone in the adapter and keep game dates as Eastern dates.
- Player positions are a list of eligible positions plus a "selected position" on roster calls. The selected position is the lineup slot that day.
- Players traded between NBA teams change `editorial_team_abbr`; the crosswalk is keyed on player, not team.
