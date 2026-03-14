"""
Analytics & Optimization Agent
Täglicher KPI-Report + Telegram-Notification an Marc.
Liest Meta Ads API + Google Ads API, berechnet ROAS/CPA/LTV.
Eskaliert bei Problemen (CPA > Schwellwert, Budget läuft leer).
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    ANTHROPIC_API_KEY, CLAUDE_HAIKU,
    META_ACCESS_TOKEN, META_AD_ACCOUNT_ID,
    GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CUSTOMER_ID,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    VALUE_LADDER, PROJECT_NAME, REPORTS_DIR
)
from db_colitis import save_kpi_snapshot, get_kpi_verlauf, init_db

try:
    import anthropic
except ImportError:
    anthropic = None


# ─── Schwellwerte für Eskalation ─────────────────────────────────────────────────
KPI_SCHWELLWERTE = {
    "max_cpa":           25.0,   # €25 — darüber → Warnung
    "min_roas":           1.5,   # Unter 1.5x → Warnung
    "min_tiny_offer_cvr": 0.03,  # 3% — darunter → Optimierung nötig
    "min_order_bump_rate":0.15,  # 15% — darunter → Copy testen
    "min_upsell_1_rate":  0.12,  # 12% — darunter → Upsell-Video prüfen
}


# ─── Meta Ads API ────────────────────────────────────────────────────────────────

def hole_meta_kpis(datum: str = None) -> dict:
    """Holt KPIs aus der Meta Ads API."""
    if not META_ACCESS_TOKEN or not META_AD_ACCOUNT_ID:
        return _simulierte_meta_daten()

    if not datum:
        datum = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    url = (
        f"https://graph.facebook.com/v19.0/{META_AD_ACCOUNT_ID}/insights"
        f"?fields=spend,impressions,clicks,actions,action_values,cost_per_action_type"
        f"&time_range={{'since':'{datum}','until':'{datum}'}}"
        f"&access_token={META_ACCESS_TOKEN}"
    )

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", [{}])[0]

            spend      = float(data.get("spend", 0))
            impressionen = int(data.get("impressions", 0))
            klicks     = int(data.get("clicks", 0))

            # Käufe aus Actions extrahieren
            actions = data.get("actions", [])
            kaeufer = next(
                (int(a["value"]) for a in actions if a["action_type"] == "purchase"), 0
            )
            umsatz = next(
                (float(v["value"]) for v in data.get("action_values", [])
                 if v["action_type"] == "purchase"), 0.0
            )

            return {
                "ad_spend": spend, "impressionen": impressionen,
                "klicks": klicks, "kaeufer": kaeufer, "umsatz": umsatz,
                "roas": umsatz / spend if spend > 0 else 0,
                "cpa": spend / kaeufer if kaeufer > 0 else 0,
                "cpl": spend / klicks if klicks > 0 else 0,
            }
    except Exception as e:
        print(f"  [Meta API] Fehler: {e} — nutze Simulation")
        return _simulierte_meta_daten()


def _simulierte_meta_daten() -> dict:
    """Platzhalter-Daten wenn keine API-Keys gesetzt."""
    return {
        "ad_spend": 0, "impressionen": 0, "klicks": 0,
        "kaeufer": 0, "umsatz": 0, "roas": 0, "cpa": 0, "cpl": 0,
        "_hinweis": "Meta API Keys fehlen — bitte META_ACCESS_TOKEN in .env setzen"
    }


# ─── Google Ads API (vereinfacht via REST) ───────────────────────────────────────

def hole_google_kpis(datum: str = None) -> dict:
    """Holt KPIs aus Google Ads (Grundimplementierung — vollständige OAuth-Integration later)."""
    if not GOOGLE_ADS_DEVELOPER_TOKEN or not GOOGLE_ADS_CUSTOMER_ID:
        return _simulierte_google_daten()

    # Vollständige Google Ads API Integration benötigt google-ads Python Library
    # Hier Platzhalter — erweiterbar mit: pip install google-ads
    return _simulierte_google_daten()


def _simulierte_google_daten() -> dict:
    return {
        "ad_spend": 0, "impressionen": 0, "klicks": 0,
        "kaeufer": 0, "umsatz": 0, "roas": 0, "cpa": 0, "cpl": 0,
        "_hinweis": "Google Ads API Keys fehlen — bitte GOOGLE_ADS_* in .env setzen"
    }


# ─── KPI Analyse mit Claude ──────────────────────────────────────────────────────

def analysiere_kpis(meta: dict, google: dict, verlauf: list[dict]) -> str:
    """Lässt Claude Haiku die KPIs analysieren und Empfehlungen geben."""
    if not anthropic or not ANTHROPIC_API_KEY:
        return _kpi_basis_analyse(meta, google)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    gesamt_spend  = meta.get("ad_spend", 0) + google.get("ad_spend", 0)
    gesamt_umsatz = meta.get("umsatz", 0) + google.get("umsatz", 0)
    gesamt_roas   = gesamt_umsatz / gesamt_spend if gesamt_spend > 0 else 0

    verlauf_7 = verlauf[:7]
    verlauf_text = "\n".join([
        f"  {v['datum']}: Spend €{v['ad_spend']:.0f}, Umsatz €{v['umsatz']:.0f}, "
        f"ROAS {v['roas']:.1f}x, CPA €{v['cpa']:.0f}"
        for v in verlauf_7
    ]) if verlauf_7 else "  Noch keine historischen Daten"

    prompt = f"""Analysiere folgende Tages-KPIs für {PROJECT_NAME}:

