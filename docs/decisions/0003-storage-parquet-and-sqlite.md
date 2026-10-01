# 0003. Storage: parquet datasets plus SQLite records

Date: 2026-10-01 · Status: accepted

## Context

Two kinds of data: bulk, columnar, mostly append-only stats and snapshots (game logs, schedule, injuries, Yahoo rosters), and small relational records that need transactions and queries (crosswalk, recommendation log, predictions, outcomes, job runs, health, team preferences). Recommendations must be reproducible without copying data for each one.

## Decision

- Parquet datasets under `data/cache/`, append-only and versioned with metadata (`fetched_at`, source, content hash); written atomically (temporary file, then rename).
- One SQLite database (`data/app.sqlite`, WAL mode) for records, with numbered SQL migrations.
- A snapshot is a manifest of dataset versions plus git commit, model version and config hash.
- All access goes through the `Store` protocol.

## Consequences

- No database server; the whole store is a folder that is easy to back up or delete.
- Reading "as of" a past date is enforced in one place, which is where look-ahead is prevented and tested.
- If the tool is ever hosted, a new `Store` implementation is needed (e.g. Postgres plus object storage); services are unaffected.
