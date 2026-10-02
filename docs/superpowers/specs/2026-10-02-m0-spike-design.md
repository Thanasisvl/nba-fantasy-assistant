# M0 spike: design

Date: 2026-10-02
Status: draft for review
Builds on: `docs/PLAN.md` (M0, exit criteria), `docs/ARCHITECTURE.md` (§4–§5 layout and interfaces, §15 open items), ADRs 0006 and 0008.

## 1. Intent

**Purpose.** Settle every open question that would otherwise block M1 (the recorder), so M1 can be built quickly and start recording early in the 2026-27 season: Yahoo login and refresh, redirect handling, Yahoo endpoints (including ranks, projections, transactions), `nba_api` from my home connection, the injury source, and player matching across sources.

**Success.** The M0 exit criteria are met (§6), `docs/spikes/M0-findings.md` answers every item in ARCHITECTURE §15, and the docs are updated with what was learned.

**Priority.** Speed over polish, because M1 is time-critical. Correctness and secret handling are not traded away.

## 2. Decisions

| # | Decision |
|---|---|
| M0-1 | **Hybrid code:** pieces M1 needs anyway are real, tested code in `src/nfa/`; probes are throwaway scripts in `scripts/spike/`. |
| M0-2 | **Kept core = auth plus the raw path:** project skeleton, Keychain and OAuth, `RawResponse`/`FetchRequest`, raw-file writer with `raw_files` table, polite HTTP helper, thin Yahoo fetch. Probes save in M1's raw format. No parsers into datasets. |
| M0-3 | **Login by pasting the redirected URL.** A local HTTPS listener on 8765 is added later only if re-logins turn out to be frequent. |
| M0-4 | **Injury comparison** of three sources: official NBA report (PDF), ESPN injuries JSON, Yahoo player status. Runs into the first week of real games if preseason data is thin. |

## 3. Kept core

Code under `src/nfa/`, following ARCHITECTURE §4–§5.

| File | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock` | Python 3.12+, `uv`. Runtime: `requests`, `keyring`, `pandas`, `pyarrow`, `nba_api`. Dev: `pytest`, `ruff`, `pyright`. Spike-only: `pdfplumber` (dependency group `spike`). |
| `nfa/clock.py` | The only module that reads real time: `now()` (UTC, timezone-aware) and `nba_today()` (US/Eastern date). |
| `nfa/config.py` | Loads `config.toml` (gitignored); `config.example.toml` committed. M0 settings: data directory (default `data/`), per-source throttle intervals. |
| `nfa/domain/raw.py` | `RawFileId`, `FetchRequest`, `RawResponse` exactly as in ARCHITECTURE §5. |
| `nfa/adapters/http.py` | `get(request, url, headers, *, throttle_s, timeout_s) -> RawResponse`. Timeout on every call; throttle per source; up to 3 retries with exponential backoff and jitter on 5xx, 999, 429 and timeouts; never retries 401/403 (raises `AuthError`); raises `FetchError` after the last retry. Strips `Authorization` from anything returned. |
| `nfa/adapters/secrets.py` | `get_secret(account)`, `set_secret(account, value)` via `keyring`, service `nba-fantasy-assistant`. Never logs values. |
| `nfa/adapters/platforms/yahoo/auth.py` | `authorize_url()`; `code_from_redirect(pasted_url)`; `exchange_code(code)`; `access_token()` refreshing when expiry is under 5 minutes away; tokens stored as JSON (access token, refresh token, expiry) in account `yahoo_tokens`. Client ID and secret from `yahoo_client_id`, `yahoo_client_secret`. Token endpoint uses HTTP Basic auth (Confidential Client). Failed refresh raises `AuthError`. |
| `nfa/adapters/platforms/yahoo/fetch.py` | `fetch(request) -> RawResponse`: builds `https://fantasysports.yahooapis.com/fantasy/v2/{path}?format=json`, adds the bearer token, GET only. |
| `nfa/adapters/store/raw.py` | `write_raw(raw) -> RawFileId`: writes `data/raw/{source}/{dataset}/{YYYY-MM-DD}/{HHMMSS}-{key}.json.gz` atomically (temporary file, then rename) and inserts a `raw_files` row (source, dataset, request key, `fetched_at`, path, sha256, status). Keys are made filesystem-safe. |
| `nfa/adapters/store/migrations/0001_raw_files.sql` + a minimal migration runner | Creates `raw_files` and `schema_migrations` in `data/app.sqlite` (WAL mode). |
| `nfa/jobs/login.py` | `uv run python -m nfa.jobs.login`: prints the authorize URL, asks me to paste the redirected URL (input not echoed), exchanges the code, stores tokens, confirms with one test call. |

**Errors.** `AuthError` (401/403 or failed refresh) is never retried and says to run the login job. `FetchError` covers 5xx, timeouts, 999 and 429 after retries. Failed responses are still written as raw files with their status, so gaps are visible.

