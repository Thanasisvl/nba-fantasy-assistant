# 0002. Yahoo access is read-only

Date: 2026-10-01 · Status: accepted

## Context

The Yahoo Fantasy API can also change rosters, lineups and trades. Automating moves raises the cost of bugs from "bad advice" to "lost matchups", and needs approval flows and safeguards.

## Decision

Request only the Fantasy Sports **read** scope. No code path calls endpoints that change anything on Yahoo. The tool advises; I make the moves.

## Consequences

- A bug can never change a team.
- Following advice takes a few taps in the Yahoo app; the digest is designed to make that fast.
- One-click actions stay in the backlog and need a new decision (write scope, per-action approval, dry runs, audit log) before any work starts.
