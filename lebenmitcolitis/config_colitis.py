"""
Konfiguration für lebenmitcolitis.de Marketing Automation
Alle API Keys via .env Datei setzen — niemals hardcoden!
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── LLM APIs ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")          # Gemini / Imagen / Veo
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# ─── Claude Modelle ─────────────────────────────────────────────────────────────
CLAUDE_SONNET = "claude-sonnet-4-6"       # Für Ad Copy, Research, Funnel
CLAUDE_HAIKU  = "claude-haiku-4-5-20251001"  # Für Analytics, einfache Tasks

# ─── Gemini Modelle ─────────────────────────────────────────────────────────────
GEMINI_FLASH    = "gemini-2.0-flash"
IMAGEN_MODEL    = "imagen-3.0-generate-002"
VEO_MODEL       = "veo-2.0-generate-001"

# ─── Ads APIs ───────────────────────────────────────────────────────────────────
META_ACCESS_TOKEN  = os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "")          # Format: act_XXXXXXXXX

GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID     = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
GOOGLE_ADS_CLIENT_ID       = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET   = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN   = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")

# ─── Email + Reporting ──────────────────────────────────────────────────────────
BREVO_API_KEY      = os.getenv("BREVO_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Perplexity ─────────────────────────────────────────────────────────────────
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL   = "sonar-pro"

# ─── Projekt ────────────────────────────────────────────────────────────────────
PROJECT_NAME = "lebenmitcolitis.de"
BRAND_URL    = "lebenmitcolitis.de"
NISCHE       = "Colitis Ulcerosa / Morbus Crohn"
ZIELGRUPPE   = "Betroffene mit Colitis Ulcerosa oder Morbus Crohn, 25–55 Jahre, DACH-Raum"
SPRACHE      = "de"

# ─── Value Ladder ───────────────────────────────────────────────────────────────
VALUE_LADDER = {
    "tiny_offer": {
        "name": "Colitis Code",
        "preis": 12,
        "beschreibung": "30-seitiger Leitfaden + Checklisten für ein Leben mit Colitis",
    },
    "order_bump": {
        "name": "Colitis Rezepte Quickstart",
        "preis": 27,
        "beschreibung": "Zusatz-Rezeptbuch mit 30 Colitis-freundlichen Rezepten",
    },
    "upsell_1": {
        "name": "Colitis Reset Protokoll",
        "preis": 67,
        "beschreibung": "8-Wochen Video-Kurs zur Symptomreduktion",
    },
    "upsell_2": {
        "name": "Colitis Community Mitgliedschaft",
        "preis": 27,  # monatlich
        "beschreibung": "Monatliche Mitgliedschaft: Rezepte, Live Q&As, Meal Plans",
    },
}

# ─── Verkaufspsychologie (Limbic Map + Motivkompass) ────────────────────────────
LIMBIC_PROFILE = {
    "primaer": "Balance",       # Sicherheit, Harmonie, Angstvermeidung
    "sekundaer": "Dominanz",    # Kontrolle zurückgewinnen
    "beschreibung": (
        "Colitis-Betroffene sitzen primär im Balance-Bereich: "
        "Sie wollen Sicherheit, Vorhersehbarkeit, Kontrolle über ihre Symptome. "
        "Sekundär Dominanz: nicht ausgeliefert sein, das Leben selbst bestimmen."
    ),
}

TIEFMOTIVE = [
    "Autonomie",      # Nicht von Symptomen kontrolliert werden
    "Zugehörigkeit",  # Andere Betroffene verstehen mich
    "Kompetenz",      # Ich verstehe meinen eigenen Körper
]

# ─── RAG / Knowledge Base ───────────────────────────────────────────────────────
KB_PATH      = "knowledge_base/chroma_db"
KB_DOCS_PATH = "knowledge_base/docs"
KB_CHUNK_SIZE    = 800
KB_CHUNK_OVERLAP = 100

# ─── Datenbank ──────────────────────────────────────────────────────────────────
DB_PATH = "data/colitis_marketing.db"

# ─── Output Verzeichnisse ────────────────────────────────────────────────────────
OUTPUT_DIR          = "output"
ADS_OUTPUT_DIR      = "output/ads"
CREATIVE_OUTPUT_DIR = "output/creatives"
VIDEO_OUTPUT_DIR    = "output/videos"
FUNNEL_OUTPUT_DIR   = "output/funnel"
REPORTS_DIR         = "output/reports"

# ─── Skalierung & Limits ─────────────────────────────────────────────────────────
ADS_PRO_TAG          = 5     # Neue Ad-Varianten täglich generieren
CREATIVES_PRO_WOCHE  = 20
DRY_RUN              = True  # True = nur Output, kein Auto-Upload zu Meta/Google
