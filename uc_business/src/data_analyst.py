"""
UC Business — Data Analyst Agent
==================================
Zieht Daten aus allen Kanälen (Google Ads, Meta, Email, Produkte),
baut KPI-Dashboards, erkennt Anomalien und liefert wöchentliche
Optimierungsempfehlungen via Claude API.

Verwendung:
  python run.py --analyst          → Vollanalyse (7 Tage)
  python run.py --analyst --days 30 → 30-Tage-Analyse
"""
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


# ─── Datenstrukturen ──────────────────────────────────────────────────────────

@dataclass
class ChannelMetrics:
    """KPIs für einen einzelnen Kanal und Zeitraum."""
    channel: str
    date_from: date
    date_to: date
    impressions: int = 0
    clicks: int = 0
    spend_eur: float = 0.0
    leads: int = 0
    sales: int = 0
    revenue_eur: float = 0.0

    @property
    def ctr(self) -> float:
        return self.clicks / self.impressions if self.impressions else 0.0

    @property
    def cpl(self) -> float:
        return self.spend_eur / self.leads if self.leads else 0.0

    @property
    def cpa(self) -> float:
        return self.spend_eur / self.sales if self.sales else 0.0

    @property
    def roas(self) -> float:
        return self.revenue_eur / self.spend_eur if self.spend_eur else 0.0

    @property
    def conversion_rate_lead(self) -> float:
        return self.leads / self.clicks if self.clicks else 0.0

    @property
    def conversion_rate_sale(self) -> float:
        return self.sales / self.leads if self.leads else 0.0


@dataclass
class FunnelSnapshot:
    """Konversions-Trichter von Impression bis Kauf."""
    impressions: int = 0
    clicks: int = 0
    optin_visits: int = 0
    optins: int = 0
    sales_page_visits: int = 0
    sales: int = 0
    upsell_shown: int = 0
    upsell_sales: int = 0

    @property
    def ctr(self) -> str:
        r = self.clicks / self.impressions if self.impressions else 0
        return f"{r:.1%}"

    @property
    def optin_rate(self) -> str:
        r = self.optins / self.optin_visits if self.optin_visits else 0
        return f"{r:.1%}"

    @property
    def sales_rate(self) -> str:
        r = self.sales / self.sales_page_visits if self.sales_page_visits else 0
        return f"{r:.1%}"

    @property
    def upsell_rate(self) -> str:
        r = self.upsell_sales / self.upsell_shown if self.upsell_shown else 0
        return f"{r:.1%}"


@dataclass
class AnalystReport:
    """Vollständiger Analysebericht."""
    generated_at: datetime = field(default_factory=datetime.now)
    period_days: int = 7
    channels: list[ChannelMetrics] = field(default_factory=list)
    funnel: FunnelSnapshot = field(default_factory=FunnelSnapshot)
    anomalies: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    ai_commentary: str = ""
    raw_totals: dict = field(default_factory=dict)


# ─── Datenbankabfragen ────────────────────────────────────────────────────────

def _load_kpis_from_db(db_path: str, days: int) -> list[dict]:
    """Lädt daily_kpis aus SQLite für die letzten N Tage."""
    since = date.today() - timedelta(days=days)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM daily_kpis WHERE date >= ? ORDER BY date DESC",
            (since.isoformat(),)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"DB-Abfrage fehlgeschlagen: {e}")
        return []


def _load_conversions_from_db(db_path: str, days: int) -> list[dict]:
    since = date.today() - timedelta(days=days)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM conversions WHERE converted_at >= ? ORDER BY converted_at DESC",
            (since.isoformat(),)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Conversions-Abfrage fehlgeschlagen: {e}")
        return []


# ─── Metriken aggregieren ─────────────────────────────────────────────────────

def _aggregate_by_channel(kpis: list[dict], days: int) -> list[ChannelMetrics]:
    channels: dict[str, ChannelMetrics] = {}
    date_to = date.today()
    date_from = date_to - timedelta(days=days)

    for row in kpis:
        ch = row.get("platform", "unknown")
        if ch not in channels:
            channels[ch] = ChannelMetrics(channel=ch, date_from=date_from, date_to=date_to)
        m = channels[ch]
        m.impressions += row.get("impressions", 0)
        m.clicks += row.get("clicks", 0)
        m.spend_eur += row.get("spend", 0.0)
        m.leads += row.get("leads", 0)
        m.sales += row.get("sales", 0)
        m.revenue_eur += row.get("revenue", 0.0)

    return list(channels.values())


