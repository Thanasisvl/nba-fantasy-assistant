---
name: nfa-engineering
description: Engineering conventions for the NBA Fantasy Assistant codebase — layering, the five extension interfaces (platform, stats source, scoring format, notifier, store), Yahoo Fantasy API and nba_api adapters, OAuth and secrets, caching, resilience and data age, domain types, recommendation objects, the daily launchd job, the email digest, tests with fixtures, tooling and definition of done. Use this for any code change in this repo: new modules, data sources, Streamlit pages, jobs, refactors, reviews or debugging — even small fixes.
---

# Engineering conventions

The design goal is **growth without rewrites** (objective O4 in `docs/PLAN.md`): a new league is config; a new format, platform, data source or notifier is one new adapter. Most rules below protect that goal. When `docs/ARCHITECTURE.md` exists, it overrides layout details here; keep the two consistent.

| Reference | Read it when |
|---|---|
| `references/yahoo-api.md` | Touching Yahoo OAuth, league/team/player keys, endpoints, pagination, or Yahoo fixtures |
| `references/nba-api.md` | Touching `nba_api`: game logs, schedule, player IDs, throttling, failures |
| `references/domain-types.md` | Creating or changing domain types, interfaces, the recommendation object or the store schema |
| `references/testing.md` | Writing tests, recording fixtures, testing adapters, backtests or the daily job |

## 1. Layers and dependency direction

```
ui/ (Streamlit)    jobs/ (daily run, backfill)
          \            /
           services/              # use cases: board, matchup, streaming, digest, scorecard, health
               |
            domain/               # pure logic + types + interfaces (Protocols)
               ^
adapters/  platforms/  sources/  notifiers/  store/   # implement domain interfaces
```

- **Domain is pure:** no network, files, environment, clocks, randomness without a seed, or Streamlit. Inputs in, results out. That is what makes it testable and backtestable: a backtest is the domain run against historical inputs.
- Dependencies point inward. `domain` imports nothing from the other layers. Services depend on interfaces, not concrete adapters; a small composition module (e.g. `nfa/wiring.py`) builds the concrete objects.
- Pass the "as of" date and time in explicitly. Never call `date.today()` or `datetime.now()` inside domain or services; take it from the caller. Backtests replay dates by passing a different `as_of`.
- UI and jobs are thin. If a Streamlit page computes something, move it to a service so the digest and tests can reuse it.
- The package layout, interfaces, data model and flows are defined in `docs/ARCHITECTURE.md` (§4–§7). Put new code where the layout says; if it has no home there, update the architecture doc in the same change.

## 2. The five interfaces

Each is a `typing.Protocol` in `domain/interfaces.py`, implemented by adapters. The agreed signatures are in `docs/ARCHITECTURE.md` §5. Injury statuses are part of `StatsSource`; a composite source combines `nba_api` with the injury provider.

| Interface | v1 implementation | Later |
|---|---|---|
| `FantasyPlatform` | Yahoo | ESPN, Sleeper |
| `StatsSource` | `nba_api` | Yahoo stats fallback, licensed feed |
| `ScoringFormat` | H2H categories | points, roto |
| `Notifier` | email (SMTP) | Telegram, Slack |
| `Store` | local files (parquet + SQLite) | hosted DB |

- Adapters translate external shapes into domain types **at the boundary**. Yahoo JSON/XML and `nba_api` DataFrames never leak past the adapter.
- An adapter may only depend on its own external library plus the domain. Two adapters never call each other; services combine them.
- Adding an implementation must not require edits in domain code. If it does, the interface is wrong; fix the interface deliberately and note it in `docs/decisions/`.

## 3. Identity

- Every player has an internal `PlayerId`. The **crosswalk** maps Yahoo player key ↔ NBA person ID ↔ injury-source name, and is stored.
- Fuzzy name matching is allowed only in the crosswalk builder. Normalize (accents, suffixes like Jr./III, punctuation), match on name + team, then confirm ambiguous ones by hand via an overrides file (`data/crosswalk_overrides.json`, committed).
- Unmatched players appear on the health page, never silently dropped. A test asserts every rostered player in the fixtures resolves.
- Leagues, teams and seasons also get stable keys. Season is a value (`"2026-27"`), never implied by "now".

## 4. Adapters, caching and resilience

- **Cache every fetch.** Final box scores are immutable: fetch each game once. Re-fetch only what changes (schedule, injuries, rosters, free agents, matchups) and decide a max age per dataset.
- **Be polite:** throttle, set a timeout on every request, retry transient errors with exponential backoff and jitter (max ~3 tries), never retry auth errors.
- Every dataset carries `fetched_at` and `source`. A fetch returns either fresh data or a typed failure; the service falls back to the cache and records the failure for the health page. The UI and job never crash on a source failure.
- Show **data age** wherever data appears ("injuries as of 08:12"). The digest says when it used stale data.
- Unofficial sources will break. Keep each behind its adapter so a fix is local, and keep recorded fixtures of the last known good response to diagnose format changes.

