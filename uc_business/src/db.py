"""
Datenbankschicht für das UC-Marketing-System.
SQLite mit WAL-Modus für Robustheit.
"""
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Erstellt alle Tabellen falls nicht vorhanden."""
    conn = get_connection()
    conn.executescript("""
        -- Kampagnen (Google Ads + Meta)
        CREATE TABLE IF NOT EXISTS campaigns (
            id              TEXT PRIMARY KEY,
            platform        TEXT NOT NULL,          -- google | meta
            name            TEXT NOT NULL,
            status          TEXT DEFAULT 'draft',   -- draft | active | paused | archived
            campaign_type   TEXT,                   -- search | display | lead_gen | retargeting
            budget_daily    REAL DEFAULT 0,
            target_cpa      REAL DEFAULT 0,
            platform_id     TEXT,                   -- ID beim jeweiligen Ad-System
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        -- Ad Creatives
        CREATE TABLE IF NOT EXISTS ad_creatives (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id     TEXT REFERENCES campaigns(id),
            platform        TEXT NOT NULL,
            format          TEXT,                   -- rsa | image | video | carousel
            headline_1      TEXT,
            headline_2      TEXT,
            headline_3      TEXT,
            body_text       TEXT,
            cta             TEXT,
            image_path      TEXT,
            status          TEXT DEFAULT 'generated', -- generated | active | paused | rejected
            impressions     INTEGER DEFAULT 0,
            clicks          INTEGER DEFAULT 0,
            conversions     INTEGER DEFAULT 0,
            spend           REAL DEFAULT 0,
            platform_id     TEXT,
            generated_at    TEXT DEFAULT (datetime('now')),
            activated_at    TEXT
        );

        -- Landing Page Varianten (A/B Tests)
        CREATE TABLE IF NOT EXISTS lp_variants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            page_type       TEXT NOT NULL,          -- optin | thankyou | sales | upsell
            variant_name    TEXT NOT NULL,
            html_path       TEXT,
            visits          INTEGER DEFAULT 0,
            conversions     INTEGER DEFAULT 0,
            active          INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        -- Email-Sequenzen
        CREATE TABLE IF NOT EXISTS email_sequences (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            trigger         TEXT NOT NULL,          -- optin | purchase_entry | purchase_upsell | inactive
            steps_json      TEXT,                   -- JSON-Array der Schritte
            active          INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        -- Subscriber / Leads
        CREATE TABLE IF NOT EXISTS subscribers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            email           TEXT UNIQUE NOT NULL,
            first_name      TEXT,
            source_utm      TEXT,                   -- utm_source
            utm_campaign    TEXT,
            utm_medium      TEXT,
            subscribed_at   TEXT DEFAULT (datetime('now')),
            status          TEXT DEFAULT 'lead',    -- lead | buyer | vip | unsubscribed
            tags            TEXT,                   -- JSON-Array
            provider_id     TEXT,                   -- ID beim Email-Provider
            last_activity   TEXT
        );

        -- Conversions / Käufe
        CREATE TABLE IF NOT EXISTS conversions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id   INTEGER REFERENCES subscribers(id),
            product_id      INTEGER REFERENCES products(id),
            revenue         REAL NOT NULL,
            channel         TEXT,                   -- google | meta | email | direct
            utm_source      TEXT,
            utm_campaign    TEXT,
            platform_order_id TEXT,
            converted_at    TEXT DEFAULT (datetime('now'))
        );

        -- Produkte
        CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL,          -- pdf | course | coaching
            price           REAL NOT NULL,
            platform_product_id TEXT,
            delivery_url    TEXT,
            description     TEXT,
            active          INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        -- Facebook-Gruppen Insights
        CREATE TABLE IF NOT EXISTS group_insights (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name      TEXT,
            post_text       TEXT,
            pain_points     TEXT,                   -- JSON-Array
            emotions        TEXT,                   -- JSON-Array
            keywords        TEXT,                   -- JSON-Array
            ad_hook         TEXT,                   -- Generierter Ad-Hook
            email_subject   TEXT,                   -- Generierte Email-Betreffzeile
            scraped_at      TEXT DEFAULT (datetime('now')),
            used_in_creative INTEGER DEFAULT 0
        );

        -- Tages-KPIs
        CREATE TABLE IF NOT EXISTS daily_kpis (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            platform        TEXT,                   -- google | meta | email | total
            impressions     INTEGER DEFAULT 0,
            clicks          INTEGER DEFAULT 0,
            spend           REAL DEFAULT 0,
            leads           INTEGER DEFAULT 0,
            sales           INTEGER DEFAULT 0,
            revenue         REAL DEFAULT 0,
            roas            REAL DEFAULT 0,
            cpl             REAL DEFAULT 0,         -- Cost per Lead
            cpa             REAL DEFAULT 0,         -- Cost per Acquisition
            recorded_at     TEXT DEFAULT (datetime('now')),
            UNIQUE(date, platform)
        );

        -- Orchestrator-Log
        CREATE TABLE IF NOT EXISTS orchestrator_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            action          TEXT NOT NULL,
            details         TEXT,
            result          TEXT,
            dry_run         INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ─── Insert-Funktionen ────────────────────────────────────────────────────────

