# Glossary

Use these terms consistently in code, UI and email.

| Term | Meaning |
|---|---|
| **H2H categories** | Head-to-head format where each category is won, lost or tied each week |
| **Category** | A scored stat in a league (PTS, REB, FG%, TO, …), with a sort direction |
| **Counting category** | A category that is a sum (PTS, REB, AST, ST, BLK, 3PTM, TO) |
| **Ratio category** | A category computed from summed numerator and denominator (FG%, FT%, A/TO) |
| **Impact** | `attempts × (pct − pool_pct)`: the contribution of a player to a ratio category |
| **Pool** | The players used to compute z-score means and spreads; roughly those who would be rostered |
| **Z-score** | Standardized value of a player in one category relative to the pool |
| **Replacement level** | Value of the best available free agent at a position in a given league |
| **Window** | A date range a projection covers: today, rest of week, rest of season |
| **Accumulated** | Stats already earned in the current matchup week |
| **Remaining** | Projected stats for the rest of the matchup week |
| **Active slot** | A lineup slot that scores (PG, SG, G, SF, PF, F, C, Util); not BN or IL |
| **Eligibility** | The positions a player may fill |
| **Usable game** | A game a player has on a day when he would be placed in an active slot |
| **Light day** | A day with few NBA games, when active slots are likely to be empty |
| **Back-to-back** | A team playing on consecutive days; a rest risk |
| **Stream** | Adding a player for his games this week, usually dropping him later |
| **Add limit** | Maximum acquisitions per scoring week |
| **Drop cost** | Rest-of-season value lost by dropping a player |
| **Need weight** | How much more production in a category is worth in this matchup |
| **Expected categories won** | Sum of per-category win probabilities for the week |
| **Punt** | Deliberately conceding a category to strengthen others |
| **Category profile** | A team's strength in each category relative to the league |
| **Probability of playing** | Chance a player plays a given game, from status and rest risk |
| **Calibration** | Whether predicted probabilities match observed frequencies |
| **Look-ahead** | Using data in a backtest that was not available at the replay date |
| **Recommendation** | An advised action (add, drop, start, bench, punt) with reasons and an input snapshot |
| **Snapshot** | The stored inputs a recommendation was computed from |
