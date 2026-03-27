import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import config
from src.db.schema import get_connection
from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    if not config.MASTER_KEY:
        raise RuntimeError("DASHBOARD_MASTER_KEY not set in .env")
    return Fernet(config.MASTER_KEY.encode())


def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ── Clients ────────────────────────────────────────────────────────────────────

def list_clients(active_only: bool = True) -> list[dict]:
    conn = get_connection()
    try:
        q = "SELECT * FROM clients"
        if active_only:
            q += " WHERE is_active = 1"
        q += " ORDER BY name"
        return [dict(r) for r in conn.execute(q).fetchall()]
    finally:
        conn.close()


def get_client(client_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_client(name: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO clients (name, slug) VALUES (?, ?)",
            (name, _slug(name)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_client(client_id: int, name: str, is_active: bool):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE clients SET name=?, slug=?, is_active=?, updated_at=datetime('now') WHERE id=?",
            (name, _slug(name), int(is_active), client_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_client(client_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
    finally:
        conn.close()


# ── Credentials ────────────────────────────────────────────────────────────────

def save_credential(client_id: int, service: str, key: str, value: str):
    encrypted = _fernet().encrypt(value.encode())
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO api_credentials (client_id, service, credential_key, credential_val)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(client_id, service, credential_key)
               DO UPDATE SET credential_val=excluded.credential_val""",
            (client_id, service, key, encrypted),
        )
        conn.commit()
    finally:
        conn.close()


def get_credentials(client_id: int, service: str) -> dict[str, str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT credential_key, credential_val FROM api_credentials WHERE client_id=? AND service=?",
            (client_id, service),
        ).fetchall()
        f = _fernet()
        return {r["credential_key"]: f.decrypt(r["credential_val"]).decode() for r in rows}
    finally:
        conn.close()


def has_credentials(client_id: int, service: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM api_credentials WHERE client_id=? AND service=? LIMIT 1",
            (client_id, service),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
