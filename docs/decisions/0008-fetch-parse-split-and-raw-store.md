# 0008. Fetch/parse split and a raw store

Date: 2026-10-02 · Status: accepted (amends 0003)

## Context

Parsing on fetch loses information for good when the parser is wrong or drops a field that later matters. For data that cannot be fetched again (ADR 0007), that loss is permanent. Yahoo's JSON is deeply nested and poorly documented, so parser mistakes are likely early on.

## Decision

- Every source adapter has two halves: **fetch** (network, throttling, retries, timeouts) returning a `RawResponse`, and **parse** (a pure function) turning a `RawResponse` into normalized dataset rows.
- Responses for non-refetchable datasets are kept as compressed raw files (`data/raw/…`), listed in a `raw_files` table, append-only, kept indefinitely.
- Refetchable datasets (box scores, schedule, NBA player list) are parsed straight into datasets; their raw responses are not kept.
- Datasets derived from raw files can be rebuilt at any time (`rebuild` job).

## Consequences

- A parser fix found in March is replayed over the whole season with no data lost.
- Recorded raw files double as test fixtures for the parsers.
- The backtest's `as_of` cut-off is exact for recorded data: it sees what was on disk at that moment.
- One extra layer (raw store and parse step) and a few hundred MB per season.
