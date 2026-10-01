# NBA Fantasy Assistant

Personal assistant for Yahoo NBA fantasy **head-to-head categories** leagues. It projects player stats, values pickups by usable games and category need, forecasts weekly matchups, and sends a daily email with lineup alerts and suggested moves.

It advises; it never makes moves on Yahoo. It runs locally on one machine for one user.

## Status

Planning is done; building has not started. Next milestone: **M0, a data access spike** (Yahoo OAuth, league settings and free agents, NBA game logs, player ID matching).

| Milestone | Delivers |
|---|---|
| M0 Spike | Yahoo OAuth, league data, NBA game logs, player ID crosswalk prototype |
| M1 Foundation | Storage, crosswalk, schedule, player board, health page |
| M2 Projections | Per-category projections, minutes and injury model, backtest and calibration harness |
| M3 Advice | Valuation, matchup projector, streaming ranker, lineup check, explanations |
| M4 Daily loop | Scheduled job, email digest, injury opportunity alerts, recommendation log |
| M5 Strategy | Punt analysis |

Details in [docs/PLAN.md](docs/PLAN.md).

## What it will do

- **Player board** with each league's own categories and scoring.
- **Matchup projector**: projected weekly totals and win probability per category, given the games left for both teams.
- **Streaming ranker**: free agents ranked by *usable* games (games on days you have an open lineup slot) and the categories you need, within the weekly add limit.
- **Lineup check**: players with games on the bench, injured players in active slots, empty slots.
- **Injury opportunity alerts**: when a player is ruled out, the teammates whose minutes rise.
- **Punt analysis**: which categories to concede, and how valuations change.
- **Daily email** across all leagues and teams.
- **Recommendation log and calibration**: every suggestion is stored with its inputs and scored against what happened.

Every recommendation comes with its reasons, with numbers.

## Design principles

- **League settings drive everything.** Categories, roster slots and add limits are read from each Yahoo league, never hardcoded.
- **Grow without rewrites.** Platform, stats source, scoring format, notifier and storage each sit behind an interface, so ESPN, points leagues or another notifier would each be one new adapter.
- **Pure core.** Projection and valuation logic does no I/O, so it can be tested and replayed against past seasons.
- **Proven, not assumed.** Projections are backtested day by day with no look-ahead and checked for calibration.
- **Degrade, don't crash.** Data sources can fail; the tool falls back to cached data and shows how old it is.

## Planned stack

Python 3.12+, `uv`, Streamlit (local UI), `nba_api` for NBA stats, the Yahoo Fantasy Sports API (read-only OAuth), parquet + SQLite for storage, launchd for the daily job, SMTP for email, `pytest`, `ruff`, `pyright`.

## Repository guide

| Path | Contents |
|---|---|
| `docs/PLAN.md` | Decisions, objectives, requirements, milestones, backlog |
| `CLAUDE.md` | Project rules for AI-assisted development |
| `.claude/skills/nba-fantasy-domain/` | Fantasy and statistics rules: z-scores, ratio categories, usable games, win probabilities, calibration |
| `.claude/skills/nfa-engineering/` | Code conventions: layers, interfaces, adapters, testing, secrets |

Setup instructions will be added with the first code (M0).

## Data and privacy

- Personal use only. NBA statistics and Yahoo data are used under those services' terms and are never committed or redistributed; `data/` is gitignored.
- Yahoo access is read-only. Credentials live in the macOS Keychain or a gitignored local file.

## License

No license is granted. All rights reserved.