**Secrets.** Never printed or logged; `Authorization` headers never saved; the pasted redirect URL is not echoed; tokens only in the Keychain. Existence checks use `security find-generic-password -s … -a …` without `-w`.

**Read-only.** The Yahoo client sends only GET requests; a test asserts it.

## 4. Throwaway probes

Scripts in `scripts/spike/`, each with a docstring saying it is throwaway M0 code. All network calls go through the kept core and every response is saved with `write_raw`.

**`yahoo_probe.py`**
1. `games;game_keys=nba`: this season's `game_id`.
2. `users;use_login=1/games;game_keys=nba/leagues` and `/teams`: my leagues and teams.
3. Per league: `settings`, `standings`, `scoreboard`, `transactions`, and each team's roster for today.
4. Free agents: `players;status=A;sort=AR;start={i};count=25` until 200 players or the end; records `percent_owned`.
5. Ranks and projections: tries `sort=AR` and `sort=OR`, `stats;type=season|lastweek|date`, and projected-stat variants; records which work and which fields they return.
6. Player IDs across seasons: the same players' keys under last season's and this season's `game_id`.
7. Prints a summary: requests, failures, durations, any 999/429 responses, and the settings field names found (stat categories, roster positions, add limits, lock rule, week dates, playoff weeks).

**`nba_probe.py`**
- `PlayerGameLogs` for 2025-26 (rows, columns, duration), `CommonAllPlayers`, `ScheduleLeagueV2` for 2026-27, and the cdn.nba.com schedule JSON as an alternative. Responses saved as raw (`source = "nba_api"`). Records whether any call is blocked or slow.

**`injury_probe.py`**
- One run fetches: the latest official NBA injury report PDF (table extracted with `pdfplumber`), the ESPN injuries JSON, and Yahoo player statuses for players in my leagues.
- Saves each response as raw and appends one row per player per source to `data/spike/injury_comparison.csv` (run time, source, player name as given, team, status, detail, source timestamp if any).
- I run it by hand a few times a day for about a week, starting with the first days of real games.

**`crosswalk_probe.py`**
- Normalizes names (accents, suffixes such as Jr./III, punctuation, case) and matches rostered Yahoo players to NBA person IDs on name plus team.
- Reports the auto-match rate (target ≥ 98%) and lists misses with suggested overrides for `data/crosswalk_overrides.json`.

**`scrub_fixture.py`** (kept for M1)
- Copies selected raw files into `tests/fixtures/raw/{source}/`. Replaces other managers' names, nicknames, emails and GUIDs with placeholders; removes token-like strings; refuses to write if anything secret-looking remains.

## 5. Tests (kept core only)

`pytest` with network blocked by an autouse fixture; written test-first.

- **auth:** authorize URL; code extraction from a pasted URL (valid, extra parameters, missing code, wrong host); code exchange and refresh against a fake HTTP layer; refresh when expiry is under 5 minutes away and not otherwise; failed refresh raises `AuthError`; tokens saved as JSON in `yahoo_tokens`.
- **secrets:** get and set through an in-memory `keyring` backend.
- **http:** retries on 5xx and 999, not on 401/403; gives up after 3 retries with `FetchError`; a timeout is always passed; throttle spaces consecutive calls; `Authorization` is not present in the returned `RawResponse`.
- **raw store:** path layout; atomic write (no partial file on failure); `raw_files` row sha256 matches the file; gzip round-trip; failed responses stored with their status; migration applies on an empty database and is idempotent.
- **yahoo fetch:** URL and `format=json`; bearer header added; only GET used.
- **architecture:** `nfa.domain` imports nothing from other `nfa` packages.

Probes have no tests; their output is the evidence.

## 6. Findings and exit criteria

`docs/spikes/M0-findings.md` has one section per ARCHITECTURE §15 item (answer, evidence, recommendation), the injury comparison table (timeliness, coverage, name matching, parse effort), the crosswalk numbers and misses, and the list of doc changes made.

M0 is done when:

- [ ] Yahoo login and token refresh work for real, and a refresh has been observed.
- [ ] Settings are fetched and readable for every league I am in (at least the family league).
- [ ] Free-agent paging returns at least 200 players.
- [ ] `nba_api` returns 2025-26 game logs and the 2026-27 schedule from my home connection.
- [ ] At least 98% of rostered players match automatically, or the reason is understood and overrides are listed.
- [ ] The injury source is chosen, or provisionally chosen with an end date for the comparison.
- [ ] The findings are written; ARCHITECTURE, the ADRs and the skills are updated and §15 items checked off.
- [ ] The kept core passes `pytest`, `ruff` and `pyright`.

## 7. Out of scope

Parsers into datasets; the `daily` and `snapshot` launchd jobs; the Streamlit app; the local login listener; backups.

## 8. Process

Branch `m0/spike`. One PR at the end, or two if the kept core is ready before the injury comparison ends. Ask before every commit, push and merge. I approve the Yahoo login in my browser; probes needing real games wait for them.
