# EuroLeague tool: ideas only, never assumptions

The EuroLeague Fantasy tool (`~/projects/thanos/euroleaguefantasy`) solved some similar problems for a **different competition with different rules**. It is a source of ideas, not of numbers, thresholds or basketball assumptions.

## The rule

**Before using anything from the EuroLeague tool — a number, a threshold, a split, a cap, a status mapping, a blending choice or an assumption about how basketball is played — stop and ask the user first.** State what you want to carry over, why, and what would differ in the NBA. Do not apply it until the user agrees. NBA parameters come from NBA data (backtests) and the user's decisions.

This applies even when the idea seems obviously transferable. The cost of asking is small; a wrong EuroLeague assumption silently baked into projections is expensive to find later.

## Why the numbers do not transfer

| | EuroLeague | NBA | Effect on the model |
|---|---|---|---|
| Game length | 40 minutes (4 × 10) | 48 minutes (4 × 12) | Minutes, caps, per-36 baselines and per-game totals all differ |
| Foul-out | 5 fouls (FIBA) | 6 fouls | Big men's minutes and foul-trouble risk differ |
| Regular season | Far fewer games, typically 1–2 per week | 82 games, typically 3–4 per team per week | Sample sizes, shrinkage speed, rest patterns |
| Back-to-backs | Rare | Common, with planned rest | Probability of playing per game |
| Rotations | Different depth and minute distribution | Deeper rosters, minutes restrictions, load management | How minutes redistribute when someone is out |
| Positions | Fantasy uses G / F / C | Yahoo uses PG, SG, SF, PF, C with multi-eligibility | Position-based splits and lineup slots |
| Fantasy scoring | PIR-based points, salary-cap squad, coach | H2H categories, draft league, no coach | Almost nothing in the scoring logic carries over |
| Injury reporting | Third-party injury page | Official NBA injury report with defined statuses, published several times a day | Status vocabulary and timing |
| Pace and style | Generally slower, different shot profile | Faster pace, more 3-point attempts | Per-minute rates and category distributions |

## Ideas worth discussing (ask before applying)

Each item lists the idea and the questions to put to the user. EuroLeague-specific values are deliberately left out.

### Injury minutes redistribution
- Idea: when a rotation player is out, give his expected minutes to available teammates; avoid double counting when his absence is already in the averages; take the minutes back when he returns. EuroLeague implementation: `src/injuries.py`, `apply_injury_minutes`.
- Ask: how to split minutes across positions in the NBA, what cap per player, whether to treat starters and bench differently, whether to use NBA on/off or lineup data instead.

### Early-season blending
- Idea: blend this season with last season while the sample is small. EuroLeague implementation: `src/project.py` (season choice and `_shrink_factor`).
- Ask: the shrinkage form and constants per stat (the NBA's longer season and different noise levels mean they must be derived from NBA backtests), and how to treat rookies and players who changed teams or roles.

### Status as a small vocabulary
- Idea: map injury statuses to a few groups. EuroLeague implementation: `src/injuries.py`, `KNOWN_LABELS`.
- Ask: how NBA statuses (and Yahoo's codes) map to a probability of playing.

### Caching and refresh
- Idea: cache immutable box scores and fetch only new games. This is an engineering pattern, not a basketball assumption, so it does not need sign-off; the refresh frequencies for NBA data do.

## Things the EuroLeague tool does that we deliberately do differently

These are design choices already agreed in `docs/PLAN.md`, not basketball assumptions:
- Backtests replay day by day (walk-forward) instead of a single time-ordered split.
- Player names are matched once in a crosswalk instead of at runtime across modules.
- UI pages stay thin, with logic in services.