HEUTE:
Meta:   Spend €{meta['ad_spend']:.2f}, Käufer {meta['kaeufer']}, ROAS {meta['roas']:.2f}x, CPA €{meta['cpa']:.2f}
Google: Spend €{google['ad_spend']:.2f}, Käufer {google['kaeufer']}, ROAS {google['roas']:.2f}x, CPA €{google['cpa']:.2f}
Gesamt: Spend €{gesamt_spend:.2f}, Umsatz €{gesamt_umsatz:.2f}, ROAS {gesamt_roas:.2f}x

SCHWELLWERTE: Max CPA €{KPI_SCHWELLWERTE['max_cpa']}, Min ROAS {KPI_SCHWELLWERTE['min_roas']}x

7-TAGE VERLAUF:
{verlauf_text}

Gib eine kurze Analyse (3-5 Sätze) mit:
1. Status (Gut/Optimierungsbedarf/Warnung)
2. Konkrete Empfehlung (Budget erhöhen/senken, Creative testen, etc.)
3. Prognose wenn Trend anhält

Antworte auf Deutsch, präzise und handlungsorientiert."""

    try:
        response = client.messages.create(
            model=CLAUDE_HAIKU,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return _kpi_basis_analyse(meta, google)


def _kpi_basis_analyse(meta: dict, google: dict) -> str:
    gesamt_spend = meta.get("ad_spend", 0) + google.get("ad_spend", 0)
    if gesamt_spend == 0:
        return "Keine Ad-Spend-Daten vorhanden. API Keys prüfen oder erste Kampagnen live schalten."
    gesamt_roas = (meta.get("umsatz", 0) + google.get("umsatz", 0)) / gesamt_spend
    if gesamt_roas >= KPI_SCHWELLWERTE["min_roas"]:
        return f"ROAS {gesamt_roas:.1f}x — über Zielwert. Budget skalieren empfohlen."
    return f"ROAS {gesamt_roas:.1f}x — unter Zielwert ({KPI_SCHWELLWERTE['min_roas']}x). Creatives testen."


# ─── Telegram Reporting ──────────────────────────────────────────────────────────

def erstelle_telegram_nachricht(meta: dict, google: dict,
                                 analyse: str, datum: str) -> str:
    """Erstellt formatierte Telegram-Nachricht für Marc."""
    gesamt_spend  = meta.get("ad_spend", 0) + google.get("ad_spend", 0)
    gesamt_umsatz = meta.get("umsatz", 0) + google.get("umsatz", 0)
    gesamt_roas   = gesamt_umsatz / gesamt_spend if gesamt_spend > 0 else 0
    gesamt_kaeufer = meta.get("kaeufer", 0) + google.get("kaeufer", 0)

    # Status-Emoji
    if gesamt_roas >= 2.5:
        status = "🟢"
    elif gesamt_roas >= KPI_SCHWELLWERTE["min_roas"]:
        status = "🟡"
    else:
        status = "🔴"

    msg = f"""{status} *{PROJECT_NAME} — KPI Report {datum}*

