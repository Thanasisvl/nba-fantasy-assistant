# NBA Fantasy Assistant — Plan

Status: requirements and architecture agreed; M0 spike next.
Last updated: 2026-10-01

## Context

A personal assistant for Yahoo NBA fantasy leagues (H2H categories). It is a separate project from the EuroLeague Fantasy tool. That tool is a reference for ideas (minutes redistribution on injuries, early-season blending, parquet caching, tests, rules file), not a codebase to share.

"Scalable" in this project means growing without rewrites: more leagues and teams, more scoring formats, more platforms, more users, and more data sources. It does not mean traffic.

## Decisions so far

| Topic | Decision |
|---|---|
| Audience (v1) | Just me. Single user, my Yahoo login, runs on my Mac. |
| Platform | Yahoo Fantasy API (official, OAuth2, read-only scope). |
| Scoring formats (v1) | H2H categories only, read from each league's settings. Points and roto later behind the same scoring interface. |
| Automation | Advise + daily email digest. Read-only on Yahoo; I make the moves. |
| Interface | Streamlit, local. Core logic separate so a web front end can replace it later. |
| Runtime | My Mac, scheduled with launchd. Runs on wake if the Mac was asleep. |
| Digest channel | Email. |
| Team | Solo for now. |
| Timeline | No rush. Built in milestones that are each usable. |
| Stats source | `nba_api` (stats.nba.com) from my home IP, cached. Yahoo player stats as fallback. |
| Tooling | Python 3.12+, `uv`, `ruff`, `pyright`, `pytest`. |
| Storage | Parquet datasets + SQLite records (ADR 0003). |
| Yahoo OAuth | Own small module, tokens in the macOS Keychain (ADR 0006). |
| Injury source | Chosen in the M0 spike (official NBA report, ESPN, or Yahoo status). |
| Architecture | Ports and adapters with an explicit `as_of`; see `docs/ARCHITECTURE.md` and `docs/decisions/`. |
| Commercial use | Not designed for now. Would require licensed data, hosting, accounts. Revisit after the season with the recommendation log as evidence. |

## Test leagues

