# 0010. Baselines and an acceptance gate for models

Date: 2026-10-02 · Status: accepted

## Context

A complicated projection model can lose to simple rankings and still look convincing. Yahoo's own ranks and projections are what most opponents use, and the recorder now captures them daily (ADR 0007).

## Decision

- Every model is compared in the backtest with two baselines: **season averages** (per-game average × games) and **Yahoo's recorded ranks and projections**.
- A model goes live only if it beats both on projection error and calibration. Otherwise the baseline is used, and the UI says so.
- The margins required to "beat" a baseline are an open decision, agreed with me from backtest results.

## Consequences

- The Yahoo baseline exists only for seasons we recorded (2026-27 onwards); on last season's data only the season-average baseline applies.
- The scorecard page shows each model against its baselines.