💶 Ad-Spend: €{gesamt_spend:.2f}
💰 Umsatz:   €{gesamt_umsatz:.2f}
📈 ROAS:     {gesamt_roas:.2f}x
🛒 Käufer:   {gesamt_kaeufer}
💸 CPA:      €{gesamt_spend/gesamt_kaeufer:.2f}" if gesamt_kaeufer > 0 else "—"}

*META:*
  Spend: €{meta['ad_spend']:.2f} | ROAS: {meta['roas']:.2f}x | CPA: €{meta['cpa']:.2f}

*GOOGLE:*
  Spend: €{google['ad_spend']:.2f} | ROAS: {google['roas']:.2f}x | CPA: €{google['cpa']:.2f}

*KI-Analyse:*
{analyse}

_Nächste Aktion bis morgen Früh definieren_"""

    return msg


def sende_telegram(nachricht: str) -> bool:
    """Sendet Nachricht via Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [Telegram] Kein Token/Chat ID — Nachricht wird nur lokal gespeichert")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": nachricht,
        "parse_mode": "Markdown",
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            print("  [Telegram] Report gesendet ✓")
            return True
    except Exception as e:
        print(f"  [Telegram] Fehler: {e}")
        return False


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run() -> dict:
    """Führt den Analytics Agent aus."""
    print(f"\n{'='*60}")
    print(f"[Analytics Agent] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    datum = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # KPIs holen
    print(f"[Analytics] Hole Meta KPIs für {datum}...")
    meta = hole_meta_kpis(datum)

    print(f"[Analytics] Hole Google KPIs für {datum}...")
    google = hole_google_kpis(datum)

    # Speichern
    save_kpi_snapshot("meta", meta)
    save_kpi_snapshot("google", google)
    save_kpi_snapshot("gesamt", {
        "ad_spend": meta["ad_spend"] + google["ad_spend"],
        "impressionen": meta["impressionen"] + google["impressionen"],
        "klicks": meta["klicks"] + google["klicks"],
        "kaeufer": meta["kaeufer"] + google["kaeufer"],
        "umsatz": meta["umsatz"] + google["umsatz"],
        "roas": (meta["umsatz"] + google["umsatz"]) / max(meta["ad_spend"] + google["ad_spend"], 0.01),
        "cpa": (meta["ad_spend"] + google["ad_spend"]) / max(meta["kaeufer"] + google["kaeufer"], 1),
    })

    # Verlauf laden
    verlauf = get_kpi_verlauf(tage=7)

    # Claude Analyse
    print("[Analytics] Claude analysiert KPIs...")
    analyse = analysiere_kpis(meta, google, verlauf)

    # Telegram
    nachricht = erstelle_telegram_nachricht(meta, google, analyse, datum)
    sende_telegram(nachricht)

    # Lokal speichern
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    report_pfad = f"{REPORTS_DIR}/kpi_report_{datum}.md"
    Path(report_pfad).write_text(nachricht.replace("*", "**"), encoding="utf-8")
    print(f"  → Report: {report_pfad}")

    print("\n" + analyse)
    return {"meta": meta, "google": google, "analyse": analyse}


if __name__ == "__main__":
    init_db()
    run()
