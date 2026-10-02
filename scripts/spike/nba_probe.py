"""THROWAWAY M0 probe: nba_api and cdn.nba.com from this Mac.

Run: uv run python scripts/spike/nba_probe.py
"""

import json
from collections.abc import Callable
from typing import Any

import requests
from _common import UA, Probe, nba_api_fetch

from nfa.adapters import http
from nfa.domain.raw import FetchRequest

CDN_SCHEDULE = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"


def calls() -> list[tuple[str, str, Callable[[], Any]]]:
    from nba_api.stats.endpoints import commonallplayers, playergamelogs

    result: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "game_logs",
            "2025-26",
            lambda: playergamelogs.PlayerGameLogs(
                season_nullable="2025-26", season_type_nullable="Regular Season", timeout=120
            ),
        ),
        (
            "nba_players",
            "2026-27",
            lambda: commonallplayers.CommonAllPlayers(
                is_only_current_season=1, season="2026-27", timeout=60
            ),
        ),
    ]
    try:
        from nba_api.stats.endpoints import scheduleleaguev2

        result.append(
            (
                "schedule",
                "2026-27",
                lambda: scheduleleaguev2.ScheduleLeagueV2(season="2026-27", timeout=60),
            )
        )
    except ImportError:
        print("ScheduleLeagueV2 is not in this nba_api version; relying on cdn.nba.com")
    return result


def describe(payload: bytes) -> str:
    data = json.loads(payload)
    sets = data.get("resultSets") or data.get("resultSet") or []
    if isinstance(sets, dict):
        sets = [sets]
    parts = [
        f"{s.get('name')}: {len(s.get('rowSet', []))} rows, columns={s.get('headers')}"
        for s in sets
    ]
    return "; ".join(parts) or f"top-level keys={list(data)[:10]}"


def main() -> int:
    probe = Probe()
    for dataset, key, build in calls():
        raw = probe.run(
            nba_api_fetch(build), FetchRequest("nba_api", dataset, key, {"season": key})
        )
        if raw is not None and raw.ok:
            print("   ", describe(raw.payload)[:600])
    session = requests.Session()
    raw = probe.run(
        lambda r: http.get(r, CDN_SCHEDULE, session=session, throttle=probe.throttle, headers=UA),
        FetchRequest("cdn_nba", "schedule", "2026-27"),
    )
    if raw is not None and raw.ok:
        games = json.loads(raw.payload).get("leagueSchedule", {}).get("gameDates", [])
        print(f"    cdn schedule: {len(games)} game dates")
    probe.print_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
