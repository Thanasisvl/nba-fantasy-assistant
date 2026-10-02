import gzip
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nfa.adapters.store import raw as raw_module
from nfa.adapters.store.db import open_db
from nfa.adapters.store.raw import RawStore, safe_key
from nfa.domain.raw import FetchRequest, RawFileId, RawResponse

AT = datetime(2026, 10, 21, 3, 15, 0, tzinfo=UTC)


def make(key: str = "466.l.1", status: int = 200, payload: bytes = b'{"ok":true}') -> RawResponse:
    request = FetchRequest("yahoo", "league_settings", key, {"path": f"league/{key}/settings"})
    return RawResponse(request=request, fetched_at=AT, status=status, payload=payload)


@pytest.fixture
def store(tmp_path: Path) -> RawStore:
    return RawStore(tmp_path, open_db(tmp_path / "app.sqlite"))


def test_path_layout(store: RawStore) -> None:
    raw_id = store.write_raw(make())
    assert raw_id == "yahoo/league_settings/2026-10-21/031500-466.l.1.json.gz"
    assert (store.root / raw_id).exists()


def test_round_trip(store: RawStore) -> None:
    original = make()
    assert store.read_raw(store.write_raw(original)) == original


def test_row_sha256_matches_payload(store: RawStore, tmp_path: Path) -> None:
    raw_id = store.write_raw(make())
    conn = open_db(tmp_path / "app.sqlite")
    sha = conn.execute("SELECT sha256 FROM raw_files WHERE raw_file_id=?", (raw_id,)).fetchone()[0]
    stored = gzip.decompress((store.root / raw_id).read_bytes())
    assert sha == hashlib.sha256(stored).hexdigest() == hashlib.sha256(b'{"ok":true}').hexdigest()


def test_failed_responses_are_stored_with_status(store: RawStore) -> None:
    raw_id = store.write_raw(make(status=503, payload=b"busy"))
    assert store.read_raw(raw_id).status == 503


def test_same_second_same_key_gets_suffix(store: RawStore) -> None:
    first = store.write_raw(make())
    second = store.write_raw(make())
    assert first != second and second.endswith("-2.json.gz")


def test_extension_follows_payload(store: RawStore) -> None:
    assert store.write_raw(make(key="a", payload=b"%PDF-1.7 ...")).endswith(".pdf.gz")
    assert store.write_raw(make(key="b", payload=b"<!doctype html>")).endswith(".html.gz")
    assert store.write_raw(make(key="c", payload=b"\x00\x01")).endswith(".bin.gz")


def test_write_raw_never_escapes_root(store: RawStore) -> None:
    raw_id = store.write_raw(make(key="../../etc/passwd; x,y z"))
    path = (store.root / raw_id).resolve()
    assert path.is_relative_to(store.root.resolve())
    assert "/" not in safe_key("../../etc/passwd") and not safe_key("..").startswith(".")


def test_read_unknown_id_raises(store: RawStore) -> None:
    with pytest.raises(KeyError):
        store.read_raw(RawFileId("nope"))


def test_atomic_write_leaves_nothing_on_failure(
    store: RawStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def boom(src: object, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(raw_module.os, "replace", boom)
    with pytest.raises(OSError):
        store.write_raw(make())
    assert [p for p in store.root.rglob("*") if p.is_file()] == []
    conn = open_db(tmp_path / "app.sqlite")
    assert conn.execute("SELECT COUNT(*) FROM raw_files").fetchone()[0] == 0
