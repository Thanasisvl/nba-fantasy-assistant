# Formulas and worked examples

Starting points, not final answers. Every constant here is a default to be tuned by the backtest harness (M2), and every change must be checked for calibration.

## Contents

1. Z-scores for counting stats
2. Z-scores for percentage stats (impact)
3. Pool selection
4. Shrinkage (early-season blending)
5. Window projections
6. Category win probability
7. Matchup win probability
8. Usable games
9. Stream gain
10. Calibration

---

## 1. Z-scores for counting stats

For category `c`, over the pool `P`:

```
mean_c = average of player per-game c over P
sd_c   = standard deviation of player per-game c over P
z_c(p) = (c(p) − mean_c) / sd_c          # flip sign if lower is better (TO)
```

Example (made-up numbers): pool BLK mean 0.6, sd 0.5. A player averaging 1.8 BLK has `z = (1.8 − 0.6) / 0.5 = 2.4`. A player with 2.0 TO when the pool mean is 1.5 and sd 0.8 has `z = −(2.0 − 1.5) / 0.8 = −0.63`.

## 2. Z-scores for percentage stats (impact)

```
pool_pct  = Σ makes over P / Σ attempts over P          # ratio of sums, not mean of ratios
impact(p) = attempts(p) × (pct(p) − pool_pct)          # per game
z_pct(p)  = (impact(p) − mean_impact) / sd_impact      # over P
```

Example: pool FT% = 78%.
- Player A: 10 FTA/g at 90% → impact = 10 × 0.12 = +1.2
- Player B: 1 FTA/g at 95% → impact = 1 × 0.17 = +0.17
- Player C: 8 FTA/g at 55% → impact = 8 × −0.23 = −1.84

B has the best percentage but barely matters; C sinks a team's FT%. This is why a center can be a great pick when FT% is punted.

Team FT% for a week is always `Σ FTM / Σ FTA` across all player-games that counted.

## 3. Pool selection

The pool should be the players who would actually be rostered.

```
size = teams × active (non-bench, non-IL) slots      # e.g. 12 × 10 = 120
1. rank all players by a simple value (e.g. z with pool = top 300)
2. take the top `size`, recompute mean/sd, recompute z
3. repeat 2 until the pool membership stops changing (usually 2–3 rounds)
```

Use per-league pools: a 6-team family league has a much shallower pool than the 12-team public league, so the same player is worth less there.

## 4. Shrinkage (early-season blending)

For a per-minute rate (or per-game value) with `n` current-season games:

```
blended = (n × current + k × prior) / (n + k)
```

- `prior` = last season's value; for rookies or big role changes, a role/position average.
- `k` is the number of games at which current and prior count equally. Stats that stabilize fast get a small `k`; noisy ones a large `k`. Reasonable starting points to tune: minutes 3–5, usage/points rate 8–12, rebounds 8–12, assists 10–15, steals/blocks 15–25, FT% and 3P% expressed in attempts (≈100+ attempts).
- These `k` values are placeholders for the NBA, not derived from data yet. Replace them with values tuned by the M2 backtest, and confirm the choice with the user. Do not take constants from the EuroLeague tool.

## 5. Window projections

```
per_game(p, stat) = proj_minutes(p) × rate(p, stat)
window(p, stat)   = Σ over p's games g in window of  P(plays g) × per_game(p, stat)
```

- `P(plays g)`: ~1.0 for healthy regulars; lower for Questionable / Day-to-Day; lower on the second night of a back-to-back for players with a rest history; 0 for Out.
- For a team's week, sum only over the games where the player is in an **active slot** (see usable games).

## 6. Category win probability

Normal approximation for counting stats:

```
D     = projected final(mine) − projected final(theirs)       # includes accumulated totals
var_D = Σ var of remaining player-games (mine) + same (theirs)
P(win) ≈ Φ( D / sqrt(var_D) )                                 # flip D for lower-is-better
```

- Per-game variance per player comes from game logs, shrunk toward a position average for small samples. Assume independence between player-games to start; correlation (same team, blowouts) is a later refinement.
- Ties in low-count categories (BLK, STL) are common. Use a continuity correction: `P(win) ≈ Φ((D − 0.5) / σ)`, `P(tie) ≈ Φ((D + 0.5)/σ) − Φ((D − 0.5)/σ)`.
- For percentages, simulate rather than approximate: sample remaining makes/attempts per player-game, add to accumulated totals, compute both percentages, count wins.
- When nothing remains (`var_D = 0`), the probability is 0, 0.5 (tie) or 1 from the actual totals.

Bootstrap alternative (handles everything consistently): for each simulation, draw each remaining player-game's stat line from that player's recent game logs (scaled to projected minutes), sum with accumulated totals, record which categories each side wins. 2,000–5,000 simulations is usually enough for stable probabilities.

## 7. Matchup win probability

With per-category win probabilities `p_1..p_n` (and tie probabilities if relevant):

```
expected categories won = Σ p_i
P(win matchup) = P(categories won > categories lost)
```

Compute the distribution of categories won with a Poisson-binomial (dynamic programming over categories, O(n²)), or read it straight from the simulation. Count ties the way the league does (Yahoo records them as ties, typically worth half a win in standings).

## 8. Usable games

For each remaining day `d` in the window:

```
players_d = my players with a game on d (and P(plays) > 0)
slots     = active slots from league settings (e.g. PG, SG, G, SF, PF, F, C, C, Util, Util)
assign players_d to slots, each player to one slot he is eligible for, maximizing Σ value
usable(p, d) = 1 if p is assigned a slot on d
```

- Value for the assignment = the player's per-game value with current need weights.
- Solve exactly: `scipy.optimize.linear_sum_assignment` on a players × slots matrix (ineligible pairs get a large cost), or a small brute force. ~10 slots × ~13 players is tiny.
- A candidate pickup's usable games = days where adding him changes the assignment so that he is placed (possibly displacing a worse player, in which case count only the net gain).

Example: a week where the free agent's team plays Mon, Wed, Thu, Sat. On Wed and Sat you already have 10 players with games for 10 slots, and he would only displace your worst starter by a small margin. Raw games = 4; usable games ≈ 2 (Mon, Thu), plus a small gain on Wed/Sat.

## 9. Stream gain

```
gain(add a, drop b) = E[categories won | roster − b + a] − E[categories won | roster]
                      − λ × rest_of_season_value_lost(b)
```

- The first part uses this week's simulation or normal model with usable games.
- `λ` turns rest-of-season value into the same units; tune it. In practice: dropping a top-100 player for a stream needs a very large weekly gain.
- Account for the add limit: if only 1 add remains, the best add today competes with the best add later in the week (compare expected gains by day).

## 10. Calibration

```
for each prediction (category or matchup) with probability q and outcome y ∈ {0,1}:
    put it in bucket floor(q × 10) / 10
for each bucket: compare mean(q) to mean(y), and count
Brier score = mean((q − y)²)        # lower is better; compare against a baseline model
```

- Report per bucket, with counts. Buckets with few predictions are noisy; do not tune to them.
- A well-calibrated model has mean(y) ≈ mean(q) in every bucket with enough data.
- Track the same table live from the recommendation log during the season.
