# 0009. InjuryFeed is its own interface

Date: 2026-10-02 · Status: accepted (supersedes the injury part of 0004)

## Context

ADR 0004 put injuries inside `StatsSource` through a combined stats-and-injuries adapter. Injuries are now a separately recorded, high-value stream (ADR 0007) with their own schedule (snapshots every ~2 hours on game days), and the provider is still undecided.

## Decision

A sixth interface, `InjuryFeed`, produces the `injury_reports` dataset. `StatsSource` covers players, game logs and schedule only. The combined stats-and-injuries source is dropped. The provider (official NBA injury report, ESPN, or Yahoo status only) is chosen in the M0 spike.

## Consequences

- Changing the injury provider touches one adapter.
- The recorder can snapshot injuries without touching game logs.
- Six interfaces instead of five; still one Protocol each, no registry.
