"""THROWAWAY M0 probe: compare the official NBA report, ESPN and Yahoo injury statuses.

Run a few times a day for about a week:
    uv run --group spike python scripts/spike/injury_probe.py
Appends to data/spike/injury_comparison.csv.
"""

import csv
import io
import re
from datetime import datetime
from typing import Any

import requests
from _common import UA, Probe, find_all, load_json, yahoo_records

from nfa import clock
from nfa.adapters import http
from nfa.adapters.platforms.yahoo.auth import YahooAuth
from nfa.adapters.platforms.yahoo.fetch import YahooFetcher, yahoo_request
from nfa.domain.raw import FetchRequest

LISTING_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
PDF_LINK = re.compile(
    rb"https://ak-static\.cms\.nba\.com/referee/injury/Injury-Report_[0-9A-Za-z_-]+\.pdf"
)
PDF_TIME = re.compile(r"Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})(?:_(\d{2}))?(AM|PM)")
FIELDS = ["run_at", "source", "player", "team", "status", "detail", "source_time"]


def report_time(url: str) -> datetime:
    m = PDF_TIME.search(url)
    if not m:
        return datetime.min
    day, hour, minute, half = m.groups()
    return datetime.strptime(f"{day} {hour}:{minute or '00'} {half}", "%Y-%m-%d %I:%M %p")


def parse_official(payload: bytes) -> list[dict[str, str]]:
    import pdfplumber

    rows: list[dict[str, str]] = []
    team = ""
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for raw_cells in table:
                    cells = [(c or "").strip() for c in raw_cells]
                    if len(cells) < 7:
                        continue
                    if cells[3] and cells[3] != "Team":
                        team = cells[3]
                    if cells[4] in ("", "Player Name"):
                        continue
                    rows.append(
                        {
                            "player": cells[4],
                            "team": team,
                            "status": cells[5],
                            "detail": cells[6],
                            "source_time": "",
                        }
                    )
        if not rows and pdf.pages:
            sample = (pdf.pages[0].extract_text() or "")[:500]
            print("official: no table rows; first page text sample:\n", sample)
    return rows


def official(probe: Probe) -> list[dict[str, str]]:
    session = requests.Session()
    page = probe.run(
        lambda r: http.get(r, LISTING_URL, session=session, throttle=probe.throttle, headers=UA),
        FetchRequest("nba_injury_report", "listing", "2026-27"),
    )
    if page is None or not page.ok:
        return []
    links = sorted({m.decode() for m in PDF_LINK.findall(page.payload)}, key=report_time)
    if not links:
        print("official: no PDF links on the listing page")
        return []
    url = links[-1]
    name = url.rsplit("/", 1)[-1]
    pdf = probe.run(
        lambda r: http.get(r, url, session=session, throttle=probe.throttle, headers=UA),
        FetchRequest("nba_injury_report", "report", name),
    )
    if pdf is None or not pdf.ok:
        return []
    rows = parse_official(pdf.payload)
    for row in rows:
        row["source_time"] = name
    return rows


def espn(probe: Probe) -> list[dict[str, str]]:
    session = requests.Session()
    raw = probe.run(
        lambda r: http.get(r, ESPN_URL, session=session, throttle=probe.throttle, headers=UA),
        FetchRequest("espn", "injuries", "nba"),
    )
    data = load_json(raw) or {}
    rows: list[dict[str, str]] = []
    for team in data.get("injuries", []):
        for item in team.get("injuries", []):
            rows.append(
                {
                    "player": item.get("athlete", {}).get("displayName", ""),
                    "team": team.get("displayName", ""),
                    "status": item.get("status", ""),
                    "detail": item.get("shortComment") or item.get("longComment", ""),
                    "source_time": item.get("date", ""),
                }
            )
    return rows


def yahoo(probe: Probe) -> list[dict[str, str]]:
    fetcher = YahooFetcher(YahooAuth(), probe.throttle)

    def get(dataset: str, key: str, path: str) -> Any:
        return load_json(probe.run(fetcher.fetch, yahoo_request(dataset, key, path)))

    leagues = get("leagues", "mine", "users;use_login=1/games;game_keys=nba/leagues")
    seen: dict[str, dict[str, str]] = {}
    for lk in sorted(set(find_all(leagues, "league_key"))):
        for start in range(0, 400, 25):
            page = get(
                "taken_players",
                f"{lk};start={start}",
                f"league/{lk}/players;status=T;start={start};count=25",
            )
            records = yahoo_records(page, "player_key")
            for rec in records:
                if rec.get("status"):
                    seen[rec["player_key"]] = {
                        "player": (rec.get("name") or {}).get("full", ""),
                        "team": rec.get("editorial_team_abbr", ""),
                        "status": rec.get("status", ""),
                        "detail": rec.get("injury_note", "") or rec.get("status_full", ""),
                        "source_time": "",
                    }
            if len(records) < 25:
                break
    return list(seen.values())


def main() -> int:
    probe = Probe()
    run_at = clock.now().isoformat()
    results = {"official": official(probe), "espn": espn(probe), "yahoo": yahoo(probe)}
    path = probe.config.data_dir / "spike" / "injury_comparison.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for source, rows in results.items():
            for row in rows:
                writer.writerow({"run_at": run_at, "source": source, **row})
    for source, rows in results.items():
        print(f"{source}: {len(rows)} players with a status")
    print(f"appended to {path}")
    probe.print_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
