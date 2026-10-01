# NBA Fantasy Assistant

Personal assistant for Yahoo NBA fantasy leagues (H2H categories). Single user, runs locally on a Mac: Streamlit UI, a daily launchd job, and a daily email digest. It advises; it never makes moves on Yahoo.

## Read first

- `docs/PLAN.md`: decisions, objectives (O1–O8), requirements (FR-*), milestones (M0–M5), backlog. It is the source of truth for scope.
- `docs/ARCHITECTURE.md`: components, interfaces, data model, flows. Source of truth for structure. Decision records in `docs/decisions/`.
- Skill `nba-fantasy-domain`: fantasy and statistics rules. Use it for projections, valuation, matchups, streaming, punting, backtests.
- Skill `nfa-engineering`: code structure, adapters, testing, and safety conventions. Use it for any code change.

## Rules that always apply

- **Yahoo is read-only.** Request only the read scope. Never call endpoints that change rosters, lineups, trades or settings, even if asked casually; that is a backlog item needing its own design.
- **Secrets stay out of git.** OAuth tokens, client secrets and SMTP passwords live in the macOS Keychain or a gitignored file. Never print or log them.
- **Tests never hit the network.** Use recorded fixtures.
- **Stay in scope.** Build what the current milestone in `docs/PLAN.md` needs. Backlog items wait until asked for. If a change alters a decision in the plan, update the plan in the same change.
- **Personal use only.** The data sources (`nba_api`, Yahoo) are used under personal-use terms. Do not add anything that redistributes their data publicly.

## Reference project

`~/projects/thanos/euroleaguefantasy` is the earlier EuroLeague tool by the same author. It is a source of ideas only, not of code, numbers or basketball assumptions. The competitions differ: the NBA plays 48-minute games (EuroLeague 40), an 82-game season with frequent back-to-backs, 6 fouls to foul out (EuroLeague 5), different rotations and positions. The fantasy games differ too: EuroLeague Fantasy is a salary-cap game, this is a draft-league H2H categories game.

**Ask the user before applying any assumption from the EuroLeague tool**: a minutes cap, a position split, a shrinkage constant, a status mapping, a threshold, anything. Say what you want to reuse and what differs in the NBA, and wait for agreement. See `.claude/skills/nba-fantasy-domain/references/euroleague-lessons.md`.
