"""Loads config.toml (gitignored). Secrets never live here; they are in the Keychain."""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_THROTTLE_S: dict[str, float] = {
    "yahoo": 1.0,
    "nba_api": 0.6,
    "cdn_nba": 1.0,
    "espn": 1.0,
    "nba_injury_report": 2.0,
}


@dataclass(frozen=True)
class Config:
    data_dir: Path
    throttle_s: Mapping[str, float]


def load_config(path: Path = Path("config.toml")) -> Config:
    raw = tomllib.loads(path.read_text()) if path.exists() else {}
    throttle = {**DEFAULT_THROTTLE_S, **{k: float(v) for k, v in raw.get("throttle_s", {}).items()}}
    return Config(data_dir=Path(raw.get("data_dir", "data")), throttle_s=throttle)
