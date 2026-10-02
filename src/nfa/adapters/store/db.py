"""SQLite connection (WAL) and numbered SQL migrations."""

import sqlite3
from pathlib import Path

from nfa import clock

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def apply_migrations(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    conn.commit()
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    newly_applied: list[str] = []
    for script in sorted(directory.glob("*.sql")):
        version = script.stem
        if version in applied:
            continue
        stamp = clock.now().isoformat()
        conn.executescript(
            f"BEGIN;\n{script.read_text()}\n"
            f"INSERT INTO schema_migrations (version, applied_at) VALUES ('{version}', '{stamp}');\n"
            "COMMIT;"
        )
        newly_applied.append(version)
    return newly_applied


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    apply_migrations(conn)
    return conn
