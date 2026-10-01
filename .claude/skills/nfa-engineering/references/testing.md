# Testing patterns

## Layout

```
tests/
  conftest.py          # blocks network, shared builders
  unit/                # domain: pure functions, hand-built inputs
  adapters/            # parse recorded fixtures into domain types
  services/            # use cases with fake adapters
  backtest/            # look-ahead and replay tests
  fixtures/
    yahoo/             # recorded JSON, secrets and names of private-league members removed
    nba_api/           # small recorded responses (trimmed to a few players/games)
```

## Block the network

```python
# conftest.py
import socket
import pytest

@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def guard(*args, **kwargs):
        raise RuntimeError("Tests must not use the network; use a fixture.")
    monkeypatch.setattr(socket.socket, "connect", guard)
```

## Recording fixtures

- Record a real response once with a script in `scripts/` (e.g. `scripts/record_yahoo_fixture.py league-settings`).
- Before saving: remove tokens and headers, replace other managers' names and emails with placeholders, trim player lists to what the test needs.
- Name fixtures after what they contain (`settings_9cat_12team.json`, `settings_8cat_no_to.json`, `scoreboard_week3_midweek.json`).
- Keep one fixture per league variant we care about: that is how we prove settings are read, not hardcoded.

## Domain tests

- Build inputs with small helpers (`make_player(...)`, `make_week(...)`), not with fixtures.
- One behavior per test, named after the rule:
  - `test_fg_pct_uses_summed_makes_and_attempts`
  - `test_turnovers_are_lower_is_better`
  - `test_usable_games_skip_days_with_full_slots`
  - `test_injury_minutes_not_added_twice_when_absence_in_sample`
  - `test_win_probability_is_certain_when_week_is_over`
  - `test_categories_come_from_settings_not_defaults`
- Property-style checks where cheap: probabilities stay in [0, 1]; adding a player never reduces raw games; punting a category gives it weight 0.

## Service tests

- Use fake implementations of the interfaces (in-memory `FakePlatform`, `FakeStats`, `FakeStore`, `FakeNotifier` that records sends).
- Test failure paths: a source raises → service returns cached data marked stale and records the failure.
- Daily job: running twice with the same `as_of` sends one email and writes one set of log entries.

## Backtest tests

- Given data spanning several days, replaying `as_of = D` must not see any stat line with `game_date >= D` or any status published after the morning of `D`. Assert it directly by feeding a sentinel future row that would change the result.
- Calibration code: on synthetic predictions with known frequencies, buckets come out as expected.

## What not to test

- Streamlit layout details. Test the services the pages call.
- Third-party library internals.
