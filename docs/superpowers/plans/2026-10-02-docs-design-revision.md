# Docs Design Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `docs/PLAN.md`, `docs/ARCHITECTURE.md`, the ADRs, both project skills and the README in line with the approved design revision spec, and record the registered Yahoo app's settings.

**Architecture:** Documentation only; no code. Each task edits one document group, ends with a verification command (grep checks that the old design is gone and the new terms are present), and one commit. All work on branch `docs/design-revision`, merged to `main` through a PR (main is protected: PR required).

**Tech Stack:** Markdown, Mermaid (rendered by GitHub), git, `gh` (run as `env -u SSL_CERT_FILE gh …` on this Mac).

**Spec:** `docs/superpowers/specs/2026-10-02-architecture-and-functionality-design.md` (decisions D1–D11, §3 milestones, §4 system shape, §5 storage, §6 core logic, §7 UI and operations, §8 testing, §9 open items, §10 documents to update). Read it before starting; when this plan says "copy from spec §N", copy the text verbatim and adapt only tense and cross-references.

## Global Constraints

- **Ask the user before every `git commit`, `git push` and merge.** Show files and message; one approval covers one action. (CLAUDE.md, `~/.claude/CLAUDE.md`.)
- `main` is protected: changes reach it only through a PR. Never push to `main`.
- No EuroLeague-derived numbers or assumptions. Every model parameter stays an open decision.
- No secret values anywhere. Only the Keychain **names** are documented: service `nba-fantasy-assistant`, accounts `yahoo_client_id`, `yahoo_client_secret`, `yahoo_tokens`.
- Yahoo app facts (registered 2026-10-02): OAuth client type **Confidential Client**; permission **Fantasy Sports – Read** only; redirect URI **`https://localhost:8765/callback`**.
- Interfaces are six: `FantasyPlatform`, `StatsSource`, `InjuryFeed`, `ScoringFormat`, `Notifier`, `Store`.
- v1 targets the **2027-28** season; 2026-27 is a test bed.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the PR body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Writing style matches the existing docs: short sentences, tables for comparisons, plain words, no marketing tone.

## Review Focus

