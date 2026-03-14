"""
SQLite Datenbankschema für lebenmitcolitis.de Marketing Automation
Läuft lokal auf MacBook — kein Server nötig.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import DB_PATH


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Erstellt alle Tabellen falls noch nicht vorhanden."""
    conn = get_connection()
    with conn:
        # ── Pain/Gain Research ──────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_insights (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                datum       TEXT    NOT NULL DEFAULT (date('now')),
                typ         TEXT    NOT NULL,  -- 'pain', 'gain', 'job', 'quote'
                inhalt      TEXT    NOT NULL,
                quelle      TEXT,              -- Reddit, Amazon, Forum etc.
                url         TEXT,
                limbic_tag  TEXT,              -- 'balance', 'dominanz', 'stimulanz'
                motiv_tag   TEXT,              -- 'autonomie', 'zugehoerigkeit', 'kompetenz'
                verwendungen INTEGER DEFAULT 0,
                erstellt_am TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Media Buying Briefings (Perplexity) ─────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mediabuy_briefings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                datum       TEXT    NOT NULL DEFAULT (date('now')),
                plattform   TEXT    NOT NULL,  -- 'meta', 'google', 'allgemein'
                kategorie   TEXT    NOT NULL,  -- 'update', 'strategie', 'creative_trend', 'warnung'
                inhalt      TEXT    NOT NULL,
                quelle_url  TEXT,
                erstellt_am TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Generierte Ad Copies ─────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ad_copies (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                datum           TEXT    NOT NULL DEFAULT (date('now')),
                plattform       TEXT    NOT NULL,  -- 'meta', 'google'
                format          TEXT,              -- 'primary_text', 'headline', 'description'
                headline        TEXT,
                primary_text    TEXT,
                description     TEXT,
                cta             TEXT,
                limbic_segment  TEXT,
                tiefmotiv       TEXT,
                begruendung     TEXT,              -- Psychologische Begründung vom Agent
                status          TEXT    DEFAULT 'draft',  -- draft, approved, live, paused
                ad_id_extern    TEXT,              -- ID bei Meta/Google nach Upload
                ctr             REAL,
                cpa             REAL,
                roas            REAL,
                erstellt_am     TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Funnel Copy & Emails ─────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS funnel_copy (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                datum       TEXT    NOT NULL DEFAULT (date('now')),
                typ         TEXT    NOT NULL,  -- 'landing_page', 'order_bump', 'upsell_1', 'upsell_2', 'email'
                name        TEXT,              -- z.B. "Email Tag 3 - Kompetenz"
                inhalt      TEXT    NOT NULL,  -- HTML oder Markdown
                version     INTEGER DEFAULT 1,
                status      TEXT    DEFAULT 'draft',  -- draft, live, archiv
                cvr         REAL,              -- Conversion Rate wenn bekannt
                erstellt_am TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Creative Briefs & Assets ─────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS creatives (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                datum           TEXT    NOT NULL DEFAULT (date('now')),
                typ             TEXT    NOT NULL,  -- 'image', 'video', 'brief'
                name            TEXT,
                brief_text      TEXT,              -- Beschreibung für Imagen/Veo
                datei_pfad      TEXT,              -- Lokaler Pfad zum generierten Asset
                plattform       TEXT,              -- 'meta', 'google', 'beide'
                format          TEXT,              -- '1:1', '9:16', '16:9'
                status          TEXT    DEFAULT 'draft',
                ctr             REAL,
                erstellt_am     TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── KPI Snapshots (täglich) ──────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kpi_snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                datum           TEXT    NOT NULL DEFAULT (date('now')),
                plattform       TEXT    NOT NULL,  -- 'meta', 'google', 'gesamt'
                ad_spend        REAL    DEFAULT 0,
                impressionen    INTEGER DEFAULT 0,
                klicks          INTEGER DEFAULT 0,
                kaeufer         INTEGER DEFAULT 0,
                umsatz          REAL    DEFAULT 0,
                roas            REAL    DEFAULT 0,
                cpa             REAL    DEFAULT 0,
                cpl             REAL    DEFAULT 0,
                order_bump_rate REAL    DEFAULT 0,
                upsell_1_rate   REAL    DEFAULT 0,
                upsell_2_rate   REAL    DEFAULT 0,
                ltv_30          REAL    DEFAULT 0,
                erstellt_am     TEXT    DEFAULT (datetime('now')),
                UNIQUE(datum, plattform)
            )
        """)

    conn.close()
    print(f"[DB] Datenbank initialisiert: {DB_PATH}")


# ─── Helper Funktionen ──────────────────────────────────────────────────────────

def save_research_insight(typ: str, inhalt: str, quelle: str = None,
                           url: str = None, limbic_tag: str = None,
                           motiv_tag: str = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO research_insights (typ, inhalt, quelle, url, limbic_tag, motiv_tag)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (typ, inhalt, quelle, url, limbic_tag, motiv_tag)
        )
        return cur.lastrowid


def get_recent_insights(tage: int = 7, typ: str = None) -> list[dict]:
    conn = get_connection()
    query = """SELECT * FROM research_insights
               WHERE datum >= date('now', ?)"""
    params = [f"-{tage} days"]
    if typ:
        query += " AND typ = ?"
        params.append(typ)
    query += " ORDER BY datum DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_ad_copy(plattform: str, headline: str, primary_text: str,
                 description: str = None, cta: str = None,
                 limbic_segment: str = None, tiefmotiv: str = None,
                 begruendung: str = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO ad_copies
               (plattform, headline, primary_text, description, cta,
                limbic_segment, tiefmotiv, begruendung)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (plattform, headline, primary_text, description, cta,
             limbic_segment, tiefmotiv, begruendung)
        )
        return cur.lastrowid


def save_mediabuy_briefing(plattform: str, kategorie: str, inhalt: str,
                            quelle_url: str = None) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO mediabuy_briefings (plattform, kategorie, inhalt, quelle_url)
               VALUES (?, ?, ?, ?)""",
            (plattform, kategorie, inhalt, quelle_url)
        )
        return cur.lastrowid


def get_todays_briefing() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM mediabuy_briefings WHERE datum = date('now') ORDER BY plattform"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_kpi_snapshot(plattform: str, data: dict):
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO kpi_snapshots
               (datum, plattform, ad_spend, impressionen, klicks, kaeufer,
                umsatz, roas, cpa, cpl, order_bump_rate, upsell_1_rate, upsell_2_rate, ltv_30)
               VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (plattform,
             data.get("ad_spend", 0), data.get("impressionen", 0),
             data.get("klicks", 0), data.get("kaeufer", 0),
             data.get("umsatz", 0), data.get("roas", 0),
             data.get("cpa", 0), data.get("cpl", 0),
             data.get("order_bump_rate", 0), data.get("upsell_1_rate", 0),
             data.get("upsell_2_rate", 0), data.get("ltv_30", 0))
        )


def get_kpi_verlauf(tage: int = 30) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM kpi_snapshots
           WHERE datum >= date('now', ?)
           ORDER BY datum DESC, plattform""",
        (f"-{tage} days",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_connection()
    stats = {}
    for table in ["research_insights", "mediabuy_briefings", "ad_copies",
                  "funnel_copy", "creatives", "kpi_snapshots"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        stats[table] = count
    conn.close()
    return stats


if __name__ == "__main__":
    init_db()
    print("[DB] Stats:", get_stats())
