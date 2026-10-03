"""Remove private data from raw JSON before it becomes a committed test fixture."""

import json
import re
from collections.abc import Iterable

PLACEHOLDER_KEYS = frozenset({"nickname", "guid", "email", "image_url", "url"})
SECRET_KEYS = frozenset({"access_token", "refresh_token", "authorization", "client_secret"})
# Any value json.loads can return.
type Json = None | bool | int | float | str | list[Json] | dict[str, Json]

TOKENISH = re.compile(r"eyJ[A-Za-z0-9_-]{10,}|[A-Za-z0-9_-]{60,}")


class UnsafeFixtureError(Exception):
    pass


class Scrubber:
    """Replaces private values with stable placeholders (same input → same placeholder)."""

    def __init__(self) -> None:
        self._aliases: dict[tuple[str, str], str] = {}
        self._counts: dict[str, int] = {}

    def _alias(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._aliases:
            self._counts[kind] = self._counts.get(kind, 0) + 1
            self._aliases[key] = f"{kind}-{self._counts[kind]}"
        return self._aliases[key]

    def scrub(self, obj: Json, team_context: bool = False) -> Json:
        if isinstance(obj, list):
            in_team = team_context or any(isinstance(e, dict) and "team_key" in e for e in obj)
            return [self.scrub(e, in_team) for e in obj]
        if isinstance(obj, dict):
            is_team = team_context or "team_key" in obj
            out: dict[str, Json] = {}
            for key, value in obj.items():
                if key.lower() in SECRET_KEYS:
                    raise UnsafeFixtureError(f"secret-like key {key!r} found")
                if key in PLACEHOLDER_KEYS and isinstance(value, str):
                    out[key] = self._alias(key, value)
                elif key == "name" and is_team and isinstance(value, str):
                    out[key] = self._alias("team", value)
                else:
                    out[key] = self.scrub(value)
            return out
        return obj


def check_safe(text: str, forbidden: Iterable[str]) -> None:
    for value in forbidden:
        if value and value in text:
            raise UnsafeFixtureError("a known secret value is present; fixture not written")
    match = TOKENISH.search(text)
    if match:
        raise UnsafeFixtureError(
            f"token-like string at offset {match.start()}; fixture not written"
        )


def scrub_payload(payload: bytes, forbidden: Iterable[str]) -> bytes:
    try:
        data: Json = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnsafeFixtureError("payload is not JSON; review and copy it by hand") from exc
    cleaned = json.dumps(Scrubber().scrub(data), sort_keys=True, indent=1)
    check_safe(cleaned, list(forbidden))
    return cleaned.encode()
