---
name: nba-fantasy-domain
description: Fantasy basketball and statistics rules for the NBA Fantasy Assistant (Yahoo H2H categories). Use this whenever you work on projections, minutes, injuries, player valuation or z-scores, matchup win probabilities, the streaming/waiver ranker, usable games, lineup checks, punt analysis, pre-draft rankings, model baselines, the recommendation log, backtests or calibration — even if the request only says "rank pickups", "fix the projection", "why did it suggest X" or "is this number right".
---

# NBA fantasy domain rules

Fantasy math has traps that look right and are wrong. Each rule below names the trap so you can spot new variants of it. The formulas, worked examples and league rules are in `references/`; read the one you need before implementing or changing that piece.

| Reference | Read it when |
|---|---|
| `references/formulas.md` | Implementing or changing z-scores, projections, shrinkage, win probabilities, usable games, stream gain, calibration |
| `references/yahoo-league-rules.md` | Anything that depends on league settings: categories, positions, roster slots, add limits, lineup locks, waivers, IL, playoffs |
| `references/euroleague-lessons.md` | Any time the EuroLeague tool comes up: rule differences, and the questions to ask the user before reusing an idea |
| `references/glossary.md` | A term is unclear, or you need consistent naming in code and UI |

## 0. NBA rules, NBA data, and ask before assuming

- Everything here is about the **NBA** (48-minute games, 82-game season, frequent back-to-backs, 6 fouls to foul out). Do not carry over basketball rules, minutes, thresholds or parameters from the EuroLeague tool or from EuroLeague basketball.
- **Before using any assumption that comes from the EuroLeague tool, ask the user first** and wait for agreement. Explain what you want to reuse and what differs in the NBA. `references/euroleague-lessons.md` lists the differences and the questions to ask.
- Model parameters (caps, splits, shrinkage constants, thresholds) are NBA-derived: from backtests on NBA data, or decided with the user. When a value is a placeholder, label it as one in code and in the docs.

## 1. The game we optimize

- Yahoo **head-to-head categories**. Each week (Monday–Sunday) a team plays one opponent; each category is won, lost or tied by comparing weekly totals. The team winning more categories wins the week.
- The standard set is 9-cat: PTS, REB, AST, STL, BLK, 3PTM, FG%, FT%, TO. **Never hardcode it.** Read the categories, their sort direction, roster slots, add limit, lock rules and playoff weeks from each league's settings. Leagues differ (8-cat without TO, extra categories such as DD or A/TO), and the sandbox league exists to change settings on purpose.
- A player only contributes on days he has a game **and** sits in an active slot. Bench (BN) and IL slots score nothing.
- What wins a week is **categories won**, not total value. A move that adds a lot of points in a category you are already winning by 300 is worth almost nothing this week.

## 2. Percentages are volume-weighted

FG% and FT% are ratios of weekly sums, not averages of player percentages. A 90% FT shooter taking 1 attempt barely moves a team's FT%; one taking 10 moves it a lot.

- Project and aggregate **makes and attempts**; compute the percentage at the end from the summed numbers.
- For valuation, z-score the **impact**: `attempts × (player_pct − pool_pct)`. A 40% shooter on 2 attempts hurts less than a 45% shooter on 20.
- Never average percentages across players or games. This includes "season FG%" built as the mean of per-game FG%.
- The same applies to any ratio category a league might use (A/TO, FT%, 3P%): sum numerators and denominators separately.

## 3. Valuation (z-scores)

- Per league, per category: `z = (value − mean) / sd` over the **relevant pool**: roughly the top `teams × active roster spots` players by value, found iteratively (rank, take the pool, recompute, repeat until stable). A pool that is too wide inflates everyone and makes replacement level meaningless.
- Flip the sign for lower-is-better categories (TO).
- Per-game value ranks talent. **Window value** (per game × usable games in the window) decides streams and starts. Do not mix them in one ranking.
- Total value = weighted sum of category z-scores. Weights: 0 for punted categories, matchup need weights for weekly decisions (section 5), 1 otherwise.
- Replacement level is the value of the best free agent at a position in **that** league. A player's value above replacement is what a roster spot is actually worth.

## 4. Projections

- **Minutes × per-minute rates.** Minutes move with injuries, rotation changes, blowouts and rest; rates are more stable. Most projection errors are really minutes errors, so put the modelling effort there.
- **Early season:** shrink toward last season (or a role/position prior for rookies and role changes) with a weight that grows with games played. Minutes and usage stabilize within a few games; FT% and 3P% need many more attempts. The shrinkage constant is per stat and tuned by backtest (formulas in `references/formulas.md`).
- **Recent form** gets some weight, but a hot week is mostly noise. Use a longer window with decay, not "last 5 games" alone.
- **Games played probability:** a player listed Questionable or Day-to-Day does not play every remaining game. Multiply window projections by the probability he plays, and treat back-to-backs as a rest risk for veterans and players on minutes restrictions.
- **Injury minutes:** when a rotation player is Out, his expected minutes go to available teammates. Do not add them again if his absence is already in teammates' recent averages; take them back when he returns. How the minutes are split (by position, role, starters vs bench) and any per-player cap are **open decisions**: derive them from NBA data and confirm them with the user. The EuroLeague tool has a version of this idea; its numbers do not apply (see `references/euroleague-lessons.md`).
- **Windows:** today, rest of week, rest of season. A window projection is per game × the player's games in the window × probability he plays.
- Separate "who will play" (status, minutes) from "how well" (rates). They fail in different ways and need different data sources.
- **Data for the minutes model.** On last season, absences inferred from box scores may be used to fit redistribution given who played, never as statuses "known that morning" in a replay. From 2026-27 the recorder captures real statuses; refit on them after the season.

