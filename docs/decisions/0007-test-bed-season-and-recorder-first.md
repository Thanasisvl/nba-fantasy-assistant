# 0007. 2026-27 is a test bed; the recorder comes first

Date: 2026-10-02 · Status: accepted

## Context

The 2026-27 season starts around 20 October 2026, before any advice can be built and validated. Some data can never be fetched later: injury statuses as they changed during the day, Yahoo free agents with % owned on a given day, Yahoo's own ranks and projections, and the decisions I made. Last season has none of it, which limits how honestly the injury and minutes model can be backtested.

## Decision

- v1 targets the 2027-28 season. 2026-27 is a test bed: each piece is tried in my leagues as it is built.
- Milestone M1 is a daily **recorder** that captures that data from as early in the season as possible.
- From M4, advice runs in **shadow mode**: logged whether or not I follow it.
- After the season, a review re-runs the backtest on the recorded data and the model parameters are refitted and agreed.

## Consequences

- No advice this season until M4; in exchange, next season's models are tested on real statuses, real waiver pools and real opponents.
- The recorder must be reliable and visible: gaps are recorded and shown on the health page, and the data is backed up weekly.
- Pre-draft rankings (M6) move into v1, because the 2027-28 draft is the first decision v1 faces.
