from pathlib import Path

from nfa.adapters.store.db import open_db


def test_migrations_apply_on_empty_database(tmp_path: Path) -> None:
    conn = open_db(tmp_path / "app.sqlite")
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"raw_files", "schema_migrations"} <= tables
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_migrations_are_idempotent(tmp_path: Path) -> None:
    open_db(tmp_path / "app.sqlite").close()
    conn = open_db(tmp_path / "app.sqlite")
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations")]
    assert versions == ["0001_raw_files"]
