"""Append-only raw file store: data/raw/{source}/{dataset}/{date}/{time}-{key}.{ext}.gz (ADR 0008).

Dates and times in paths are UTC. The extension follows the payload (json, pdf, html, bin).
"""

import gzip
import hashlib
import json
import os
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from nfa.domain.raw import FetchRequest, RawFileId, RawResponse

_UNSAFE = re.compile(r"[^A-Za-z0-9._=-]+")


def safe_key(key: str) -> str:
    cleaned = _UNSAFE.sub("_", key).strip("_").lstrip(".")
    return (cleaned or "key")[:120]


def _extension(payload: bytes) -> str:
    head = payload.lstrip()[:16].lower()
    if head.startswith((b"{", b"[")):
        return "json"
    if head.startswith(b"%pdf"):
        return "pdf"
    if head.startswith(b"<"):
        return "html"
    return "bin"


class RawStore:
    def __init__(self, data_dir: Path, conn: sqlite3.Connection) -> None:
        self.root = data_dir / "raw"
        self._conn = conn

    def write_raw(self, raw: RawResponse) -> RawFileId:
        request = raw.request
        at = raw.fetched_at.astimezone(UTC)
        folder = (
            self.root
            / safe_key(request.source)
            / safe_key(request.dataset)
            / at.strftime("%Y-%m-%d")
        )
        folder.mkdir(parents=True, exist_ok=True)
        stem = f"{at.strftime('%H%M%S')}-{safe_key(request.key)}"
        ext = _extension(raw.payload)
        target = folder / f"{stem}.{ext}.gz"
        suffix = 2
        while target.exists():
            target = folder / f"{stem}-{suffix}.{ext}.gz"
            suffix += 1
        tmp = target.with_name(target.name + ".tmp")
        try:
            tmp.write_bytes(gzip.compress(raw.payload))
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        raw_id = RawFileId(target.relative_to(self.root).as_posix())
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO raw_files (raw_file_id, source, dataset, request_key, params_json,"
                    " fetched_at, path, sha256, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        raw_id,
                        request.source,
                        request.dataset,
                        request.key,
                        json.dumps(dict(request.params), sort_keys=True),
                        at.isoformat(),
                        raw_id,
                        hashlib.sha256(raw.payload).hexdigest(),
                        raw.status,
                    ),
                )
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return raw_id

    def read_raw(self, raw_id: RawFileId) -> RawResponse:
        row = self._conn.execute(
            "SELECT source, dataset, request_key, params_json, fetched_at, status, sha256"
            " FROM raw_files WHERE raw_file_id = ?",
            (raw_id,),
        ).fetchone()
        if row is None:
            raise KeyError(raw_id)
        source, dataset, key, params_json, fetched_at, status, sha = row
        payload = gzip.decompress((self.root / raw_id).read_bytes())
        if hashlib.sha256(payload).hexdigest() != sha:
            raise ValueError(f"sha256 mismatch for {raw_id}")
        return RawResponse(
            request=FetchRequest(source, dataset, key, json.loads(params_json)),
            fetched_at=datetime.fromisoformat(fetched_at),
            status=status,
            payload=payload,
        )