def insert_campaign(platform: str, name: str, campaign_type: str,
                    budget_daily: float, target_cpa: float,
                    campaign_id: Optional[str] = None) -> str:
    import hashlib
    cid = campaign_id or hashlib.sha256(f"{platform}{name}".encode()).hexdigest()[:16]
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO campaigns
            (id, platform, name, campaign_type, budget_daily, target_cpa)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cid, platform, name, campaign_type, budget_daily, target_cpa))
    conn.commit()
    conn.close()
    return cid


def insert_creative(campaign_id: str, platform: str, format: str,
                    headline_1: str, body_text: str, cta: str,
                    headline_2: str = "", headline_3: str = "") -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO ad_creatives
            (campaign_id, platform, format, headline_1, headline_2, headline_3, body_text, cta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (campaign_id, platform, format, headline_1, headline_2, headline_3, body_text, cta))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def insert_subscriber(email: str, first_name: str = "", source_utm: str = "",
                      utm_campaign: str = "", utm_medium: str = "") -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT OR IGNORE INTO subscribers (email, first_name, source_utm, utm_campaign, utm_medium)
        VALUES (?, ?, ?, ?, ?)
    """, (email, first_name, source_utm, utm_campaign, utm_medium))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def insert_group_insight(group_name: str, post_text: str, pain_points: list,
                         emotions: list, keywords: list,
                         ad_hook: str = "", email_subject: str = "") -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO group_insights
            (group_name, post_text, pain_points, emotions, keywords, ad_hook, email_subject)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (group_name, post_text,
          json.dumps(pain_points, ensure_ascii=False),
          json.dumps(emotions, ensure_ascii=False),
          json.dumps(keywords, ensure_ascii=False),
          ad_hook, email_subject))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid


def upsert_daily_kpi(date_str: str, platform: str, **kwargs):
    conn = get_connection()
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values())
    conn.execute(f"""
        INSERT INTO daily_kpis (date, platform, {', '.join(kwargs.keys())})
        VALUES (?, ?, {', '.join('?' * len(kwargs))})
        ON CONFLICT(date, platform) DO UPDATE SET {fields}
    """, [date_str, platform, *values, *values])
    conn.commit()
    conn.close()


def log_orchestrator_action(action: str, details: str = "", result: str = "",
                             dry_run: bool = True):
    conn = get_connection()
    conn.execute("""
        INSERT INTO orchestrator_log (action, details, result, dry_run)
        VALUES (?, ?, ?, ?)
    """, (action, details, result, int(dry_run)))
    conn.commit()
    conn.close()


# ─── Query-Funktionen ─────────────────────────────────────────────────────────

def get_top_insights(limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM group_insights
        WHERE used_in_creative = 0
        ORDER BY scraped_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_campaigns(platform: str = None) -> list:
    conn = get_connection()
    if platform:
        rows = conn.execute(
            "SELECT * FROM campaigns WHERE status = 'active' AND platform = ?", (platform,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM campaigns WHERE status = 'active'"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_kpi_summary(days: int = 7) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT date, platform, impressions, clicks, spend, leads, sales, revenue, roas
        FROM daily_kpis
        WHERE date >= date('now', ?)
        ORDER BY date DESC, platform
    """, (f"-{days} days",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subscriber_count() -> dict:
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='lead' THEN 1 ELSE 0 END) as leads,
            SUM(CASE WHEN status='buyer' THEN 1 ELSE 0 END) as buyers,
            SUM(CASE WHEN status='vip' THEN 1 ELSE 0 END) as vips
        FROM subscribers
        WHERE status != 'unsubscribed'
    """).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_total_revenue() -> float:
    conn = get_connection()
    row = conn.execute("SELECT COALESCE(SUM(revenue), 0) as total FROM conversions").fetchone()
    conn.close()
    return row["total"] if row else 0.0


if __name__ == "__main__":
    init_db()
    print(f"[db] Datenbank initialisiert: {DB_PATH}")
