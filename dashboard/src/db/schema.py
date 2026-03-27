import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config

SCHEMA_VERSION = 1

MIGRATIONS = [
    (1, """
    CREATE TABLE IF NOT EXISTS clients (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL UNIQUE,
        slug       TEXT NOT NULL UNIQUE,
        is_active  INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS api_credentials (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id      INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        service        TEXT NOT NULL,
        credential_key TEXT NOT NULL,
        credential_val BLOB NOT NULL,
        UNIQUE(client_id, service, credential_key)
    );

    CREATE TABLE IF NOT EXISTS kpi_targets (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id        INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        month            TEXT NOT NULL,
        kpi_key          TEXT NOT NULL,
        target_value     REAL NOT NULL,
        target_direction TEXT NOT NULL DEFAULT 'minimize',
        UNIQUE(client_id, month, kpi_key)
    );

    CREATE TABLE IF NOT EXISTS data_cache (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id      INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        service        TEXT NOT NULL,
        date_range_key TEXT NOT NULL,
        payload        TEXT NOT NULL,
        fetched_at     TEXT NOT NULL DEFAULT (datetime('now')),
        expires_at     TEXT NOT NULL,
        UNIQUE(client_id, service, date_range_key)
    );

    CREATE TABLE IF NOT EXISTS refresh_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id   INTEGER REFERENCES clients(id),
        service     TEXT,
        status      TEXT,
        message     TEXT,
        duration_ms INTEGER,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """),
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations():
    conn = get_connection()
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, sql in MIGRATIONS:
        if version > current:
            conn.executescript(sql)
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
    conn.close()
