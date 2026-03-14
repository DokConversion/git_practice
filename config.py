"""
Konfiguration fuer die Outreach-Kampagne.
Sensitive Werte (API Keys) werden aus Umgebungsvariablen gelesen.
"""

import os

# --- API Keys ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# --- Facebook Ad Library ---
FB_AD_LIBRARY_URL = "https://www.facebook.com/ads/library/"
FB_AD_LIBRARY_API_URL = "https://www.facebook.com/ads/library/async/search_ads/"

# Suchbegriffe fuer Live-Webinar-Anzeigen
SEARCH_KEYWORDS = [
    "kostenloses Webinar",
    "Live Webinar",
    "kostenloser Workshop",
    "Live-Training",
    "Online-Seminar",
    "gratis Webinar",
    "kostenlose Masterclass",
    "Live Masterclass",
]

# DACH-Laendercodes
COUNTRIES = ["DE", "AT", "CH"]

# --- Outreach ---
SENDER_NAME = "Marc"
BRAND_URL = "quantum-bsl.com"

# Zielgruppen-Bezeichnungen (fuer personalisierte Nachrichten)
TARGET_LABELS = ["Coaches", "Berater", "Trainer", "Dienstleister"]

# --- Datenbank ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "leads.db")

# --- Nachrichtengenerierung ---
OUTREACH_STYLE = "dabei-gewesen"  # oder "oeffentliche-referenz"
FORMALITY = "du"  # "du" oder "sie"
PRIMARY_CHANNEL = "instagram"  # "instagram", "linkedin", "email"
