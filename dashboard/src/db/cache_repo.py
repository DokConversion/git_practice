import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db.schema import get_connection


def get_cached(client_id: int, service: str, date_range_key: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT payload FROM data_cache
               WHERE client_id=? AND service=? AND date_range_key=?
               AND expires_at > datetime('now')""",
            (client_id, service, date_range_key),
        ).fetchone()
        return json.loads(row["payload"]) if row else None
    finally:
        conn.close()


def set_cache(client_id: int, service: str, date_range_key: str, payload: dict, ttl_seconds: int):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO data_cache (client_id, service, date_range_key, payload, expires_at)
               VALUES (?, ?, ?, ?, datetime('now', ?))
               ON CONFLICT(client_id, service, date_range_key)
               DO UPDATE SET payload=excluded.payload, fetched_at=datetime('now'), expires_at=excluded.expires_at""",
            (client_id, service, date_range_key, json.dumps(payload), f"+{ttl_seconds} seconds"),
        )
        conn.commit()
    finally:
        conn.close()


def invalidate_client(client_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM data_cache WHERE client_id=?", (client_id,))
        conn.commit()
    finally:
        conn.close()


def purge_expired():
    conn = get_connection()
    try:
        conn.execute("DELETE FROM data_cache WHERE expires_at < datetime('now')")
        conn.commit()
    finally:
        conn.close()


def log_refresh(client_id: int, service: str, status: str, message: str = "", duration_ms: int = 0):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO refresh_log (client_id, service, status, message, duration_ms) VALUES (?,?,?,?,?)",
            (client_id, service, status, message, duration_ms),
        )
        conn.commit()
    finally:
        conn.close()
