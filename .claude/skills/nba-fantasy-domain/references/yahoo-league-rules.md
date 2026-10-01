# Yahoo NBA league rules that affect the math

Commissioners can change most of these, so **read them from league settings** (`league/{league_key}/settings`); the values below are typical defaults for recognizing what you see, not values to code against. Verify anything marked (verify) during M0 against the real leagues.

## Scoring

- **Head-to-head categories:** each category is a separate win, loss or tie each week. Standings count category wins, losses and ties (ties usually count as half).
- Default 9 categories: FG%, FT%, 3PTM, PTS, REB, AST, ST, BLK, TO. Settings mark each category's sort direction; TO is lower-is-better.
- Settings also list categories that are **display only** (e.g. FGM/FGA, FTM/FTA). They are not scored but are exactly what we need to compute percentages. Do not treat display-only stats as scoring categories.

## Weeks and schedule

- Scoring weeks run Monday–Sunday. Some weeks are longer (around the All-Star break and the season start) (verify per season from the league's week dates).
- Playoffs occupy the last weeks of the fantasy season; the number of playoff teams and weeks are settings. Playoff weeks matter for trades and rest-of-season value in the second half.

## Roster and positions

- Typical slots: PG, SG, G, SF, PF, F, C, C, Util, Util, plus bench (BN) and injured (IL / IL+) slots (verify the exact default; always read `roster_positions`).
- Players have **eligible positions** (e.g. PG,SG,G,Util). G accepts PG or SG; F accepts SF or PF; Util accepts anyone. Eligibility can change during the season.
- IL slots accept players with an eligible injury status (IL: Out/INJ; IL+ may also accept Day-to-Day/GTD) (verify). A player in IL does not score and does not count against the active roster.

## Lineups

- **Daily lineups.** Starters for each day are set separately.
- Lock timing is a setting: lineups lock at each player's **game time**, or for the whole day at the first game (verify which your leagues use). After a player's game starts, his slot for that day is fixed.
- Players on bench score nothing even if they play. This is why usable games matter.

## Transactions

- **Max acquisitions per week** (adds): a setting; resets at the start of each scoring week. Some leagues also have a season maximum.
- **Waivers:** dropped players usually go on waivers for a period (often 2 days) before becoming free agents; leagues can use continual rolling lists or FAAB. Free agent status in the API distinguishes W (waivers) from FA. A waiver player cannot be streamed today.
- Trades have review periods and deadlines (settings). Trade analysis is a backlog item.

## Player status

- Yahoo statuses include GTD (game-time decision), DTD (day-to-day), O (out), INJ, SUSP and NA (verify the exact codes from the API). Map them to a probability of playing, not a yes/no.
- Yahoo's status can lag the official NBA injury report. Cross-check against the injury source and prefer the more recent one.

## Ownership

- `percent_owned` (and its recent change) is available per player. A fast rise is a signal that a pickup will not last on waivers; it is not a projection input.