| League | Role | Tests |
|---|---|---|
| Public league (12 teams) | Production | Whether the advice wins against active opponents and a realistic waiver wire. |
| Friends & family (6–8, mostly inactive, I'm commissioner) | Dev / sandbox | Whether the tool reads settings and data correctly. Settings can be changed on purpose. |
| Closed 4-team, active (maybe) | Format variant | Only worth creating as a different format (points or roto) to test the scoring abstraction. |

My teams: Bulldozers (est. 2015), The Alternates (est. 2026).

## Objectives

| # | Objective | Success measure |
|---|---|---|
| O1 | Win more H2H category matchups | Public league win rate; categories won vs. projection |
| O2 | Under 5 minutes a day of management | The daily email alone is enough to act on most days |
| O3 | Prove the advice works | Every recommendation is logged and scored; weekly scorecard |
| O4 | Grow without rewrites | A new league is config; a new format, platform or source is one adapter |
| O5 | Explainable | Every recommendation carries its top 3 reasons, with numbers |
| O6 | Low upkeep | Under 1 hour/week of tool maintenance; a health page shows every source's status |
| O7 | Calibrated | Win probabilities in a bucket (e.g. 60–70%) come true about that often; checked in backtests and live |
| O8 | Fun / social | The family league stays engaged (weekly recap after v1) |

## Scope

**In v1:** Yahoo, H2H categories, multiple leagues and teams, read-only, local Streamlit, daily email, recommendation log, schedule planner, injury opportunity alerts, backtest and calibration harness, punt analysis.

**Not in v1 (the design must allow it later):** points/roto, ESPN/Sleeper, draft assistant, trade analyzer, write actions (lineups, add/drop), multiple users, hosting, AI chat, commercial use.

## Functional requirements

### A. League connection (Yahoo)
- FR-A1: Yahoo OAuth2 with read-only scope; the token refreshes automatically.
- FR-A2: Find all my NBA leagues and teams for the current season automatically.
- FR-A3: Read each league's settings: categories, roster slots, weekly add limit, schedule and playoff weeks, lineup lock rules.
- FR-A4: Read rosters, current matchup and opponent, free agents with % owned, and recent transactions.

### B. Basketball data
- FR-B1: Player game logs for this season and last season, and the full schedule.
- FR-B2: Injury status from an NBA/ESPN source, cross-checked against Yahoo's flag.
- FR-B3: Player ID crosswalk (Yahoo ID ↔ NBA ID), resolved once and stored. No fuzzy name matching at runtime.

### C. Projections
- FR-C1: Per-game projection for each counting stat. For percentages, project makes and attempts, not the percentage itself.
- FR-C2: Minutes model including injury redistribution and early-season blending with last season. Both ideas exist in the EL tool, but all NBA parameters (splits, caps, shrinkage) are derived from NBA data and agreed with me; nothing is carried over from EuroLeague without asking.
- FR-C3: Projections for any window: today, rest of the week, rest of the season.

### D. Valuation
- FR-D1: Z-score value per league, using that league's categories and replacement level.
- FR-D2: Need-based weights for a specific matchup.

### E. Tools (Streamlit pages)
- FR-E1: Player board: filters by league, free agent or rostered, games this week.
- FR-E2: Matchup projector: projected final total and win probability per category, given the games left for both teams.
- FR-E3: Streaming / waiver ranker: free agents ranked by usable games × category need, respecting the weekly add limit and who to drop.
- FR-E4: Lineup check: players with games on the bench, injured players in active slots, empty slots.

### F. Daily digest
- FR-F1: One email per day covering all my teams: lineup alerts, injury changes, matchup status, top 3 suggested moves.
- FR-F2: Sent before the first game of the day locks. If the Mac was asleep, sent on wake and marked late.

### G. Recommendation log
- FR-G1: Store each recommendation with a snapshot of the inputs it was based on.
- FR-G2: Weekly scorecard: what was recommended, what I did, how it turned out.

### H. Schedule
- FR-H1: Grid of games per team per week for the whole season, flagging light days and back-to-backs.
- FR-H2: Usable games: a pickup's games only count on days with an open active slot for his position. The streaming ranker uses this instead of raw games.

### I. Injury opportunities
- FR-I1: When a player's status changes to Out, recalculate teammates' minutes and flag free agents whose projection rises above a threshold.
- FR-I2: Opportunity alerts go at the top of the daily email.

### J. Backtest and calibration
- FR-J1: Replay last season day by day using only data available on each date.
- FR-J2: Report projection error per category and a calibration table for matchup win probabilities.
- FR-J3: Compute the same metrics live from the recommendation log during the season.

### K. Punt analysis
- FR-K1: Category profile for each of my teams: strength vs. the league in each category.
- FR-K2: Suggest 0–2 categories to punt; show how valuations and the ranker change if accepted.
- FR-K3: Punt settings stored per team.

### Cross-cutting
- FR-X1: Every recommendation object includes a `reasons` list. UI and email display it; they never generate it.
- FR-X2: Health page plus an email section showing each source's last success, data age and error count.

## Non-functional requirements

| Area | Requirement |
|---|---|
| Runtime | Python, on my Mac. Scheduled with launchd. Jobs are safe to re-run and catch up after sleep. Cost: $0. |
| Resilience | Unofficial sources will break. Keep working on cached data, show data age, never crash. |
| Politeness | Cache aggressively; fetch only new data; respect rate limits. |
| Security | OAuth tokens and SMTP credentials outside git (Keychain or gitignored file). Yahoo access read-only. |
| Testability | Core logic does no I/O. Tests use recorded fixtures and never hit the network. |
| Observability | Each job records its last success. Failures show in the app and in the email. |
| Reproducibility | Inputs snapshotted so any past recommendation can be recomputed exactly. |
| Extensibility | Five interfaces: platform, stats source, scoring format, notifier, storage. |

## Constraints and assumptions

- Personal use only, so unofficial data sources are acceptable. A commercial version would need licensed data.
- Yahoo NBA leagues default to daily lineups; freshness matters every day.
- Solo, no deadline. Each milestone should still produce something usable.

## Risks

| Risk | Mitigation |
|---|---|
| stats.nba.com breaks or blocks requests | Fall back to Yahoo player stats; cached data keeps the tool usable |
| Yahoo API quirks (XML, undocumented rate limits, free agent pagination) | Test everything in M0 before building on it |
| Bad player ID matching silently corrupts projections | Crosswalk checked in a test; unmatched players reported on the health page |
| Too much scope | v1 ends at M5; everything else goes to the backlog |

## Milestones

| Milestone | Delivers | Proves |
|---|---|---|
| M0 Spike | Yahoo OAuth, league settings and free agents, `nba_api` game logs, ID crosswalk prototype | Data access works from my Mac |
| M1 Foundation | Storage, crosswalk, schedule, player board, health page | Data is complete and correct |
| M2 Projections | Per-category projections, minutes and injury model, backtest and calibration harness | Projections are trustworthy before anything depends on them |
| M3 Advice | Z-score valuation, matchup projector, streaming ranker with usable games, lineup check, reasons | O1, O5 |
| M4 Daily loop | launchd job, email digest, injury opportunity alerts, recommendation log, scorecard | O2, O3, O6 |
| M5 Strategy | Punt analysis | Completes v1 |
| v1.x | Weekly recap (O8), what-if simulator, buy-low/sell-high, playoff schedule | |

The backtest harness is in M2, before the advice tools, so advice is never built on unvalidated projections.

## Backlog (after v1)

- Weekly league recap for the family league (O8). Members must agree to receive it; an AI-written version needs an LLM API key.
- What-if simulator (add X / drop Y → category win odds)
- Buy-low / sell-high
- Fantasy-playoff schedule strength
- Opponent profiling (manager activity)
- IL slot manager
- Trade analyzer
- "Ask my league" AI chat (Claude + MCP on top of the core)
- Draft assistant for next season
- Points and roto formats; ESPN / Sleeper adapters; one-click actions

## Next step

M0 spike (see `docs/ARCHITECTURE.md` §15 for the items to verify):

- Before it starts (me): register a Yahoo Developer app with Fantasy Sports read permission, join the public league, set up the family league.
- `scripts/spike/`: `yahoo_auth.py`, `yahoo_probe.py`, `nba_probe.py`, `crosswalk_probe.py`.
- Findings in `docs/spikes/M0-findings.md`; resolve every "(verify)" note and revise the architecture.
- Exit criteria: OAuth login and refresh work; settings parsed for both leagues; free agent pagination works; `nba_api` works from home; ≥ 98% of rostered players auto-matched to NBA IDs.
