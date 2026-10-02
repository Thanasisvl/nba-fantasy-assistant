# 0004. nba_api as primary stats source, Yahoo stats as fallback

Date: 2026-10-01 · Status: accepted; injury part superseded by 0009

## Context

Projections need complete game logs with makes and attempts, minutes, and the full schedule. stats.nba.com (via `nba_api`) is the most complete free source but unofficial and sensitive to rate and IP. Yahoo's API has player stats with fewer details. Several injury sources exist with different reliability and formats.

## Decision

- `nba_api` is the primary source for players, game logs and schedule, used gently from my home IP with aggressive caching.
- Yahoo player stats by date are the fallback for recent game lines when `nba_api` fails.
- Injury statuses come through the separate `InjuryFeed` interface (ADR 0009); the provider is chosen in the M0 spike.

## Consequences

- The tool stays useful when stats.nba.com is down, with reduced detail shown as stale.
- Personal-use only: a commercial version would need a licensed feed, which is one new `StatsSource` adapter.
- Recorded fixtures of the last good responses help diagnose upstream format changes.
