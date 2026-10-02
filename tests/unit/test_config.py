from pathlib import Path

from nfa.config import DEFAULT_THROTTLE_S, load_config


def test_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.toml")
    assert config.data_dir == Path("data")
    assert dict(config.throttle_s) == DEFAULT_THROTTLE_S


def test_file_overrides_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('data_dir = "/tmp/nfa"\n[throttle_s]\nyahoo = 2.5\n')
    config = load_config(path)
    assert config.data_dir == Path("/tmp/nfa")
    assert config.throttle_s["yahoo"] == 2.5
    assert config.throttle_s["espn"] == DEFAULT_THROTTLE_S["espn"]
