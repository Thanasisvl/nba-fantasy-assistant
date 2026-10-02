"""THROWAWAY M0 probe: how many rostered Yahoo players match an NBA person ID automatically.

Run: uv run python scripts/spike/crosswalk_probe.py
Writes suggestions to data/spike/crosswalk_suggestions.json.
"""

import difflib
import json
import re
import unicodedata
from typing import Any

from _common import Probe, find_all, load_json, nba_api_fetch, yahoo_records

from nfa.adapters.platforms.yahoo.auth import YahooAuth
from nfa.adapters.platforms.yahoo.fetch import YahooFetcher, yahoo_request
from nfa.domain.raw import FetchRequest

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z ]+", " ", text.replace("'", ""))
    return " ".join(part for part in text.split() if part not in SUFFIXES)


def nba_players(probe: Probe) -> list[dict[str, Any]]:
    from nba_api.stats.endpoints import commonallplayers

    raw = probe.run(
        nba_api_fetch(
            lambda: commonallplayers.CommonAllPlayers(
                is_only_current_season=1, season="2026-27", timeout=60
            )
        ),
        FetchRequest("nba_api", "nba_players", "2026-27", {"season": "2026-27"}),
    )
    data = load_json(raw) or {}
    if not data.get("resultSets"):
        print("nba_api players call failed; no NBA side to match against")
        return []
    result_set = data["resultSets"][0]
    return [dict(zip(result_set["headers"], row, strict=True)) for row in result_set["rowSet"]]


def yahoo_rostered(probe: Probe) -> list[dict[str, str]]:
    fetcher = YahooFetcher(YahooAuth(), probe.throttle)

    def get(dataset: str, key: str, path: str) -> Any:
        return load_json(probe.run(fetcher.fetch, yahoo_request(dataset, key, path)))

    leagues = get("leagues", "mine", "users;use_login=1/games;game_keys=nba/leagues")
    players: dict[str, dict[str, str]] = {}
    for lk in sorted(set(find_all(leagues, "league_key"))):
        for start in range(0, 400, 25):
            page = get(
                "taken_players",
                f"{lk};start={start}",
                f"league/{lk}/players;status=T;start={start};count=25",
            )
            records = yahoo_records(page, "player_key")
            for rec in records:
                players[rec["player_key"]] = {
                    "player_key": rec["player_key"],
                    "name": (rec.get("name") or {}).get("full", ""),
                    "team": rec.get("editorial_team_abbr", ""),
                }
            if len(records) < 25:
                break
    return list(players.values())


def main() -> int:
    probe = Probe()
    nba = nba_players(probe)
    by_name: dict[str, list[dict[str, Any]]] = {}
    for p in nba:
        by_name.setdefault(normalize(p["DISPLAY_FIRST_LAST"]), []).append(p)
    yahoo = yahoo_rostered(probe)
    matched: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for y in yahoo:
        candidates = by_name.get(normalize(y["name"]), [])
        if len(candidates) > 1:
            same_team = [
                c for c in candidates if c.get("TEAM_ABBREVIATION", "").upper() == y["team"].upper()
            ]
            candidates = same_team if len(same_team) == 1 else candidates
        if len(candidates) == 1:
            matched.append({**y, "nba_person_id": candidates[0]["PERSON_ID"]})
        elif candidates:
            ambiguous.append({**y, "candidates": [c["PERSON_ID"] for c in candidates]})
        else:
            close = difflib.get_close_matches(normalize(y["name"]), list(by_name), n=3, cutoff=0.8)
            suggestions = [(n, [c["PERSON_ID"] for c in by_name[n]]) for n in close]
            unmatched.append({**y, "suggestions": suggestions})
    total = len(yahoo)
    rate = 100.0 * len(matched) / total if total else 0.0
    print(
        f"rostered Yahoo players: {total}; auto-matched: {len(matched)} ({rate:.1f}%); "
        f"ambiguous: {len(ambiguous)}; unmatched: {len(unmatched)}"
    )
    for row in ambiguous + unmatched:
        print("  ", json.dumps(row))
    out = probe.config.data_dir / "spike" / "crosswalk_suggestions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"ambiguous": ambiguous, "unmatched": unmatched}, indent=1))
    print(f"suggestions written to {out}")
    probe.print_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