1. **Stale references to the old design** survive in some file (five interfaces, `composite.py`, `services/refresh.py`, `data/cache/`, `oob`, `8080`, "Draft assistant" in the backlog, email as primary surface). Expected: none remain outside `docs/superpowers/`. Pinned by the grep checks in Tasks 2–7 and the sweep in Task 8.
2. **A Mermaid diagram fails to render** on GitHub after editing. Expected: every diagram renders. Pinned by Task 8 Step 3 (check each diagram in the PR's rich diff).
3. **Inferred absences contradict the no-look-ahead rule.** ARCHITECTURE §7.4 says inferring statuses from who did not play is look-ahead; spec §6 fits minutes redistribution on last season's box scores with absences inferred. Expected: the docs say inferred absences are used **only to fit redistribution given who played**, never as morning-of statuses in a replay. Pinned by Task 4 Step 4 and Task 6 Step 2.
4. **Secret values leak into docs.** Expected: only Keychain names appear. Pinned by Task 8 Step 2 (grep for the client-ID prefix `dj0y` and 40-hex strings).
5. **New requirements without a home.** FR-L*, FR-M*, FR-E0, FR-G3, FR-J4, FR-X3 must each appear in ARCHITECTURE §14. Pinned by Task 4 Step 8.

---

## File map

| File | Change |
|---|---|
| `docs/decisions/0003-storage-parquet-and-sqlite.md` | Amend: raw tier, `data/datasets/` |
| `docs/decisions/0004-nba-api-primary-yahoo-stats-fallback.md` | Amend: injuries move to `InjuryFeed` (ADR 0009) |
| `docs/decisions/0005-ports-and-adapters-with-as-of.md` | Amend: six interfaces |
| `docs/decisions/0006-own-yahoo-oauth-module.md` | Amend: Yahoo app registration facts |
| `docs/decisions/0007-test-bed-season-and-recorder-first.md` | Create |
| `docs/decisions/0008-fetch-parse-split-and-raw-store.md` | Create |
| `docs/decisions/0009-injury-feed-interface.md` | Create |
| `docs/decisions/0010-baselines-and-acceptance-gate.md` | Create |
| `docs/PLAN.md` | Decisions, objectives, scope, FRs, risks, milestones, backlog, next step |
| `docs/ARCHITECTURE.md` | All sections touched by the spec |
| `.claude/skills/nfa-engineering/SKILL.md` | Interfaces, layers, storage, jobs, Yahoo, testing, DoD |
| `.claude/skills/nfa-engineering/references/domain-types.md` | Interface sketch → six + raw types |
| `.claude/skills/nfa-engineering/references/yahoo-api.md` | App registration, ranks endpoints |
| `.claude/skills/nfa-engineering/references/testing.md` | Raw fixtures, parser tests |
| `.claude/skills/nba-fantasy-domain/SKILL.md` | Projections data, baselines, draft rankings |
| `README.md` | Status, milestones, features, repo guide |

---

### Task 1: Branch and decision records

**Files:**
- Create: `docs/decisions/0007-test-bed-season-and-recorder-first.md`, `0008-fetch-parse-split-and-raw-store.md`, `0009-injury-feed-interface.md`, `0010-baselines-and-acceptance-gate.md`
- Modify: `docs/decisions/0003-…`, `0004-…`, `0005-…`, `0006-…`

**Interfaces:**
- Produces: ADR numbers 0007–0010 that Tasks 2–7 cite by number.

- [ ] **Step 1: Create the branch**

```bash
git switch main && git pull --ff-only && git switch -c docs/design-revision
```
(`git pull --ff-only` updates local `main`; ask the user before running it, as it is a merge.)

- [ ] **Step 2: Create `0007-test-bed-season-and-recorder-first.md`**

```markdown
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
```

- [ ] **Step 3: Create `0008-fetch-parse-split-and-raw-store.md`**

```markdown
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
```

- [ ] **Step 4: Create `0009-injury-feed-interface.md`**

```markdown
# 0009. InjuryFeed is its own interface

Date: 2026-10-02 · Status: accepted (supersedes the injury part of 0004)

## Context

ADR 0004 put injuries inside `StatsSource` through a composite adapter. Injuries are now a separately recorded, high-value stream (ADR 0007) with their own schedule (snapshots every ~2 hours on game days), and the provider is still undecided.

## Decision

A sixth interface, `InjuryFeed`, produces the `injury_reports` dataset. `StatsSource` covers players, game logs and schedule only. The composite source is dropped. The provider (official NBA injury report, ESPN, or Yahoo status only) is chosen in the M0 spike.

## Consequences

- Changing the injury provider touches one adapter.
- The recorder can snapshot injuries without touching game logs.
- Six interfaces instead of five; still one Protocol each, no registry.
```

- [ ] **Step 5: Create `0010-baselines-and-acceptance-gate.md`**

```markdown
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
```

- [ ] **Step 6: Amend 0003, 0004, 0005, 0006**

In `0003-storage-parquet-and-sqlite.md`:
- Status line → `Date: 2026-10-01 · Status: accepted, amended 2026-10-02 by 0008`
- In Decision, replace `Parquet datasets under \`data/cache/\`` with `Parquet datasets under \`data/datasets/\``.
- Append:

```markdown
## Amendment (2026-10-02, ADR 0008)

A third tier holds **raw responses** for data that cannot be fetched again (`data/raw/{source}/{dataset}/{YYYY-MM-DD}/{HHMMSS}-{key}.json.gz`, listed in the `raw_files` table). Datasets derived from raw files carry `observed_at` and can be rebuilt. `data/raw` and `app.sqlite` are backed up weekly to a folder set in `config.toml`.
```

In `0004-nba-api-primary-yahoo-stats-fallback.md`:
- Status line → `Date: 2026-10-01 · Status: accepted; injury part superseded by 0009`
- Replace the third Decision bullet with: `- Injury statuses come through the separate \`InjuryFeed\` interface (ADR 0009); the provider is chosen in the M0 spike.`

In `0005-ports-and-adapters-with-as-of.md`:
- Status line → `Date: 2026-10-01 · Status: accepted, amended 2026-10-02`
- Replace the protocol list with `(\`FantasyPlatform\`, \`StatsSource\`, \`InjuryFeed\`, \`ScoringFormat\`, \`Notifier\`, \`Store\`; see ADR 0009)` and append to that bullet: `Source adapters are split into fetch and pure parse halves (ADR 0008).`

In `0006-own-yahoo-oauth-module.md`, append:

```markdown
## Yahoo app registration (2026-10-02)

- OAuth client type: **Confidential Client** (the code flow with client secret described above).
- Permissions: **Fantasy Sports – Read** only.
- Redirect URI: **`https://localhost:8765/callback`** (8765 avoids Streamlit's 8501 and the common 8080). M0 decides between a local listener on that port and pasting the redirected URL.
- Keychain: service `nba-fantasy-assistant`; accounts `yahoo_client_id`, `yahoo_client_secret`, and `yahoo_tokens` (written by the login job).
```

- [ ] **Step 7: Verify**

```bash
ls docs/decisions && grep -l "Status: accepted" docs/decisions/*.md | wc -l && grep -n "composite\|data/cache" docs/decisions/*.md
```
Expected: ten files 0001–0010; count `10`; the final grep prints nothing.

- [ ] **Step 8: Commit (ask the user first)**

```bash
git add docs/decisions
git commit -m "Record design revision decisions (ADRs 0007-0010, amend 0003-0006)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: PLAN.md

**Files:**
- Modify: `docs/PLAN.md`

**Interfaces:**
- Consumes: ADRs 0007–0010.
- Produces: FR IDs used by ARCHITECTURE §14 (Task 4): FR-A4 (amended), FR-B2 (amended), FR-E0, FR-F1 (amended), FR-G3, FR-J4, FR-L1–L5, FR-M1–M3, FR-X3.

- [ ] **Step 1: Header**

`Status:` → `Status: design revised 2026-10-02 (spec in docs/superpowers/specs/); M0 spike next.` · `Last updated: 2026-10-02`.

- [ ] **Step 2: Decisions table** — replace these rows and add the new ones:

| Topic | Decision |
|---|---|
| Automation | Advise only; read-only on Yahoo; I make the moves. |
| Interface | Streamlit, local. The **Today** page is the main surface. Core logic separate so a web front end can replace it later. |
| Digest channel | Email, as a short daily nudge. |
| Timeline | 2026-27 is a test bed; v1 targets the 2027-28 drafts (ADR 0007). |
| Data collection | Daily recorder from M1: injuries, Yahoo league state, Yahoo ranks and projections, my decisions (ADR 0007). |
| Storage | Raw responses + parquet datasets + SQLite records (ADRs 0003, 0008). Weekly backup. |
| Yahoo OAuth | Own small module; Confidential Client; redirect `https://localhost:8765/callback`; credentials and tokens in the Keychain, service `nba-fantasy-assistant` (ADR 0006). |
| Injury source | `InjuryFeed` interface; provider chosen in the M0 spike (ADR 0009). |
| Model acceptance | Models must beat season averages and Yahoo's ranks in the backtest (ADR 0010). |

- [ ] **Step 3: Objectives** — O2 row becomes: `| O2 | Under 5 minutes a day of management | The Today page answers "what do I do today?" for every team in one screen; the email says when to open it |`

- [ ] **Step 4: Scope**

- In v1: `Yahoo, H2H categories, multiple leagues and teams, read-only, local Streamlit with a Today page, daily nudge email, daily recorder and weekly backup, recommendation log (shadow mode from M4), schedule planner, injury opportunity alerts, backtest and calibration harness with baselines, punt analysis, pre-draft rankings.`
- Not in v1: replace `draft assistant` with `live draft board`.

- [ ] **Step 5: Functional requirements** — edit and add:

- FR-A4 → `Read rosters, current matchup and opponent, free agents with % owned, recent transactions, and Yahoo's player ranks and projections.`
- FR-B2 → `Injury status through the \`InjuryFeed\` interface (provider chosen in M0), cross-checked against Yahoo's flag.`
- Add at the top of E: `- FR-E0: **Today** page (home), per team: lineup issues; matchup by category with win probabilities and games left; top moves with reasons; injury opportunities; data age.`
- Heading `### F. Daily digest` → `### F. Daily email`.
- FR-F1 → `One short email per day: urgent items (lineup problems, new Outs on my rosters, opportunities), one line per matchup, a pointer to open the app, and a health line only when something is wrong.`
- Add to G: `- FR-G3: Shadow mode: from M4, every recommendation is logged whether or not I follow it.`
- Add to J: `- FR-J4: Every model is compared with season averages and recorded Yahoo ranks and projections; it goes live only if it beats both on error and calibration, otherwise the baseline is used and the UI says so.`
- New group after K:

```markdown
### L. Recorder
- FR-L1: Keep raw responses for data that cannot be fetched again: injury reports; Yahoo settings, rosters, free agents with % owned, matchups, transactions, ranks and projections.
- FR-L2: A full morning run (US/Eastern dates) plus injury and free-agent snapshots about every 2 hours on game days while the Mac is awake. Missed snapshots are recorded as gaps.
- FR-L3: Raw files are append-only and kept indefinitely; datasets derived from them can be rebuilt.
- FR-L4: Record my decisions: daily rosters and lineups, and transactions, for my teams.
- FR-L5: Weekly backup of `data/raw` and `app.sqlite` to a configured folder; keep the last 8; show the last backup date on the health page.

### M. Draft rankings
- FR-M1: Pre-draft rankings per league: season-long values for no punt and for each punt build I choose.
- FR-M2: Season projections from last season's rates (shrunk) and a minutes estimate with an uncertainty range.
- FR-M3: Export rankings to CSV.
```

- Add to Cross-cutting: `- FR-X3: Data that cannot be fetched again is never lost silently: gaps and failures appear on the health page.`

- [ ] **Step 6: Risks** — add two rows:

| Risk | Mitigation |
|---|---|
| Mac asleep or off: recorder misses snapshots | launchd catches up on wake; gaps recorded and shown; accept some gaps |
| Recorded data lost (disk, accidental delete) | Weekly backup outside the repo; last backup date on the health page |

- [ ] **Step 7: Milestones** — replace the table and the sentence below it with spec §3's table (M0–M6 and the season-end review, with the "Timing" column) followed by: `M1 is time-critical: every day before the recorder runs is data that cannot be recovered.`

- [ ] **Step 8: Backlog** — replace `Draft assistant for next season` with `Live draft board (pick tracking during the draft)`; add `Multi-move weekly streaming plan`.

- [ ] **Step 9: Next step** — keep the M0 text; replace the "Before it starts (me)" line with `Done 2026-10-02: Yahoo Developer app registered (ADR 0006). Still before M0: join the public league; set up the family league (8 teams preferred, avoid an odd number).` Add to the M0 list: `Yahoo ranks and projections endpoints; whether transactions and daily rosters reconstruct my decisions.`

- [ ] **Step 10: Verify**

```bash
grep -nE "FR-(E0|G3|J4|L[1-5]|M[1-3]|X3)" docs/PLAN.md | wc -l; grep -niE "draft assistant|five interfaces" docs/PLAN.md
```
Expected: `12`; second grep prints nothing.

- [ ] **Step 11: Commit (ask the user first)**

```bash
git add docs/PLAN.md
git commit -m "Update plan for test-bed season, recorder and draft rankings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: ARCHITECTURE.md — structure (§1–§5)

**Files:**
- Modify: `docs/ARCHITECTURE.md:1-208`

**Interfaces:**
- Produces (used by Tasks 4, 5): types `RawResponse`, `FetchRequest`, `RecordScope`, `DatasetRows`; protocols `Fetcher`, `Parser`; services `record.py`, `build.py`, `today.py`, `draft_sheet.py`, `backup.py`; jobs `daily`, `snapshot`, `backup`, `rebuild`, `backfill`, `backtest`, `login`, `draft_sheet`.

- [ ] **Step 1: Header** — Status line: `Status: v1 design, revised 2026-10-02 (spec: docs/superpowers/specs/2026-10-02-architecture-and-functionality-design.md). Sections marked **(M0)** will be revised with the spike's findings.` · `Last updated: 2026-10-02`.

- [ ] **Step 2: §1 Drivers** — after the objectives paragraph add: `**Season plan:** 2026-27 is a test bed; v1 targets the 2027-28 season (ADR 0007). Data that cannot be fetched again is recorded from M1.` Add to Constraints: `the Mac sleeps, so recording has gaps that must be visible.`

- [ ] **Step 3: §2 System context** — in the Mermaid block: app label `NBA Fantasy Assistant<br/>Streamlit app + jobs`; store label `Local store<br/>raw + parquet + SQLite`; add node `backup[(Backup folder<br/>iCloud Drive or disk)]` inside `mac` with edge `store -- weekly --> backup`; change the SMTP edge label to `daily nudge`; add edge `app -- ranks, projections,<br/>transactions --> yahoo`.

- [ ] **Step 4: §3 Runtime view** — replace the table with:

| Entry point | Started by | Does |
|---|---|---|
| **Streamlit app** (`nfa.ui.app`) | Me, on demand | Reads the store; Today page and tool pages; can trigger a `record` + `build` for one league |
| **Daily** (`python -m nfa.jobs.daily`) | launchd, each morning ET; or by hand | `record` → `build` → `advise` (M4) → `notify` (M5); each step recorded and safe to re-run; `--as-of`, `--dry-run` |
| **Snapshot** (`nfa.jobs.snapshot`) | launchd, about every 2 h on game days | `record` + `build` for injuries and free agents only |
| **Backup** (`nfa.jobs.backup`) | launchd, weekly | Archives `data/raw` and `app.sqlite` to the backup folder; keeps the last 8 |
| **Rebuild** (`nfa.jobs.rebuild`) | Me, after a parser fix | Re-parses all raw files into datasets |
| **Backfill** (`nfa.jobs.backfill`) | Me, once per season | Last season's box scores and schedule |
| **Backtest** (`nfa.jobs.backtest`) | Me | Walk-forward replay, calibration, baselines |
| **Login** (`nfa.jobs.login`) | Me, once and when Yahoo asks | Yahoo OAuth; tokens to the Keychain |
| **Draft sheet** (`nfa.jobs.draft_sheet`) | Me, before drafts (M6) | Pre-draft rankings per league and punt build; CSV |

Replace "Both the app and the job call the same **services**." with "The app and all jobs call the same **services**." Add to the concurrency paragraph: `Raw files are written to a temporary name and renamed, then listed in \`raw_files\` in the same transaction as their job step.`

- [ ] **Step 5: §4 Components** — in the Mermaid block: `jobs[jobs — daily, snapshot, backup, rebuild, backfill, backtest, login, draft_sheet]`; `adapters[adapters — fetch + parse per source; email; store]`. Add a dependency rule: `- **Parse functions are pure**: they take a \`RawResponse\` and return \`DatasetRows\`, with no I/O and no clock; the import-rule test treats \`adapters/*/parse.py\` like \`domain\` (stdlib, pandas and \`domain\` only).`

Replace the package layout block with:

```
src/nfa/
  domain/
    types.py            League, LeagueSettings, Category, Player, StatLine, Projection, Recommendation, …
    raw.py              RawResponse, FetchRequest, RecordScope, DatasetRows
    datasets.py         row types and schemas for every normalized dataset (the contract adapters must produce)
    interfaces.py       Fetcher, Parser, FantasyPlatform, StatsSource, InjuryFeed, ScoringFormat, Notifier, Store
    identity.py         name normalization and matching rules used by the crosswalk builder
    minutes.py          minutes model, injury redistribution, probability of playing
    projections.py      rates, shrinkage, window projections
    baselines.py        season-average baseline; comparison against Yahoo ranks; acceptance gate
    scoring/h2h_categories.py   ScoringFormat for H2H categories: z-scores, impact, matchup outlook
    usable_games.py     daily slot assignment
    streaming.py        stream gain, add-limit timing, drop cost
    lineup.py           lineup checks
    punt.py             category profile, punt suggestions
    draft.py            season-long values per punt build
    calibration.py      buckets, Brier score, projection error
    reasons.py          builds ordered reasons from computed contributions
  services/
    record.py           run fetchers for a RecordScope; keep raw where required; record gaps and health
    build.py            parse unparsed raw files and refetchable responses into datasets; rebuild
    crosswalk.py        build and update the player ID crosswalk
    context.py          assemble a LeagueContext (settings, rosters, projections) for an as_of
    today.py            the Today page view per team
    board.py  matchup.py  streaming.py  lineup.py  opportunities.py  punt.py  draft_sheet.py
    digest.py           collect urgent items and render the nudge email
    scorecard.py        outcomes, calibration and baselines from the log
    backtest.py         walk-forward replay
    backup.py           archive raw files and SQLite
    health.py
  adapters/
    platforms/yahoo/    auth.py (own OAuth module), fetch.py, parse.py
    sources/nba_api/    fetch.py, parse.py
    sources/injuries/<provider>/   fetch.py, parse.py (one provider, chosen in M0)
    notifiers/email_smtp.py
    store/local.py      raw files + parquet datasets + SQLite; store/migrations/0001_init.sql, …
  jobs/   daily.py  snapshot.py  backup.py  rebuild.py  backfill.py  backtest.py  login.py  draft_sheet.py
  ui/     app.py  pages/ (today, board, schedule, streaming, punt, draft, scorecard, health)
  wiring.py   config.py   clock.py
tests/   unit/  adapters/  services/  backtest/  fixtures/raw/  test_architecture.py
scripts/ spike/  scrub_fixture.py  crosswalk_audit.py
```

- [ ] **Step 6: §5 Interfaces** — replace the code block with:

```python
# domain/raw.py
RawFileId = NewType("RawFileId", str)

@dataclass(frozen=True)
class FetchRequest:
    source: str            # "yahoo", "nba_api", "injuries:<provider>"
    dataset: str           # "rosters", "free_agents", "game_logs", …
    key: str               # e.g. "466.l.12345.t.3;date=2026-10-21"
    params: Mapping[str, str]

@dataclass(frozen=True)
class RawResponse:
    request: FetchRequest
    fetched_at: datetime   # timezone-aware
    status: int
    payload: bytes         # body as received

@dataclass(frozen=True)
class RecordScope:
    as_of: datetime
    kind: Literal["full", "snapshot"]     # snapshot = injuries + free agents only
    leagues: Sequence[LeagueKey]

@dataclass(frozen=True)
class DatasetRows:
    dataset: str           # a name from domain/datasets.py
    rows: Sequence[Any]    # row type defined for that dataset in domain/datasets.py
    observed_at: datetime

# domain/interfaces.py
class Fetcher(Protocol):
    source: str
    retain_raw: frozenset[str]                                   # datasets whose raw responses are kept
    def requests(self, scope: RecordScope) -> list[FetchRequest]: ...   # pure: what to fetch
    def fetch(self, request: FetchRequest) -> RawResponse: ...          # network; raises FetchError

class Parser(Protocol):
    source: str
    def parse(self, raw: RawResponse) -> list[DatasetRows]: ...         # pure

class FantasyPlatform(Fetcher, Parser, Protocol):
    name: str              # "yahoo"; produces league_settings, teams, rosters, matchups,
                           # transactions, available_players, player_ranks, platform_players

class StatsSource(Fetcher, Parser, Protocol):
    name: str              # produces nba_players, game_logs, schedule

class InjuryFeed(Fetcher, Parser, Protocol):
    name: str              # produces injury_reports

class ScoringFormat(Protocol):
    name: str                                                   # "h2h_categories"
    def player_values(self, projections: Sequence[Projection], settings: LeagueSettings,
                      weights: Mapping[str, float] | None = None) -> dict[PlayerId, Valuation]: ...
    def matchup_outlook(self, mine: WeekState, theirs: WeekState,
                        settings: LeagueSettings) -> MatchupOutlook: ...
    def move_gain(self, before: MatchupOutlook, after: MatchupOutlook) -> float: ...

class Notifier(Protocol):
    def send(self, message: Message) -> None: ...               # subject, html, text

class Store(Protocol):
    # raw tier
    def write_raw(self, raw: RawResponse) -> RawFileId: ...
    def unparsed_raw(self, source: str | None = None) -> Iterator[tuple[RawFileId, RawResponse]]: ...
    def all_raw(self, source: str | None = None) -> Iterator[tuple[RawFileId, RawResponse]]: ...
    def mark_parsed(self, ids: Sequence[RawFileId], build_id: str) -> None: ...
    # datasets (parquet)
    def write_dataset(self, data: DatasetRows, meta: DatasetMeta) -> DatasetVersion: ...
    def read_dataset(self, name: str, as_of: datetime | None = None) -> tuple[Any, DatasetMeta] | None: ...
    # records (SQLite)
    def crosswalk(self) -> Crosswalk: ...
    def save_crosswalk(self, entries: Sequence[CrosswalkEntry]) -> None: ...
    def team_prefs(self, team: TeamKey) -> TeamPrefs: ...
    def save_team_prefs(self, prefs: TeamPrefs) -> None: ...
    def save_snapshot(self, snapshot: Snapshot) -> str: ...
    def log_recommendations(self, recs: Sequence[Recommendation]) -> None: ...
    def log_predictions(self, preds: Sequence[Prediction]) -> None: ...
    def record_outcomes(self, outcomes: Sequence[Outcome]) -> None: ...
    def record_run(self, run: JobRun) -> None: ...
    def record_health(self, event: HealthEvent) -> None: ...
    def backup(self, dest: Path, keep: int) -> Path: ...
```

Replace the Notes list with:

- `- **Source adapters are a fetcher plus a parser** (ADR 0008). The contract between an adapter and the rest of the system is the set of datasets it produces, with row types in \`domain/datasets.py\`. A new platform (ESPN) produces the same datasets.`
- `- **Injuries have their own interface** (\`InjuryFeed\`, ADR 0009).`
- keep the existing `ScoringFormat` and `Store` notes; change the Store note's first words to `**\`Store\`** is one facade over three kinds of storage (raw files, parquet, SQLite).`

- [ ] **Step 7: Verify**

```bash
sed -n 1,260p docs/ARCHITECTURE.md | grep -nE "composite|refresh\.py|five|InjuryFeed|RawResponse|retain_raw" 
```
Expected: no `composite`, `refresh.py` or `five`; `InjuryFeed`, `RawResponse`, `retain_raw` present.

- [ ] **Step 8: Commit (ask the user first)**

```bash
git add docs/ARCHITECTURE.md
git commit -m "Architecture: fetch/parse adapters, InjuryFeed, new jobs and layout

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: ARCHITECTURE.md — data, flows and the rest (§6–§15)

**Files:**
- Modify: `docs/ARCHITECTURE.md` (from `## 6. Data model and storage` to the end)

**Interfaces:**
- Consumes: names from Task 3; FR IDs from Task 2.

- [ ] **Step 1: §6 Entities** — add rows:

| Entity | Key | Holds |
|---|---|---|
| RawFile | raw_file_id | source, dataset, request key, `fetched_at`, path, sha256, status, parsed build id |
| PlayerRank | league + player_id + observed_at | Yahoo rank and projection values as shown that day |
| Transaction | league + transaction id | type (add, drop, trade), team, players, time |

Change InjuryStatus key to `player_id + observed_at` and add `published_at` to its "Holds" column.

- [ ] **Step 2: §6 Where things live** — replace the tree with:

```
data/                          gitignored (except data/crosswalk_overrides.json)
  raw/{source}/{dataset}/{YYYY-MM-DD}/{HHMMSS}-{key}.json.gz   append-only, kept indefinitely
  datasets/
    nba_players/season=2026-27/…parquet
    game_logs/season=2026-27/…parquet        immutable once games are final
    schedule/season=2026-27/…parquet
    injury_reports/season=2026-27/…parquet   rebuilt from raw
    yahoo/<dataset>/season=2026-27/…parquet  league_settings, teams, rosters, matchups,
                                             transactions, available_players, player_ranks
  app.sqlite                    WAL mode
  logs/                         rotated structured logs
data/crosswalk_overrides.json   committed: manual fixes for ambiguous matches
<backup folder from config>/nfa-backup-YYYY-MM-DD.tar.gz   last 8 kept
```

Replace the two bullets under it with:
- `- **Raw** for responses that cannot be fetched again (ADR 0008). Each file is listed in \`raw_files\`.`
- `- **Parquet** for normalized datasets. Raw-derived rows carry \`observed_at\`; box scores carry \`game_date\`.`
- keep the SQLite bullet, adding `raw_files` to its list.

- [ ] **Step 3: §6 Snapshots and SQLite** — in "Snapshots without copying data" change "the dataset versions used" to "the raw-file IDs and dataset versions used". In the `erDiagram`, add:

```
    raw_files {
        text raw_file_id PK
        text source
        text dataset
        text request_key
        text fetched_at
        text path
        text sha256
        int status
        text parsed_build_id
    }
```

- [ ] **Step 4: §7 flows**

Replace §7.1's diagram with:

```mermaid
sequenceDiagram
    participant L as launchd
    participant J as jobs.daily
    participant R as services.record
    participant B as services.build
    participant A as advice services
    participant S as Store
    participant D as services.digest
    participant N as Notifier

    L->>J: start (or I run it with --as-of / --dry-run)
    J->>S: run_key = date; skip steps already ok today
    J->>R: record(scope = full, as_of)
    R->>S: write_raw (retained datasets) + health events; gaps recorded
    J->>B: build()
    B->>S: parse unparsed raw + refetchable responses → write datasets
    opt from M4 (shadow mode)
        loop each league and my team
            J->>A: lineup check, matchup outlook, streaming, opportunities
            A-->>J: recommendations + predictions (with reasons)
            J->>S: save snapshot, log recommendations and predictions
        end
        J->>S: score yesterday's outcomes
    end
    opt from M5
        J->>D: render nudge (urgent items, one line per matchup, health if broken)
        D->>N: send (skipped with --dry-run or if already sent today)
    end
    J->>S: record run steps
```

Keep the sentence after it.

§7.2 step 3 → `Refresh runs \`record\` + \`build\` for that league only, then re-renders.`

§7.3 step 1 → `The morning run and the game-day snapshots record injury reports; \`build\` appends them to \`injury_reports\` with \`observed_at\`.`

§7.4: in the diagram, change the final message to `error per category, calibration table, Brier score vs baselines`. Replace the **Limitation** bullet with:

`- **Last season (2025-26)** has no recorded statuses. Absences inferred from box scores are used **only to fit minutes redistribution given who played**; a replay never treats them as statuses known that morning. The historical backtest therefore measures rates and minutes given who played, against the season-average baseline. Synthetic matchups use last season's player pool.`
`- **This season (2026-27)** is recorded (ADR 0007). The season-end review replays it with real statuses, real rosters and free-agent pools, and both baselines (ADR 0010).`

§7.5: replace step 1 with `First login (\`python -m nfa.jobs.login\`): read the client ID and secret from the Keychain (service \`nba-fantasy-assistant\`, accounts \`yahoo_client_id\`, \`yahoo_client_secret\`), print the authorize URL, I approve, and Yahoo redirects to \`https://localhost:8765/callback\` **(M0: local listener or paste the redirected URL)**.` In step 2 add `(account \`yahoo_tokens\`)`. Add a line: `The app is a Confidential Client with Fantasy Sports – Read only (ADR 0006).`

Add new subsections after 7.5:

```markdown
### 7.6 Game-day snapshot

1. launchd starts `jobs.snapshot` about every 2 hours on days with NBA games.
2. `record(scope = snapshot)` fetches injury reports and each league's available players; `build` parses them.
3. A slot that passed while the Mac was asleep is recorded as a gap in `job_runs`; it is not back-filled.

### 7.7 Rebuild

1. After a parser fix, `jobs.rebuild` deletes the raw-derived datasets and replays `Store.all_raw()` through the parsers in `fetched_at` order.
2. Dataset versions change; existing snapshots still point to the raw-file IDs they used.

### 7.8 Backup

1. Weekly, `jobs.backup` copies `app.sqlite` with SQLite's backup API, archives it with `data/raw` into `nfa-backup-YYYY-MM-DD.tar.gz` in the configured folder, and deletes archives beyond the last 8.
2. The health page shows the last backup date; a backup older than 8 days is flagged.
```

- [ ] **Step 5: §8–§11**

§8: append `- Raw-derived rows carry \`observed_at\`; \`read_dataset(name, as_of)\` returns rows with \`observed_at ≤ as_of\` (box scores: \`game_date < as_of\`). It is the only look-ahead cut-off.`

§9 table: Injuries row → Refreshed `morning run; game-day snapshots ~2 h; on request`; add rows `| Yahoo ranks and projections | Yahoo | morning run | 24 h | cache |` and `| Transactions | Yahoo | morning run | 24 h | cache |`. After the table add `Recorder gaps (missed snapshots) are recorded per slot and shown on the health page.`

§10: add bullets `- backup folder and number of archives kept` and `- game-day snapshot hours` to the config list; change the Secrets bullet to `**Secrets** in the macOS Keychain via \`keyring\`, service \`nba-fantasy-assistant\`: accounts \`yahoo_client_id\`, \`yahoo_client_secret\`, \`yahoo_tokens\`, \`smtp_password\`. Never in config files, logs, fixtures or exceptions.`

§11: add to the health page list `recorder gaps, last backup date`; change the digest bullet to `The nudge email includes a health line only when something is broken.`

- [ ] **Step 6: §12 Testing** — Adapters bullet → `**Parsers:** run recorded raw files (scrubbed of tokens and private names) through \`parse\` and check the dataset rows; one fixture per league variant. **Fetchers:** \`requests(scope)\` is tested as a pure function; \`fetch\` is not unit-tested.` Add `- **Rebuild:** parsing the same raw files twice gives identical datasets.`

- [ ] **Step 7: §13 Extensibility** — ESPN row "What is added" → `adapters/platforms/espn/ (fetch + parse) producing the same Yahoo-equivalent datasets; ESPN IDs in the crosswalk`. Licensed feed row → `New \`StatsSource\` adapter producing \`nba_players\`, \`game_logs\`, \`schedule\``. Add row: `| **Another injury provider** | \`adapters/sources/injuries/<provider>/\` implementing \`InjuryFeed\` | Config chooses the provider. Nothing else changes. |`

- [ ] **Step 8: §14 Traceability** — update and add rows:

| Requirement | Where |
|---|---|
| FR-A1–A4 Yahoo connection | `adapters/platforms/yahoo/*`, ADR 0002, 0006, §7.5 |
| FR-B1–B2 Stats, schedule, injuries | `adapters/sources/*`, `services/record.py`, `services/build.py`, ADR 0004, 0009 |
| FR-E0 Today page | `services/today.py`, `ui/pages/today` |
| FR-E2 Matchup projector | `services/matchup.py`, `ScoringFormat.matchup_outlook`, shown on Today |
| FR-E4 Lineup check | `domain/lineup.py`, `services/lineup.py`, shown on Today |
| FR-F1–F2 Daily nudge | `jobs/daily.py`, `services/digest.py`, `adapters/notifiers/email_smtp.py`, §7.1 |
| FR-G1–G3 Log, scorecard, shadow mode | `recommendations`, `predictions`, `outcomes`, `snapshots` tables; `services/scorecard.py`; §7.1 |
| FR-J1–J4 Backtest, calibration, baselines | `services/backtest.py`, `domain/calibration.py`, `domain/baselines.py`, §7.4, ADR 0010 |
| FR-L1–L4 Recorder | `services/record.py`, `services/build.py`, `raw_files`, `jobs/daily.py`, `jobs/snapshot.py`, §7.6, §7.7, ADR 0007, 0008 |
| FR-L5 Backup | `services/backup.py`, `jobs/backup.py`, §7.8 |
| FR-M1–M3 Draft rankings | `domain/draft.py`, `services/draft_sheet.py`, `jobs/draft_sheet.py`, `ui/pages/draft` |
| FR-X3 No silent data loss | `job_runs` gaps, `services/health.py`, §7.6 |

Keep the other existing rows unchanged.

- [ ] **Step 9: §15 Open items** — first item → `- [x] Yahoo redirect URI: registered as \`https://localhost:8765/callback\` (ADR 0006). Still open: local listener vs pasting the redirected URL.` Add:
  - `- [ ] Yahoo endpoints for player ranks and projections (season, rest of season, daily) and their fields.`
  - `- [ ] Whether transactions plus daily rosters reconstruct my lineup and add/drop decisions.`

  Add to model decisions: `- [ ] Acceptance-gate margins against each baseline.` and `- [ ] Draft-season minutes estimate and its uncertainty range.` Add a third list:

```markdown
Recording decisions (confirmed in M1):

- [ ] Game-day snapshot hours.
- [ ] Backup folder.
```

- [ ] **Step 10: Verify**

```bash
grep -nE "data/cache|refresh\.py|composite|oob|8080" docs/ARCHITECTURE.md; grep -cE "FR-(E0|G1–G3|J1–J4|L1–L4|L5|M1–M3|X3)" docs/ARCHITECTURE.md
```
Expected: first grep prints nothing; count `7`.

- [ ] **Step 11: Commit (ask the user first)**

```bash
git add docs/ARCHITECTURE.md
git commit -m "Architecture: storage tiers, recorder flows, baselines and traceability

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: nfa-engineering skill and its references

**Files:**
- Modify: `.claude/skills/nfa-engineering/SKILL.md`, `references/domain-types.md`, `references/yahoo-api.md`, `references/testing.md`

- [ ] **Step 1: SKILL.md**

- Frontmatter description: `the five extension interfaces (platform, stats source, scoring format, notifier, store)` → `the six extension interfaces (platform, stats source, injury feed, scoring format, notifier, store), fetch/parse adapters and the raw store, the recorder jobs`; `the daily launchd job, the email digest` → `the launchd jobs (daily, snapshot, backup), the nudge email`.
- §1 diagram: `jobs/ (daily run, backfill)` → `jobs/ (daily, snapshot, backup, rebuild, backfill, backtest)`; adapter line → `adapters/: fetch (I/O) → raw store → parse (pure)   notifiers/  store/`. Add bullet: `- **Parsers are pure** like the domain: raw response in, dataset rows out. That makes recorded raw files the test fixtures and lets \`rebuild\` replay them.`
- §2 title `The five interfaces` → `The six interfaces`; table: add row `| \`InjuryFeed\` | provider chosen in M0 | another provider |`; `Store` row → `local raw files + parquet + SQLite`. Replace the sentence about injuries/composite with `Source adapters (\`FantasyPlatform\`, \`StatsSource\`, \`InjuryFeed\`) are a fetcher plus a parser; their contract is the datasets they produce (\`domain/datasets.py\`). Signatures: \`docs/ARCHITECTURE.md\` §5.`
- §4 first bullet → `- **Record, don't just cache.** Responses for data that cannot be fetched again are kept raw (ADR 0008). Final box scores are fetched once. Decide per dataset whether its raw response is retained (\`retain_raw\`).`
- §5 → replace the first bullet with `- \`data/\` is gitignored except \`data/crosswalk_overrides.json\`. Three tiers: raw files in \`data/raw/\` (append-only, kept indefinitely), parquet datasets in \`data/datasets/\` (raw-derived ones rebuildable), records in \`data/app.sqlite\` (WAL). Full layout: \`docs/ARCHITECTURE.md\` §6, ADRs 0003 and 0008.` Add `- A weekly backup archives \`data/raw\` and \`app.sqlite\`; never delete raw files.`
- §7 title → `The jobs`; first bullet → `- \`python -m nfa.jobs.daily\` (launchd each morning, or by hand with \`--as-of\` and \`--dry-run\`) runs \`record\` → \`build\` → \`advise\` → \`notify\`. \`advise\` arrives in M4 (shadow mode), \`notify\` in M5. Other jobs: \`snapshot\` (game days, ~2 h), \`backup\` (weekly), \`rebuild\`, \`backfill\`, \`backtest\`, \`login\`, \`draft_sheet\`.` Replace the "Steps:" bullet with `- Each step records its own success; a failure in one league does not stop the others. Missed snapshot slots are recorded as gaps.`
- §8 add: `- The Yahoo app is a Confidential Client with Fantasy Sports – Read only; redirect \`https://localhost:8765/callback\`. Keychain service \`nba-fantasy-assistant\`, accounts \`yahoo_client_id\`, \`yahoo_client_secret\`, \`yahoo_tokens\`, \`smtp_password\`. Check that an entry exists with \`security find-generic-password -s … -a …\` (no \`-w\`); never read or print values.`
- §9 Adapters bullet → `- Parsers: run recorded raw files through \`parse\`. Fetchers: test \`requests(scope)\`; never call the network.`
- Definition of done: add `- [ ] Parsers are pure; any new non-refetchable dataset is in \`retain_raw\``.
- Top sentence: `When \`docs/ARCHITECTURE.md\` exists, it overrides` → `\`docs/ARCHITECTURE.md\` overrides`.

- [ ] **Step 2: domain-types.md**

- Header: `the interfaces (§5)` stays; change `the interface sketch at the end of this file is superseded by §5` → `the interface sketch that used to end this file was removed; see §5`.
- Delete the `## Interfaces` section and its code block; replace with:

```markdown
## Interfaces and raw types

See `docs/ARCHITECTURE.md` §5: `FetchRequest`, `RawResponse`, `RecordScope`, `DatasetRows` (in `domain/raw.py`) and the protocols `Fetcher`, `Parser`, `FantasyPlatform`, `StatsSource`, `InjuryFeed`, `ScoringFormat`, `Notifier`, `Store` (in `domain/interfaces.py`).
```

- Notes: change the last bullet to `- \`as_of\` flows through every call that depends on time; raw-derived dataset rows carry \`observed_at\`.`

- [ ] **Step 3: yahoo-api.md**

- In "App registration and OAuth2": first bullet → `- App registered 2026-10-02 (ADR 0006): **Confidential Client**, **Fantasy Sports – Read** only.` Replace the Redirect URI bullet with `- Redirect URI: \`https://localhost:8765/callback\` (accepted at registration). M0 decides between a local listener on 8765 and pasting the redirected URL; \`oob\` is not used.` Add `- Credentials: Keychain service \`nba-fantasy-assistant\`, accounts \`yahoo_client_id\`, \`yahoo_client_secret\`; tokens in \`yahoo_tokens\`.`
- In "Useful resources" add rows: `| Player ranks | \`league/{league_key}/players;sort=AR\` (actual rank) and \`sort=OR\` (preseason/overall rank) (verify) |` and `| Player projections | not documented; look for projected stats in \`players/…/stats;type=…\` (verify in M0) |`.

- [ ] **Step 4: testing.md**

- Layout: `adapters/             # parse recorded fixtures into domain types` → `adapters/             # run recorded raw files through parsers`; `fixtures/` children → `raw/yahoo/`, `raw/nba_api/`, `raw/injuries/` with the comment `# recorded RawResponse files, scrubbed`.
- "Recording fixtures": first bullet → `- Fixtures are raw files from the recorder (or the M0 spike), copied with \`scripts/scrub_fixture.py\`.`
- Service tests: `FakePlatform, FakeStats` → `FakePlatform, FakeStats, FakeInjuryFeed`; add `- Recorder: a fetch failure records a health event and a gap, and the other sources still run.`
- Add under Backtest tests: `- A raw file with \`fetched_at\` after \`as_of\` is invisible to the replay.`

- [ ] **Step 5: Verify**

```bash
grep -rnE "five|composite|refresh\.py|oob|8080|data/cache" .claude/skills/nfa-engineering
```
Expected: no output except the yahoo-api.md line saying `\`oob\` is not used`.

- [ ] **Step 6: Commit (ask the user first)**

```bash
git add .claude/skills/nfa-engineering
git commit -m "Engineering skill: six interfaces, raw store, recorder jobs, Yahoo app

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: nba-fantasy-domain skill

**Files:**
- Modify: `.claude/skills/nba-fantasy-domain/SKILL.md`

- [ ] **Step 1: Description** — after `punt analysis,` add `pre-draft rankings, model baselines,`.

- [ ] **Step 2: §4 Projections** — add a final bullet:

`- **Data for the minutes model.** On last season, absences inferred from box scores may be used to fit redistribution given who played, never as statuses "known that morning" in a replay. From 2026-27 the recorder captures real statuses; refit on them after the season.`

- [ ] **Step 3: §9 Backtests** — replace the baseline bullet with:

`- **Baselines and the acceptance gate** (ADR 0010): compare every model with season average × games and with Yahoo's recorded ranks and projections. A model goes live only if it beats both on error and calibration; otherwise use the baseline and say so. The margins are an open decision.`

- [ ] **Step 4: New section** before "Common traps":

```markdown
## 10. Pre-draft rankings

- Rank by **season-long value** in each league: per-game z-values × expected games, over that league's pool and categories.
- Produce one ranking with no punt and one per punt build the user chooses; punted categories get weight 0.
- Season projections come from last season's rates, shrunk, and a minutes estimate with an uncertainty range. Show the range; a rookie or a player changing team is less certain than a veteran in the same role.
- The draft sheet is a cheat sheet, not a live board: no pick tracking.
```

- [ ] **Step 5: Common traps** — add `- A model shipped without beating the season-average and Yahoo baselines.`

- [ ] **Step 6: Verify**

```bash
grep -nE "Pre-draft|acceptance gate|absences inferred" .claude/skills/nba-fantasy-domain/SKILL.md
```
Expected: three matches.

- [ ] **Step 7: Commit (ask the user first)**

```bash
git add .claude/skills/nba-fantasy-domain/SKILL.md
git commit -m "Domain skill: baselines, inferred absences, pre-draft rankings

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Status** — replace the paragraph and table with:

```markdown
Design is done; building has not started. The 2026-27 season is a test bed and v1 targets the 2027-28 season. Next milestone: **M0, a data access spike**, then **M1, the recorder**, which captures data that cannot be fetched later (injury statuses, Yahoo league state and ranks) from early in this season.

| Milestone | Delivers |
|---|---|
| M0 Spike | Yahoo OAuth, league data and ranks, NBA game logs, injury source choice, player ID crosswalk prototype |
| M1 Recorder | Raw store, daily and game-day recording, crosswalk, health page, weekly backup |
| M2 Foundation | Datasets, schedule grid, player board, Today page skeleton |
| M3 Projections | Minutes and injury model, projections, backtest and calibration against baselines |
| M4 Advice | Valuation, matchup projector, streaming ranker, lineup check, full Today page (shadow mode) |
| M5 Daily loop | Nudge email, injury opportunity alerts, recommendation log, scorecard |
| M6 Strategy and draft | Punt analysis, pre-draft rankings |
```

- [ ] **Step 2: What it will do** — first bullet → `- **Today page**: for each team, lineup issues, the matchup by category with win probabilities, and the top moves with their reasons.`; daily email bullet → `- **Daily email**: a short nudge with anything urgent across all leagues.`; add `- **Recorder**: keeps injury statuses, Yahoo league state and ranks as they were each day, so models are tested on what was really known.` and `- **Pre-draft rankings** per league and punt build.`

- [ ] **Step 3: Design principles** — add `- **Keep what can't be fetched again.** Raw responses are stored and can be re-parsed; models must beat simple baselines and Yahoo's ranks before they are used.`

- [ ] **Step 4: Repository guide** — add rows `| \`docs/superpowers/\` | Design specs and implementation plans |`; change the engineering skill row to `Code conventions: layers, six interfaces, fetch/parse adapters, raw store, testing, secrets`.

- [ ] **Step 5: Verify**

```bash
grep -nE "M6|Today page|Recorder|docs/superpowers" README.md | wc -l
```
Expected: at least `5`.

- [ ] **Step 6: Commit (ask the user first)**

```bash
git add README.md
git commit -m "README: test-bed season, recorder, Today page, milestones M0-M6

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Consistency sweep, push and PR

**Files:**
- Modify: any file the sweep flags.

- [ ] **Step 1: Stale-term sweep**

```bash
grep -rnE "five (extension )?interfaces|composite|services/refresh|refresh\.py|data/cache|8080|Draft assistant for next|daily (email )?digest|email digest" docs .claude README.md CLAUDE.md | grep -v "docs/superpowers/"
```
Expected: no output. Fix each hit in its file (the replacement wording is in Tasks 2–7), then rerun. `CLAUDE.md` line "a daily email digest" in its first paragraph → "a short daily email".

- [ ] **Step 2: Secrets sweep**

```bash
grep -rnE "dj0y|[0-9a-f]{40}" docs .claude README.md CLAUDE.md
```
Expected: no output.

- [ ] **Step 3: Commit sweep fixes, if any (ask the user first)**

```bash
git add -A docs .claude README.md CLAUDE.md
git commit -m "Remove stale references to the previous design

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Push (ask the user first)**

```bash
git push -u origin docs/design-revision
```

- [ ] **Step 5: Open the PR (ask the user first)**

```bash
env -u SSL_CERT_FILE gh pr create --base main --head docs/design-revision \
  --title "Docs: apply design revision (test-bed season, recorder, six interfaces)" \
  --body "<summary of Tasks 1–8, the Review Focus list, and: check every Mermaid diagram in the rich diff>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```
Write the body from what was actually changed; do not paste this template line.

- [ ] **Step 6: Mermaid check** — open the PR's "Files changed" → rich diff for `docs/ARCHITECTURE.md`; every diagram (§2, §4, §6 ER, §7.1, §7.4) renders. Fix syntax errors on the branch (commit and push only after asking).

- [ ] **Step 7: Hand back** — tell the user the PR URL; the user reviews and merges. After the merge, offer the local cleanup (`git switch main`, `git pull --ff-only`, `git branch -d docs/design-revision`), asking first.