## 5. Storage

- `data/` is gitignored except `data/crosswalk_overrides.json`. Parquet datasets under `data/cache/` (append-only, versioned, written atomically); records in `data/app.sqlite` (WAL mode). Full layout and tables: `docs/ARCHITECTURE.md` §6, ADR 0003.
- Schema changes go through numbered migrations (plain SQL files applied in order). Never edit a table by hand.
- A snapshot is a manifest of dataset versions plus git commit, model version and config hash, enough to recompute a recommendation without copying data.
- `Store.read_dataset(name, as_of)` is the single place that cuts off data after `as_of`; never filter by date ad hoc elsewhere.

## 6. Recommendations

- A recommendation is a frozen data object: action (add / drop / start / bench / punt), team and league, target players, expected impact, ordered `reasons` with numbers, optional counter-reasons, confidence, `as_of`, model version, snapshot ID. See `references/domain-types.md`.
- The UI and email only render recommendations; they never invent reasons or recompute values.
- The daily job writes every recommendation to the log **before** sending it, and later records the outcome (followed or not, result).

## 7. The daily job

- One entry point, `python -m nfa.jobs.daily`, triggered by launchd and runnable by hand with `--as-of` and `--dry-run` (no email, no log writes).
- Steps: refresh sources → build projections → per league and team: matchup, lineup check, streaming, opportunities → write log → render and send digest → record run. Each step records its own success, so a failure in one league does not stop the others.
- **Idempotent:** a run key per date prevents duplicate log entries and emails; re-running resumes from failed steps.
- launchd: use `StartCalendarInterval` (launchd runs a missed job when the Mac wakes). If the run happens after the first game lock, mark the digest late.
- Output a structured log line per step to `data/logs/` (rotated); the health page reads the last runs.

## 8. Yahoo, OAuth and secrets

- OAuth with the **read-only** scope. Never add code that changes anything on Yahoo; that is a backlog item needing its own design and safeguards.
- Tokens, client ID/secret and SMTP credentials live in the macOS Keychain (via `keyring`) or a gitignored file outside `src/`. Commit `config.example.toml` with placeholders.
- Never print, log or commit secrets. Redact `Authorization` headers and tokens from errors and recorded fixtures.
- Refresh tokens automatically; when refresh fails, the health page and digest say "Yahoo login needed" instead of failing silently.

## 9. Testing

Details and patterns in `references/testing.md`. In short:

- `pytest`, no network ever (enforce with a fixture that blocks sockets).
- Domain: small hand-built inputs, one focused test per rule, named after the behavior (`test_fg_pct_uses_summed_makes_and_attempts`).
- Adapters: parse recorded fixtures into domain types.
- Services: fake adapters implementing the interfaces.
- Backtests: a test proving data after `as_of` is invisible.

## 10. Tooling and style

- Python 3.12+, managed with `uv` (`pyproject.toml`, lockfile committed).
- `ruff` for lint and format, `pyright` (or `mypy --strict` on `domain/`) for types, `pytest` for tests. Run all three before calling work done.
- Type hints everywhere; frozen `dataclass`es for domain types; `Enum`s for fixed vocabularies (categories direction, slot types, statuses, actions).
- pandas/numpy are fine for bulk stats inside adapters and domain computations; convert to typed objects at module boundaries rather than passing loosely shaped DataFrames around.
- Small modules with one responsibility. A file past ~400 lines is probably doing two things.
- Comments explain why, not what. Docstrings on public functions state units (per game, per window, per 36).
- Logging via the standard `logging` module, not `print`, outside scripts.

## 11. Git and docs

- **Ask the user before every commit, push or merge**, showing what will be committed or pushed, and wait for an explicit yes. One approval covers one action.
- Branch per piece of work (`m1/crosswalk`, `m2/backtest-harness`), small commits with clear messages, merge to `main` when tests pass and the user approves.
- If a change alters a decision, requirement or milestone, update `docs/PLAN.md` (and `docs/ARCHITECTURE.md`) in the same change. Record significant design choices as short ADRs in `docs/decisions/NNNN-title.md` (context, decision, consequences).
- Build what the current milestone needs. Put good ideas in the plan's backlog instead of building them.

## Definition of done

- [ ] Behavior covered by tests; `pytest`, `ruff`, type checker all pass
- [ ] No network in tests; new external responses recorded as fixtures with secrets removed
- [ ] Domain code has no I/O and no implicit "now"
- [ ] New data shows its age; source failures degrade gracefully and appear on the health page
- [ ] Recommendations include numeric reasons and are logged with a snapshot
- [ ] Domain rules (skill `nba-fantasy-domain`) respected, especially ratio categories and usable games
- [ ] Docs updated if a decision or requirement changed
