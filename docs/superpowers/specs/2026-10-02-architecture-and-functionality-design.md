# Design revision: architecture and functionality

Date: 2026-10-02
Status: draft for review
Revises: `docs/PLAN.md`, `docs/ARCHITECTURE.md` (both on branch `docs/architecture`). Where this spec and those documents disagree, this spec wins; the implementation plan turns it into edits of those documents, the ADRs and the skills.

## 1. Intent

**Outcome.** A personal assistant for Yahoo NBA H2H categories leagues (the 12-team public league; the 6–8 team family league; maybe a 4-team league) that helps me win more category matchups with little daily effort, and that proves its advice works.

**Success criteria.**
- v1 is ready before the 2027-28 drafts (around early October 2027).
- Its advice is measured: every recommendation is logged and scored, and its probabilities are calibrated.
- Its models beat two simple baselines (season averages and Yahoo's own ranks and projections) before they are used.
- It runs daily without attention; failures are visible, never silent.

**Unchanged constraints.** Single user, local Mac, $0, Yahoo read-only, personal use of data, no EuroLeague-derived assumptions without asking, ask before any git commit or push.

## 2. Decisions made in this brainstorm

| # | Decision | Replaces |
|---|---|---|
| D1 | The 2026-27 season is a **test bed**. v1 targets the **2027-28** season. | v1 for this season |
| D2 | A **recorder** runs daily from shortly after M0 and captures: injury statuses, Yahoo league state (rosters, free agents with % owned, matchups, transactions), Yahoo ranks and projections, and my decisions (lineups, adds and drops). | Not planned |
| D3 | **Pre-draft rankings** per league and punt build are in v1 (M6). A live draft board stays in the backlog. | Draft assistant in backlog |
| D4 | I act mostly at the Mac: the **Streamlit app is the main product**, with a **Today** home page; the email is a short nudge. | Email as the primary surface (O2) |
| D5 | **Hybrid storage:** raw responses kept for data that cannot be fetched again; normalized parquet for the rest; raw-derived tables can be rebuilt. | Normalized-only storage |
| D6 | Adapters split into **fetch** (I/O, writes raw) and **parse** (pure). | Parse on fetch |
| D7 | The daily job has four steps: `record`, `build`, `advise`, `notify`. | One job with all steps |
| D8 | Injuries get their own interface, **`InjuryFeed`** (six interfaces in total). | Injuries inside a composite `StatsSource` |
| D9 | **Baselines and acceptance gate:** a model goes live only if it beats season averages and Yahoo's ranks and projections in the backtest. | No explicit baseline |
| D10 | **Shadow mode** from M4: advice is logged this season whether or not I follow it. | Logging from M4 daily loop only |
| D11 | **Weekly backup** of the raw store and SQLite to a folder I choose. | No backups |

Objective O2 ("under 5 minutes a day") now reads: *the Today page answers "what do I do today?" for every team in one screen; the email tells me when to open it.*

## 3. Scope and milestones

| # | Milestone | Delivers | Timing |
|---|---|---|---|
| M0 | Spike | Yahoo OAuth; settings; free agents; **Yahoo ranks and projections endpoints**; `nba_api`; injury source chosen; crosswalk prototype | Now |
| M1 | Recorder | Raw store and `raw_files` manifest; normalized parse step; crosswalk; launchd jobs `record` and `build` (morning run and game-day snapshots); job run records; minimal health page; weekly backup | As early in the season as possible |
| M2 | Foundation | Normalized datasets complete; schedule grid; player board; Today page skeleton | This season |
| M3 | Projections | Minutes and injury model; per-category projections; walk-forward backtest and calibration on last season; baselines | This season |
| M4 | Advice | Valuation; matchup projector; usable-games streaming; lineup check; reasons; full Today page; `advise` step in shadow mode | This season |
| M5 | Daily loop | `notify` (nudge email); injury opportunity alerts; recommendation log scoring; scorecard page | This season or spring |
| M6 | Strategy and draft | Punt analysis; pre-draft rankings and CSV export | Summer 2027 |
| — | Season-end review | Re-run the backtest on this season's recorded data (with real injury statuses); refit and agree model parameters | Summer 2027 |

**v1 scope:** everything in M0–M6. **Backlog** (unchanged except as noted): live draft board, multi-move weekly streaming plan, weekly league recap, what-if simulator, buy-low/sell-high, fantasy-playoff schedule strength, opponent profiling, IL slot manager, trade analyzer, AI chat, points/roto, ESPN/Sleeper, write actions.

## 4. System shape

```
            launchd                              me (Mac)
               |                                    |
   jobs/ record → build → advise → notify     ui/ Today + tool pages
               \____________________________________/
                              services/
                                 |
                              domain/      pure: types, interfaces, projections, valuation, matchups
                                 ^
 adapters/:  fetch (I/O) ──► raw store ──► parse (pure) ──► datasets (parquet) / records (SQLite)
```

- **Domain** is pure: no network, files, clock or unseeded randomness. `as_of` is passed in; only `clock.py` reads real time. An import-rule test enforces it.
- **Adapters** have two halves. *Fetch* does network, throttling, retries and timeouts, and writes each raw response with `fetched_at` and source. *Parse* is a pure function from a raw response to domain types. Box scores and the schedule may go straight to datasets (they can be fetched again).
- **Services** are the use cases (board, matchup, streaming, lineup, opportunities, digest, scorecard, health, draft sheet). UI and jobs stay thin.
- **One wiring module** builds the concrete objects.

**Interfaces** (`typing.Protocol` in `domain/interfaces.py`):

| Interface | v1 implementation |
|---|---|
| `FantasyPlatform` | Yahoo |
| `StatsSource` | `nba_api` (Yahoo stats as fallback) |
| `InjuryFeed` | Chosen in M0 |
| `ScoringFormat` | H2H categories |
| `Notifier` | Email (SMTP) |
| `Store` | Raw files + parquet + SQLite |

No plugin system or registry beyond these Protocols.

**Jobs:**

| Job | Does | From |
|---|---|---|
| `daily` | `record` → `build` → `advise` → `notify`; each step recorded and safe to re-run; `--as-of`, `--dry-run` | M1 (`record`, `build`), M4 (`advise`), M5 (`notify`) |
| `snapshot` | Injury and free-agent snapshots on game days | M1 |
| `backup` | Weekly archive of `data/raw` and `app.sqlite` | M1 |
| `rebuild` | Re-parse all raw data into datasets | M1 |
| `backfill` | Last season's box scores and schedule | M1 |
| `backtest` | Walk-forward replay and calibration | M3 |
| `login` | Yahoo OAuth | M0/M1 |
| `draft-sheet` | Pre-draft rankings | M6 |

## 5. Data and storage

| Tier | Holds | Format | Mutability |
|---|---|---|---|
| Raw | Injury reports; Yahoo rosters, free agents and % owned, matchups, transactions, ranks and projections, settings | `data/raw/{source}/{dataset}/{YYYY-MM-DD}/{HHMMSS}-{key}.json.gz`; one row per file in SQLite `raw_files` (source, dataset, request key, `fetched_at`, sha256, status) | Append only |
| Datasets | Box scores and game logs, schedule, players, injuries over time, league state over time, Yahoo ranks over time | Parquet in `data/datasets/{name}/`, partitioned by season | Box scores append only; raw-derived tables rebuildable |
| Records | Crosswalk, recommendations, snapshots, outcomes, job runs, source health, team preferences (punts), `raw_files` | `data/app.sqlite`, WAL, numbered migrations | Versioned rows, not edited in place |

- Every raw-derived row carries `observed_at`. `Store.read_dataset(name, as_of)` returns rows with `observed_at ≤ as_of` (box scores: `game_date < as_of`). It is the only look-ahead cut-off.
- A **snapshot** lists the raw-file IDs and dataset versions used, plus git commit, model version and config hash.
- **Recording frequency:** a full morning run (US/Eastern dates), plus injury and free-agent snapshots about every 2 hours on game days while the Mac is awake. Missed snapshots are recorded as gaps and shown on the health page.
- **Size:** a few hundred MB per season, compressed. Raw data is kept indefinitely.
- **Backups:** weekly; SQLite copied with its backup API; dated archives in a folder from `config.toml`; keep the last 8; the health page shows the last backup date.
- `data/` stays gitignored, except `data/crosswalk_overrides.json`.

## 6. Core logic

All numeric parameters are open until derived from NBA data and agreed with me (see §9).

- **Projections.** Expected minutes × per-minute rate per stat; makes and attempts for FG% and FT%. Rates are shrunk toward a prior (last season, or career for low-sample players), with weight *k* fitted in the backtest. Minutes model: recent minutes, role (starter flag), redistribution when teammates are out, probability of playing per game. This season these are fitted on last season's box scores with absences inferred; next summer they are refitted on recorded statuses.
- **Valuation.** Per-league z-scores over a pool of teams × active slots; ratio categories by impact = attempts × (pct − pool pct). Need-based weights per matchup. Punts set category weights to 0.
- **Matchups.** Weekly total per category = accumulated + projected remaining usable games. Per-category win probability by normal approximation (bootstrap as a check); categories won by Poisson-binomial.
- **Usable games and streaming.** Daily slot assignment with `linear_sum_assignment`. Pickup value = Δ expected categories won this week − drop cost λ, within the remaining weekly adds. v1 ranks single add/drop pairs.
- **Draft rankings.** Season-long z-values per league, for no punt and for chosen punt builds. Season projections from last season's rates (shrunk) and a minutes estimate with an uncertainty range.
- **Baselines and acceptance gate.** Each model is compared in the backtest with season averages and with recorded Yahoo ranks and projections. A model goes live only if it beats both on error and calibration; otherwise the baseline is used and the UI says so.
- **Recommendations.** Frozen objects: action, league and team, players, expected gain, confidence, top 3 reasons with numbers (and counter-reasons), `as_of`, snapshot ID, model version. UI and email only render them.

## 7. User interface, email and operations

**Streamlit pages:**

| Page | Contents | From |
|---|---|---|
| Today (home) | Per team: lineup issues; matchup by category with win probabilities and games left; top moves with reasons; injury opportunities; data age | M2 skeleton, M4 full |
| Player board | Filters by league, free agent/rostered, games this week; value under current punts | M2 |
| Schedule | Season grid of games per team per day; light days, back-to-backs; usable games for my rosters | M2 |
| Streaming | Ranked add/drop pairs with gain, adds left and reasons | M4 |
| Punts | Category profile vs league; suggested punts; ranking changes | M6 |
| Draft sheet | Rankings per league and punt build; CSV export | M6 |
| Scorecard | Recommendations vs outcomes; calibration buckets; model vs baselines | M5 |
| Health | Per source: last success, data age, errors; recorder gaps; last backup; Yahoo login state | M1 |

**Email (M5).** One short email per day: urgent items (lineup problems, new Outs on my rosters, opportunities), one line per matchup, a pointer to open the app, a health line only when something is wrong. Marked "late" if sent after the first game lock.

**Operations.** launchd schedules `daily` (morning, Eastern), `snapshot` (game days) and `backup` (weekly). All jobs catch up after sleep and can be re-run safely. Logs in `data/logs/`, rotated. On Yahoo refresh failure, jobs record "login needed" and continue with everything else; the health page and email show it. Secrets in the Keychain via `keyring`; `config.toml` gitignored, `config.example.toml` committed.

## 8. Testing

- `pytest` with sockets blocked; no test touches the network.
- Parsers tested on real recorded raw files, scrubbed of private data, stored as fixtures.
- Domain: small hand-built cases, one rule per test.
- Services: fake adapters implementing the Protocols.
- A look-ahead test proves rows after `as_of` are invisible.
- An import-rule test keeps the domain pure.
- `ruff` and `pyright` pass before work is called done.

## 9. Open items

**M0 verification** (unchanged from ARCHITECTURE.md §15, plus):
- Which Yahoo endpoints expose player ranks and projections, and in what form (season, rest-of-season, daily).
- Whether transactions and daily rosters are enough to reconstruct my own decisions (lineups, adds, drops).

**Model decisions** (to agree with me, from NBA data only): injury minutes redistribution (split, caps); shrinkage weights per stat; probability of playing per status and for back-to-backs; opportunity alert threshold; drop-cost λ; acceptance-gate margins; draft-season minutes estimate.

**Recording decisions** (to confirm in M1): exact snapshot hours on game days; backup destination folder.

## 10. Documents to update (in the implementation plan)

- `docs/PLAN.md`: decisions table, O2 wording, scope, FR changes (recorder FRs, draft rankings FRs, Today page, baselines, backups), milestones M0–M6, backlog.
- `docs/ARCHITECTURE.md`: system shape, fetch/parse split, `InjuryFeed`, jobs, storage tiers, flows (daily job steps, snapshot, rebuild, backup), traceability, open items.
- `docs/decisions/`: revise 0003 (storage) for raw tier; new ADRs for recorder-first sequencing (D1–D2), fetch/parse split (D6), `InjuryFeed` (D8), baselines and acceptance gate (D9).
- Skills `nfa-engineering` and `nba-fantasy-domain`, and `references/domain-types.md`: interfaces, storage, jobs, baselines.
- `README.md`: status, milestones, features.
