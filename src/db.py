"""
SQLite-Datenbank fuer Leads und Outreach-Tracking.
"""

import sqlite3
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ads (
            id TEXT PRIMARY KEY,
            advertiser_name TEXT,
            ad_text TEXT,
            landing_page_url TEXT,
            search_keyword TEXT,
            country TEXT,
            found_at TEXT DEFAULT (datetime('now')),
            UNIQUE(advertiser_name, landing_page_url)
        );

        CREATE TABLE IF NOT EXISTS webinars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT REFERENCES ads(id),
            webinar_date TEXT,
            webinar_topic TEXT,
            landing_page_content TEXT,
            parsed_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT REFERENCES ads(id),
            name TEXT,
            instagram_handle TEXT,
            linkedin_url TEXT,
            email TEXT,
            website_url TEXT,
            found_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER REFERENCES contacts(id),
            webinar_id INTEGER REFERENCES webinars(id),
            channel TEXT,
            message_text TEXT,
            generated_at TEXT DEFAULT (datetime('now')),
            sent_at TEXT,
            status TEXT DEFAULT 'generated'
        );
    """)
    conn.commit()
    conn.close()


def insert_ad(ad_id: str, advertiser_name: str, ad_text: str,
              landing_page_url: str, search_keyword: str, country: str) -> bool:
    """Fuegt eine Anzeige ein. Gibt True zurueck wenn neu, False wenn Duplikat."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO ads (id, advertiser_name, ad_text, landing_page_url, search_keyword, country) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ad_id, advertiser_name, ad_text, landing_page_url, search_keyword, country),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def insert_webinar(ad_id: str, webinar_date: str, webinar_topic: str,
                   landing_page_content: str = "") -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO webinars (ad_id, webinar_date, webinar_topic, landing_page_content) "
            "VALUES (?, ?, ?, ?)",
            (ad_id, webinar_date, webinar_topic, landing_page_content),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_contact(ad_id: str, name: str, instagram_handle: str = "",
                   linkedin_url: str = "", email: str = "",
                   website_url: str = "") -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO contacts (ad_id, name, instagram_handle, linkedin_url, email, website_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ad_id, name, instagram_handle, linkedin_url, email, website_url),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_outreach(contact_id: int, webinar_id: int, channel: str,
                    message_text: str) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO outreach (contact_id, webinar_id, channel, message_text) "
            "VALUES (?, ?, ?, ?)",
            (contact_id, webinar_id, channel, message_text),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def mark_sent(outreach_id: int):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE outreach SET status = 'sent', sent_at = datetime('now') WHERE id = ?",
            (outreach_id,),
        )
        conn.commit()
    finally:
        conn.close()


def get_yesterdays_webinars():
    """Gibt alle Webinare zurueck, die gestern stattgefunden haben."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT w.*, a.advertiser_name, a.ad_text, a.landing_page_url
            FROM webinars w
            JOIN ads a ON w.ad_id = a.id
            WHERE date(w.webinar_date) = date('now', '-1 day')
            AND w.id NOT IN (SELECT webinar_id FROM outreach WHERE webinar_id IS NOT NULL)
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_contact_for_ad(ad_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE ad_id = ? LIMIT 1", (ad_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pending_outreach():
    """Gibt alle generierten aber noch nicht gesendeten Nachrichten zurueck."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT o.*, c.name, c.instagram_handle, c.linkedin_url, c.email
            FROM outreach o
            JOIN contacts c ON o.contact_id = c.id
            WHERE o.status = 'generated'
            ORDER BY o.generated_at
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Datenbank initialisiert: {config.DB_PATH}")
