import os
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "dashboard.db")

# ── Security ───────────────────────────────────────────────────────────────────
MASTER_KEY = os.environ.get("DASHBOARD_MASTER_KEY", "")

# ── Cache TTLs (seconds) ───────────────────────────────────────────────────────
CACHE_TTL = {
    "today_meta":     15 * 60,
    "today_ga4":       4 * 3600,
    "today_close":    30 * 60,
    "recent":          6 * 3600,   # yesterday, last 7d
    "month":          12 * 3600,   # last 30d, this month
    "historical":     24 * 3600,   # fully past custom ranges
}

# ── Traffic light thresholds ───────────────────────────────────────────────────
TRAFFIC_GREEN_PCT  = 0.10   # ≤ 10 % deviation → green
TRAFFIC_YELLOW_PCT = 0.25   # ≤ 25 % deviation → yellow  (>25 % → red)

# ── UI colours ─────────────────────────────────────────────────────────────────
COLOR_GREEN  = "#28a745"
COLOR_YELLOW = "#ffc107"
COLOR_RED    = "#dc3545"
COLOR_GREY   = "#6c757d"
COLOR_BLUE   = "#0d6efd"

# ── Date range presets (label → (offset_days_from, offset_days_to)) ────────────
DATE_PRESETS = {
    "Heute":            (0, 0),
    "Gestern":          (-1, -1),
    "Letzte 7 Tage":    (-6, 0),
    "Letzte 30 Tage":   (-29, 0),
    "Dieser Monat":     None,   # handled separately
    "Individuell":      None,   # date picker shown
}