def _build_funnel(kpis: list[dict], conversions: list[dict]) -> FunnelSnapshot:
    f = FunnelSnapshot()
    for row in kpis:
        f.impressions += row.get("impressions", 0)
        f.clicks += row.get("clicks", 0)
        f.leads += row.get("leads", 0) if hasattr(f, "leads") else 0
    f.optins = sum(r.get("leads", 0) for r in kpis)
    f.sales = sum(1 for c in conversions if c.get("product_type") == "entry")
    f.upsell_sales = sum(1 for c in conversions if c.get("product_type") == "upsell")
    f.optin_visits = f.clicks
    f.sales_page_visits = f.optins
    f.upsell_shown = f.sales
    return f


# ─── Anomalie-Erkennung ───────────────────────────────────────────────────────

def _detect_anomalies(channels: list[ChannelMetrics]) -> list[str]:
    """Regelbasierte Anomalie-Erkennung."""
    from src.config import TARGET_CPA_LEAD, TARGET_CPA_SALE, ROAS_SCALE_DOWN_THRESHOLD, PAUSE_CTR_THRESHOLD  # noqa
    anomalies = []

    for m in channels:
        if m.impressions > 200 and m.ctr < PAUSE_CTR_THRESHOLD:
            anomalies.append(
                f"[{m.channel.upper()}] CTR kritisch niedrig: {m.ctr:.2%} "
                f"(Ziel: >{PAUSE_CTR_THRESHOLD:.0%}) — Creatives prüfen!"
            )
        if m.leads > 0 and m.cpl > TARGET_CPA_LEAD * 1.5:
            anomalies.append(
                f"[{m.channel.upper()}] CPL zu hoch: €{m.cpl:.2f} "
                f"(Ziel: <€{TARGET_CPA_LEAD:.2f}) — Targeting prüfen!"
            )
        if m.sales > 0 and m.cpa > TARGET_CPA_SALE * 1.5:
            anomalies.append(
                f"[{m.channel.upper()}] CPA zu hoch: €{m.cpa:.2f} "
                f"(Ziel: <€{TARGET_CPA_SALE:.2f}) — Funnel prüfen!"
            )
        if m.spend_eur > 10 and m.roas < ROAS_SCALE_DOWN_THRESHOLD:
            anomalies.append(
                f"[{m.channel.upper()}] ROAS kritisch: {m.roas:.2f} "
                f"(Ziel: >{ROAS_SCALE_DOWN_THRESHOLD}) — Budget reduzieren!"
            )

    return anomalies


# ─── AI-Kommentar (Claude) ────────────────────────────────────────────────────

def _generate_ai_commentary(report: AnalystReport, dry_run: bool) -> str:
    """Claude analysiert die Zahlen und gibt strategische Empfehlungen."""
    if dry_run:
        return "[DRY-RUN] AI-Kommentar nicht generiert."

    try:
        from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART  # noqa
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        totals = report.raw_totals
        funnel = report.funnel
        anomalies_text = "\n".join(report.anomalies) or "Keine Anomalien."

        prompt = f"""Du bist ein datengetriebener Marketing-Analyst für ein deutsches Online-Business 
rund um das Thema Colitis Ulcerosa. Analysiere folgende KPIs der letzten {report.period_days} Tage 
und gib 3-5 konkrete, priorisierte Handlungsempfehlungen. Sei direkt, präzise, ohne Floskeln.

GESAMT-KPIs ({report.period_days} Tage):
- Impressionen: {totals.get('impressions', 0):,}
- Klicks: {totals.get('clicks', 0):,}
- Ausgaben: €{totals.get('spend', 0):.2f}
- Leads (Opt-ins): {totals.get('leads', 0)}
- Verkäufe: {totals.get('sales', 0)}
- Umsatz: €{totals.get('revenue', 0):.2f}
- ROAS gesamt: {totals.get('revenue', 0) / totals.get('spend', 1):.2f}x

FUNNEL:
- CTR: {funnel.ctr}
- Opt-in Rate: {funnel.optin_rate}
- Sales Rate: {funnel.sales_rate}
- Upsell Rate: {funnel.upsell_rate}

ANOMALIEN:
{anomalies_text}

Format: Nummerierte Liste, jeder Punkt: [PRIORITÄT: HOCH/MITTEL/NIEDRIG] Handlung: Begründung"""

        resp = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

    except Exception as e:
        logger.error(f"AI-Kommentar fehlgeschlagen: {e}")
        return f"AI-Kommentar nicht verfügbar: {e}"


