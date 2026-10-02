"""THROWAWAY M0 probe: exercise the Yahoo Fantasy API and save every response as raw.

Run: uv run python scripts/spike/yahoo_probe.py
"""

from typing import Any

from _common import Probe, all_keys, find_all, load_json

from nfa import clock
from nfa.adapters.platforms.yahoo.auth import YahooAuth
from nfa.adapters.platforms.yahoo.fetch import YahooFetcher, yahoo_request

FA_TARGET = 200
PAGE = 25
RANK_PATHS = [
    ("sort_AR", "league/{lk}/players;sort=AR;count=10"),
    ("sort_OR", "league/{lk}/players;sort=OR;count=10"),
    ("stats_season", "league/{lk}/players;sort=AR;count=5/stats;type=season"),
    ("stats_lastweek", "league/{lk}/players;sort=AR;count=5/stats;type=lastweek"),
    ("stats_date", "league/{lk}/players;sort=AR;count=5/stats;type=date;date={today}"),
    ("stats_projected_season", "league/{lk}/players;sort=AR;count=5/stats;type=projected_season"),
    ("stats_projected_week", "league/{lk}/players;sort=AR;count=5/stats;type=projected_week"),
    ("draft_analysis", "league/{lk}/players;sort=AR;count=5/draft_analysis"),
    ("ownership", "league/{lk}/players;sort=AR;count=5/ownership"),
]


def main() -> int:
    probe = Probe()
    auth = YahooAuth()
    fetcher = YahooFetcher(auth, probe.throttle)

    def get(dataset: str, key: str, path: str) -> Any:
        return load_json(probe.run(fetcher.fetch, yahoo_request(dataset, key, path)))

    games = get("games", "nba", "games;game_keys=nba")
    print("refreshed this run:", auth.refreshed_at is not None)
    print("game keys:", find_all(games, "game_key"))
    leagues = get("leagues", "mine", "users;use_login=1/games;game_keys=nba/leagues")
    league_keys = sorted(set(find_all(leagues, "league_key")))
    print("my leagues:", league_keys)
    get("teams", "mine", "users;use_login=1/games;game_keys=nba/teams")

    today = clock.nba_today().isoformat()
    setting_fields: set[str] = set()
    sample_player_keys: list[str] = []
    for lk in league_keys:
        setting_fields |= all_keys(get("league_settings", lk, f"league/{lk}/settings"))
        for dataset in ("standings", "scoreboard", "transactions"):
            get(dataset, lk, f"league/{lk}/{dataset}")
        teams = get("teams", lk, f"league/{lk}/teams")
        for tk in sorted(set(find_all(teams, "team_key"))):
            get("rosters", f"{tk};date={today}", f"team/{tk}/roster;date={today}")
        fetched = 0
        for start in range(0, FA_TARGET, PAGE):
            page = get(
                "available_players",
                f"{lk};start={start}",
                f"league/{lk}/players;status=A;sort=AR;start={start};count={PAGE}/percent_owned",
            )
            keys = find_all(page, "player_key")
            if start == 0:
                sample_player_keys += keys[:5]
            fetched += len(keys)
            if len(keys) < PAGE:
                break
        print(f"{lk}: free agents fetched = {fetched}")
        for label, template in RANK_PATHS:
            get(f"rank_probe_{label}", lk, template.format(lk=lk, today=today))

    previous = get("games", "nba;seasons=2025", "games;game_codes=nba;seasons=2025")
    prev_keys = find_all(previous, "game_key")
    if prev_keys and sample_player_keys:
        sample = sample_player_keys[:5]
        ids = [k.split(".p.")[1] for k in sample]
        now_names = find_all(
            get("players", "current", "players;player_keys=" + ",".join(sample)), "full"
        )
        old_keys = ",".join(f"{prev_keys[0]}.p.{i}" for i in ids)
        old_names = find_all(get("players", "previous", "players;player_keys=" + old_keys), "full")
        print(
            "player id stability (current vs previous season):",
            list(zip(now_names, old_names, strict=False)),
        )

    print("\nsettings fields:", ", ".join(sorted(setting_fields)))
    probe.print_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
