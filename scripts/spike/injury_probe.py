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
from nfa.adapters.http import AuthError
from nfa.adapters.platforms.yahoo.auth import YahooAuth
from nfa.adapters.platforms.yahoo.fetch import YahooFetcher, yahoo_request
from nfa.domain.raw import FetchRequest

# The new season's page may not exist yet; the previous one links to the latest report.
LISTING_URLS = [
    "https://official.nba.com/nba-injury-report-2026-27-season/",
    "https://official.nba.com/nba-injury-report-2025-26-season/",
]
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


HEADER_COLUMNS = {
    "Game Date": "date",
    "Game Time": "time",
    "Matchup": "matchup",
    "Team": "team",
    "Player Name": "player",
    "Current Status": "status",
    "Reason": "detail",
}


def parse_official(payload: bytes) -> list[dict[str, str]]:
    """The report is positioned text, not a table: place words by the header's column x-positions."""
    import pdfplumber

    rows: list[dict[str, str]] = []
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=1.5)
            lines: dict[int, list[dict[str, Any]]] = {}
            for w in words:
                lines.setdefault(round(w["top"] / 3), []).append(w)
            columns: list[tuple[float, str]] = []
            records: list[tuple[float, dict[str, str]]] = []
            reasons: list[tuple[float, str]] = []
            carry = {"date": "", "time": "", "matchup": "", "team": ""}
            for key in sorted(lines):
                line = sorted(lines[key], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in line)
                if not columns and "Player Name" in text:
                    for label, field in HEADER_COLUMNS.items():
                        first = label.split()[0]
                        xs = [w["x0"] for w in line if w["text"] == first]
                        if label == "Game Time":
                            xs = xs[1:2]
                        if xs:
                            columns.append((xs[0] - 3, field))
                    columns.sort()
                    continue
                if not columns or text.startswith("Page"):
                    continue
                cells: dict[str, list[str]] = {}
                for w in line:
                    field = [f for x, f in columns if x <= w["x0"]]
                    if field:
                        cells.setdefault(field[-1], []).append(w["text"])
                joined = {f: " ".join(v) for f, v in cells.items()}
                for f in carry:
                    if joined.get(f):
                        carry[f] = joined[f]
                top = line[0]["top"]
                if joined.get("player"):
                    records.append(
                        (
                            top,
                            {
                                **carry,
                                "player": joined["player"],
                                "status": joined.get("status", ""),
                                "detail": joined.get("detail", ""),
                            },
                        )
                    )
                elif joined.get("detail"):
                    reasons.append((top, joined["detail"]))
            for top, fragment in reasons:
                if records:
                    _, nearest = min(records, key=lambda r: abs(r[0] - top))
                    nearest["detail"] = (nearest["detail"] + " " + fragment).strip()
            for _, record in records:
                rows.append(
                    {
                        "player": record["player"],
                        "team": record["team"],
                        "status": record["status"],
                        "detail": record["detail"],
                        "source_time": "",
                    }
                )
    return rows


def official(probe: Probe) -> list[dict[str, str]]:
    session = requests.Session()
    links: list[str] = []
    for listing in LISTING_URLS:
        page = probe.run(
            lambda r, url=listing: http.get(
                r, url, session=session, throttle=probe.throttle, headers=UA
            ),
            FetchRequest("nba_injury_report", "listing", listing.rstrip("/").rsplit("/", 1)[-1]),
        )
        if page is not None and page.ok:
            links = sorted({m.decode() for m in PDF_LINK.findall(page.payload)}, key=report_time)
            if links:
                break
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
    results = {"official": official(probe), "espn": espn(probe)}
    try:
        results["yahoo"] = yahoo(probe)
    except AuthError as exc:  # Fantasy API not approved yet: keep the other two sources
        print(f"yahoo: skipped ({exc})")
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