# ─── Report drucken ───────────────────────────────────────────────────────────

def print_analyst_report(report: AnalystReport):
    """Formatierter Report auf der Konsole."""
    t = report.raw_totals
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  DATA ANALYST — Report ({report.period_days}-Tage-Analyse)
║  Erstellt: {report.generated_at.strftime('%d.%m.%Y %H:%M')}
╚══════════════════════════════════════════════════════════════╝

── GESAMT-KPIs ──────────────────────────────────────────────
  Impressionen:   {t.get('impressions', 0):>12,}
  Klicks:         {t.get('clicks', 0):>12,}
  CTR:            {t.get('ctr', 0):>11.2%}
  Werbeausgaben:  {t.get('spend', 0):>11.2f} €
  Leads:          {t.get('leads', 0):>12,}
  CPL:            {t.get('cpl', 0):>11.2f} €
  Verkäufe:       {t.get('sales', 0):>12,}
  CPA:            {t.get('cpa', 0):>11.2f} €
  Umsatz:         {t.get('revenue', 0):>11.2f} €
  ROAS:           {t.get('roas', 0):>11.2f}x

── NACH KANAL ────────────────────────────────────────────────""")

    for m in report.channels:
        print(f"  [{m.channel.upper():12}]  "
              f"Spend: €{m.spend_eur:6.2f}  "
              f"Leads: {m.leads:4}  "
              f"Sales: {m.sales:3}  "
              f"ROAS: {m.roas:.2f}x  "
              f"CPL: €{m.cpl:.2f}")

    print(f"""
── FUNNEL ────────────────────────────────────────────────────
  Impressionen → Klicks:       {report.funnel.ctr}
  Klicks → Opt-in:             {report.funnel.optin_rate}
  Opt-in → Kauf:               {report.funnel.sales_rate}
  Kauf → Upsell:               {report.funnel.upsell_rate}

── ANOMALIEN ─────────────────────────────────────────────────""")

    if report.anomalies:
        for a in report.anomalies:
            print(f"  ⚠  {a}")
    else:
        print("  ✓  Keine Anomalien erkannt.")

    print(f"""
── AI-EMPFEHLUNGEN ───────────────────────────────────────────
{report.ai_commentary}
""")


# ─── Haupt-Einstiegspunkt ─────────────────────────────────────────────────────

def run(db_path: str, days: int = 7, dry_run: bool = True) -> AnalystReport:
    """Führt die vollständige Datenanalyse durch."""
    logger.info(f"Data Analyst gestartet (letzte {days} Tage, dry_run={dry_run})")

    kpis = _load_kpis_from_db(db_path, days)
    conversions = _load_conversions_from_db(db_path, days)
    channels = _aggregate_by_channel(kpis, days)
    funnel = _build_funnel(kpis, conversions)

    # Gesamttotale
    total_impressions = sum(m.impressions for m in channels)
    total_clicks = sum(m.clicks for m in channels)
    total_spend = sum(m.spend_eur for m in channels)
    total_leads = sum(m.leads for m in channels)
    total_sales = sum(m.sales for m in channels)
    total_revenue = sum(m.revenue_eur for m in channels)

    raw_totals = {
        "impressions": total_impressions,
        "clicks": total_clicks,
        "ctr": total_clicks / total_impressions if total_impressions else 0,
        "spend": total_spend,
        "leads": total_leads,
        "cpl": total_spend / total_leads if total_leads else 0,
        "sales": total_sales,
        "cpa": total_spend / total_sales if total_sales else 0,
        "revenue": total_revenue,
        "roas": total_revenue / total_spend if total_spend else 0,
    }

    report = AnalystReport(
        period_days=days,
        channels=channels,
        funnel=funnel,
        anomalies=_detect_anomalies(channels),
        raw_totals=raw_totals,
    )
    report.ai_commentary = _generate_ai_commentary(report, dry_run)

    return report
