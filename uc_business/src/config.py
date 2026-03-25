"""
Konfiguration für das UC-Marketing-System.
Alle API-Keys kommen aus Umgebungsvariablen (.env Datei).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Claude / Anthropic ───────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_MODEL_SMART = "claude-sonnet-4-6"   # Für komplexere Aufgaben

# ─── Google Ads ───────────────────────────────────────────────────────────────
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")

# ─── Meta / Facebook ──────────────────────────────────────────────────────────
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "")   # Format: act_XXXXXXXXXX
META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")

# ─── Email-Marketing ─────────────────────────────────────────────────────────
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "activecampaign")  # activecampaign | mailchimp | getresponse
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY", "")
EMAIL_API_URL = os.getenv("EMAIL_API_URL", "")         # Für ActiveCampaign: https://ACCOUNT.api-us1.com
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "UC Insider")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "")

# ─── Produkt-Plattform ────────────────────────────────────────────────────────
PRODUCT_PLATFORM = os.getenv("PRODUCT_PLATFORM", "digistore24")  # digistore24 | elopage | teachable
PRODUCT_API_KEY = os.getenv("PRODUCT_API_KEY", "")
PRODUCT_API_SECRET = os.getenv("PRODUCT_API_SECRET", "")

# ─── Tracking ────────────────────────────────────────────────────────────────
GA4_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_API_SECRET = os.getenv("GA4_API_SECRET", "")

# ─── Business-Einstellungen ───────────────────────────────────────────────────
NICHE = "colitis_ulcerosa"
BRAND_NAME = "UC Insider"
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN", "uc-insider.de")
LANGUAGE = "de"
MARKET = "DACH"  # DE, AT, CH

# Produkt-Preise (EUR)
PRICE_LEAD_MAGNET = 0.0
PRICE_ENTRY_PRODUCT = 37.0   # UC Ernährungs-Kompass (PDF)
PRICE_UPSELL_PRODUCT = 247.0  # UC Selbsthilfe-System (Video-Kurs)

# Tagesbudgets (EUR)
DAILY_BUDGET_GOOGLE = float(os.getenv("DAILY_BUDGET_GOOGLE", "20.0"))
DAILY_BUDGET_META = float(os.getenv("DAILY_BUDGET_META", "15.0"))

# Target CPA
TARGET_CPA_LEAD = float(os.getenv("TARGET_CPA_LEAD", "2.5"))   # EUR pro Lead
TARGET_CPA_SALE = float(os.getenv("TARGET_CPA_SALE", "18.0"))  # EUR pro Sale

# ROAS-Schwellwerte für automatische Budget-Anpassung
ROAS_SCALE_UP_THRESHOLD = 3.0    # ROAS > 3.0 → Budget +25%
ROAS_SCALE_DOWN_THRESHOLD = 1.5  # ROAS < 1.5 → Budget -20%
BUDGET_ADJUST_MAX_PCT = 0.25     # Max. 25% Anpassung pro Tag

# ─── Datenbank ────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "uc_business.db")

# ─── System-Verhalten ─────────────────────────────────────────────────────────
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Facebook-Gruppen für Intelligence-Scraping (öffentliche Gruppen)
UC_FACEBOOK_GROUPS = [
    "Colitis.Ulcerosa.Deutschland",
    "CED.Colitis.Crohn.Gemeinschaft",
    "CU.Selbsthilfe.DACH",
    "Morbus.Crohn.Colitis.Ulcerosa.Community",
    "CED.Betroffene.Deutschland",
]

# Google Ads Starter-Keywords (Low Competition, DE/AT/CH)
GOOGLE_ADS_SEED_KEYWORDS = [
    "colitis ulcerosa ernährung",
    "colitis ulcerosa schub was tun",
    "colitis ulcerosa selbsthilfe",
    "colitis ulcerosa natürlich behandeln",
    "colitis ulcerosa symptome lindern",
    "colitis ulcerosa remission erreichen",
    "colitis ulcerosa erfahrungen",
    "colitis ulcerosa tagebuch",
    "colitis ulcerosa stressbewältigung",
    "colitis ulcerosa leaky gut",
    "chronisch entzündliche darmerkrankung ernährung",
    "ced ernährungsplan",
    "darm beruhigen colitis",
    "colitis schub überbrücken",
    "leben mit colitis ulcerosa",
    "colitis ulcerosa ohne medikamente",
    "colitis ulcerosa entzündung reduzieren",
    "colitis ulcerosa mikrobiom",
    "colitis ulcerosa psyche",
    "colitis ulcerosa sport",
]

# Negative Keywords Google Ads
GOOGLE_ADS_NEGATIVE_KEYWORDS = [
    "wikipedia", "icd", "diagnose stellen", "arzt", "krankenhaus",
    "stellenangebote", "jobs", "studium", "studien teilnehmen",
    "medikament kaufen", "rezept", "cortison", "mesalazin kaufen",
    "gratis", "kostenlos download", "torrent", "pdf free",
]
