# 0005. Ports and adapters, with an explicit as_of

Date: 2026-10-01 · Status: accepted

## Context

The tool must grow without rewrites (new formats, platforms, sources, notifiers) and its projections must be backtested without look-ahead. Both fail if business logic is mixed with I/O or reads the current time itself.

## Decision

- Layers: domain (pure) ← services ← ui/jobs, with adapters implementing domain protocols (`FantasyPlatform`, `StatsSource`, `ScoringFormat`, `Notifier`, `Store`). An import-rule test enforces the direction.
- Every time-dependent call takes `as_of`. Only `clock.py`, used by ui, jobs and wiring, reads the real time.

## Consequences

- The backtest is the same domain code run with past `as_of` values and historical inputs.
- Adding an implementation does not touch domain code; if it would, the interface is changed deliberately and recorded here.
- Slightly more boilerplate (protocols, wiring) than a direct script, accepted for testability and longevity.