## 5. Matchups and win probability

- Weekly projected total per category = **already accumulated** total + projected remainder for players in active slots on the remaining days.
- Win probability per category comes from the projected difference and its uncertainty. Start with a normal approximation; move to simulation (bootstrapping each player's game logs) if calibration shows the normal model is off, especially for percentages and low-count categories like BLK and STL.
- Uncertainty shrinks as the week progresses. On Sunday night most of the total is already known, and the probabilities must reflect that.
- **Expected categories won** = sum of per-category win probabilities. **Matchup win probability** = probability of winning more categories than the opponent (a Poisson-binomial over categories, ties counted as Yahoo counts them).
- **Need weights:** a category you are sure to win or sure to lose gains nothing from more production; close categories gain the most. Score weekly moves by how much they raise expected categories won, not by raw z-score.

## 6. Usable games and streaming

- Raw games this week overstate a pickup. A game only counts if, on that day, there is an open active slot he can fill after your existing players are placed. On busy days (10+ NBA games) slots are full; on light days they are empty.
- Fill slots per day as an **assignment** of eligible players to slots (PG, SG, G, SF, PF, F, C, Util…), maximizing projected value. Greedy filling can miss a valid arrangement; with ~10 slots an exact assignment is cheap.
- Respect the weekly **add limit**. An add used Monday is not available Friday, so the ranker should consider when to add, not just whom.
- Show the **drop cost**. Dropping a good player for a 1-week stream is usually wrong; the gain must be net of the dropped player's rest-of-season value, and dropped players may be claimed by others.
- Yahoo lineups lock per game or per day depending on settings. A pickup added after his game has started does not score that day.

## 7. Punting

- A punt deliberately concedes a category so value goes into others. Common pairs are correlated: FT% with traditional centers, TO with high-usage guards, PTS with defensive role players, FG% with high-volume guards.
- Suggest punts from the team's category profile vs the league (where it already ranks low and is far from the middle), not from slogans. Show the trade-off: value gained elsewhere vs weeks likely lost in the punted category.
- Punts change valuations: with FT% punted, a big man's FT% impact no longer counts against him, so he rises in the rankings.
- Punts are stored per team. The Bulldozers and The Alternates can follow different strategies.

## 8. Recommendations must be explainable and logged

- Every recommendation carries **reasons with numbers**, ordered by impact: "4 usable games (3 on light days)", "you trail BLK 9–14 with 3 days left; he averages 1.8 BLK", "+0.42 expected categories won". If you cannot write the reason, the recommendation is not ready.
- Include the **counter-reason** when there is a real one ("costs 1 of your 2 remaining adds", "FT% 62% hurts a category you lead narrowly").
- Every recommendation is logged with a snapshot of the inputs it used, so it can be recomputed and scored later. The log records what the tool advised, what you did, and how it turned out.

## 9. Backtests and calibration

- **No look-ahead.** When replaying a past date, use only data available that morning: stats through the previous day, injury status as known then, rosters as they were. Leakage makes every model look great and is the most common backtest bug.
- Replay **walk-forward**, day by day, not one train/test split. The question we care about is "what would the tool have said that morning".
- Measure projection error per category (MAE and bias) and **calibration**: bucket predicted probabilities (50–60%, 60–70%, …) and compare to actual win rates. A model that says 70% must win about 70% of the time.
- **Baselines and the acceptance gate** (ADR 0010): compare every model with season average × games and with Yahoo's recorded ranks and projections. A model goes live only if it beats both on error and calibration; otherwise use the baseline and say so. The margins are an open decision.
- Prefer a simpler model that is calibrated over a clever one that is not.

## 10. Pre-draft rankings

- Rank by **season-long value** in each league: per-game z-values × expected games, over that league's pool and categories.
- Produce one ranking with no punt and one per punt build the user chooses; punted categories get weight 0.
- Season projections come from last season's rates, shrunk, and a minutes estimate with an uncertainty range. Show the range; a rookie or a player changing team is less certain than a veteran in the same role.
- The draft sheet is a cheat sheet, not a live board: no pick tracking.

## Common traps (quick check before you finish)

- Averaging percentages, or z-scoring FG% instead of FG impact.
- Counting raw games instead of usable games.
- Hardcoded 9-cat, roster slots or add limits.
- Ignoring stats already accumulated this week.
- `today()` or future data inside a projection or backtest.
- Ranking by total value for a weekly decision that should use need weights.
- Treating Questionable as certain to play, or Out as permanent.
- A recommendation without numbers in its reasons.
- A model shipped without beating the season-average and Yahoo baselines.
