"""Copy raw files into tests/fixtures/raw/ with private data removed (kept for M1).

Usage: uv run python scripts/spike/scrub_fixture.py <raw_file_id> [<raw_file_id> ...]
Raw file IDs are paths relative to data/raw/, as printed by the probes.
"""

import contextlib
import gzip
import json
import sys
from pathlib import Path

from nfa.adapters.platforms.yahoo.auth import Tokens
from nfa.adapters.secrets import MissingSecretError, get_secret
from nfa.adapters.store.db import open_db
from nfa.adapters.store.raw import RawStore
from nfa.config import load_config
from nfa.devtools.scrub import UnsafeFixtureError, scrub_payload
from nfa.domain.raw import RawFileId

FIXTURES = Path("tests/fixtures/raw")


def forbidden_values() -> list[str]:
    values: list[str] = []
    for account in ("yahoo_client_id", "yahoo_client_secret"):
        with contextlib.suppress(MissingSecretError):
            values.append(get_secret(account))
    try:
        tokens = Tokens.from_json(get_secret("yahoo_tokens"))
        values += [tokens.access_token, tokens.refresh_token]
    except MissingSecretError:
        pass
    return values


def main(raw_ids: list[str]) -> int:
    config = load_config()
    store = RawStore(config.data_dir, open_db(config.data_dir / "app.sqlite"))
    forbidden = forbidden_values()
    failures = 0
    for raw_id in raw_ids:
        raw = store.read_raw(RawFileId(raw_id))
        try:
            cleaned = scrub_payload(raw.payload, forbidden)
        except UnsafeFixtureError as exc:
            print(f"SKIPPED {raw_id}: {exc}")
            failures += 1
            continue
        dest = FIXTURES / raw_id
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(gzip.compress(cleaned))
        meta = {
            "source": raw.request.source,
            "dataset": raw.request.dataset,
            "key": raw.request.key,
            "params": dict(raw.request.params),
            "fetched_at": raw.fetched_at.isoformat(),
            "status": raw.status,
        }
        dest.with_name(dest.name + ".meta.json").write_text(json.dumps(meta, indent=1))
        print(f"wrote {dest}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
