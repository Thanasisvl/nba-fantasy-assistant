CREATE TABLE raw_files (
    raw_file_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    dataset TEXT NOT NULL,
    request_key TEXT NOT NULL,
    params_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    status INTEGER NOT NULL,
    parsed_build_id TEXT
);
CREATE INDEX raw_files_by_dataset ON raw_files (source, dataset, fetched_at);
