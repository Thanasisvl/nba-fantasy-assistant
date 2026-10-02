"""THROWAWAY M0 helpers shared by the probes. Not imported by src/."""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from nfa import clock
from nfa.adapters.http import AuthError, Throttle
from nfa.adapters.store.db import open_db
from nfa.adapters.store.raw import RawStore
from nfa.config import load_config
from nfa.domain.raw import FetchRequest, RawFileId, RawResponse

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) nba-fantasy-assistant/0.0.1 personal use"}


@dataclass
class LogRow:
    source: str
    dataset: str
    key: str
    status: int | None
    seconds: float
    raw_id: RawFileId | None
    error: str


class Probe:
    def __init__(self) -> None:
        self.config = load_config()
        self.store = RawStore(self.config.data_dir, open_db(self.config.data_dir / "app.sqlite"))
        self.throttle = Throttle(self.config.throttle_s)
        self.log: list[LogRow] = []

    def run(
        self, fetch: Callable[[FetchRequest], RawResponse], request: FetchRequest
    ) -> RawResponse | None:
        start = time.monotonic()
        raw: RawResponse | None = None
        error = ""
        try:
            raw = fetch(request)
        except AuthError as exc:
            if exc.response is not None:
                self.store.write_raw(exc.response)
            raise
        except Exception as exc:  # throwaway probe: record anything and carry on
            raw = getattr(exc, "response", None)
            error = f"{type(exc).__name__}: {exc}"
        raw_id = self.store.write_raw(raw) if raw is not None else None
        row = LogRow(
            request.source,
            request.dataset,
            request.key,
            raw.status if raw else None,
            time.monotonic() - start,
            raw_id,
            error,
        )
        self.log.append(row)
        print(
            f"{row.status or 'ERR':>4} {row.seconds:6.2f}s {request.source}/{request.dataset} "
            f"{request.key} -> {raw_id or '-'} {error}"
        )
        return raw

    def print_summary(self) -> None:
        failures = [r for r in self.log if r.status is None or not 200 <= r.status < 300]
        limited = [r for r in self.log if r.status in (429, 999)]
        print(
            f"\n{len(self.log)} requests, {len(failures)} failed, {len(limited)} rate-limited, "
            f"{sum(r.seconds for r in self.log):.1f}s total"
        )
        for r in failures:
            print(f"  FAILED {r.source}/{r.dataset} {r.key}: {r.status} {r.error}")


def load_json(raw: RawResponse | None) -> Any:
    if raw is None or not raw.ok:
        return None
    return json.loads(raw.payload)


def find_all(obj: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                found.append(v)
            found += find_all(v, key)
    elif isinstance(obj, list):
        for v in obj:
            found += find_all(v, key)
    return found


def all_keys(obj: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        keys |= set(obj)
        for v in obj.values():
            keys |= all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            keys |= all_keys(v)
    return keys


def yahoo_records(obj: Any, marker: str) -> list[dict[str, Any]]:
    """Yahoo returns records as lists of single-key dicts; merge each list containing `marker`."""
    records: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            if any(isinstance(e, dict) and marker in e for e in node):
                merged: dict[str, Any] = {}
                for e in node:
                    if isinstance(e, dict):
                        merged.update(e)
                records.append(merged)
            for e in node:
                walk(e)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    walk(obj)
    return records


def nba_api_fetch(build: Callable[[], Any]) -> Callable[[FetchRequest], RawResponse]:
    """Wraps an nba_api endpoint constructor so its JSON is saved like any other raw response."""

    def fetch(request: FetchRequest) -> RawResponse:
        endpoint = build()
        response = endpoint.nba_response
        status = int(getattr(response, "_status_code", 200) or 200)
        payload = response.get_json().encode()
        return RawResponse(request=request, fetched_at=clock.now(), status=status, payload=payload)

    return fetch
