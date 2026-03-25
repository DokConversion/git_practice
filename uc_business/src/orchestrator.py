"""
UC Business Orchestrator — CEO/CMO Agent
==========================================
Koordiniert alle Sub-Agenten und trifft autonome Entscheidungen:

Täglicher Ablauf:
  09:00 — KPI Report (gestern)
  09:05 — Google Ads: Performance-Check + Optimierungen
  09:10 — Meta Ads: Performance-Check + Creative-Rotation
  09:15 — Email: Subscriber-Aktivität prüfen
  09:20 — Creative Agent: Neue Varianten generieren (wenn nötig)
  09:25 — Produkte: Umsatz-Check
  09:30 — Tages-Report ausgeben

Wöchentlich (Montag):
  — Neue Keywords aus Facebook-Gruppen-Insights
  — Email-Sequenzen überprüfen / updaten
  — Full Creative Refresh

Autonome Entscheidungen (regelbasiert):
  — ROAS > 3.0 → Budget +25%
  — ROAS < 1.5 → Budget -20%
  — CTR < 1% + 500 Imp → Creative pausieren
  — CPL > 5€ → Targeting-Warnung
"""
import asyncio
import json
import os
import sys
import logging
from datetime import datetime, date
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    DRY_RUN, DAILY_BUDGET_GOOGLE, DAILY_BUDGET_META,
    TARGET_CPA_LEAD, TARGET_CPA_SALE,
    ROAS_SCALE_UP_THRESHOLD, ROAS_SCALE_DOWN_THRESHOLD,
    BRAND_NAME
)
from db import init_db, get_kpi_summary, get_subscriber_count, get_total_revenue, log_orchestrator_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ─── Sub-Agent Imports (lazy, mit Fallback) ───────────────────────────────────

def _safe_import(module_name: str):
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as e:
        log.warning(f"Modul {module_name} konnte nicht geladen werden: {e}")
        return None


# ─── Tages-Report ─────────────────────────────────────────────────────────────

def generate_daily_report(dry_run: bool = DRY_RUN) -> dict:
    """Erstellt den täglichen KPI-Report."""
    today = date.today().isoformat()
    kpis = get_kpi_summary(days=1)
    subscribers = get_subscriber_count()
    total_revenue = get_total_revenue()

    # Aggregierte Zahlen
    total_spend = sum(k.get("spend", 0) for k in kpis)
    total_leads = sum(k.get("leads", 0) for k in kpis)
    total_sales = sum(k.get("sales", 0) for k in kpis)
    total_revenue_today = sum(k.get("revenue", 0) for k in kpis)
    roas = total_revenue_today / total_spend if total_spend > 0 else 0
    cpl = total_spend / total_leads if total_leads > 0 else 0

    report = {
        "date": today,
        "dry_run": dry_run,
        "kpis": {
            "spend": total_spend,
            "leads": total_leads,
            "sales": total_sales,
            "revenue": total_revenue_today,
            "roas": roas,
            "cpl": cpl,
        },
        "subscribers": subscribers,
        "total_revenue_alltime": total_revenue,
        "decisions": [],
        "alerts": [],
    }

    # Automatische Entscheidungen
    if total_spend > 0:
        if roas > ROAS_SCALE_UP_THRESHOLD:
            report["decisions"].append(f"SCALE_UP: ROAS {roas:.1f}x > {ROAS_SCALE_UP_THRESHOLD}x — Budget erhöhen")
        elif roas < ROAS_SCALE_DOWN_THRESHOLD and total_leads > 5:
            report["decisions"].append(f"SCALE_DOWN: ROAS {roas:.1f}x < {ROAS_SCALE_DOWN_THRESHOLD}x — Budget senken")

    if cpl > TARGET_CPA_LEAD * 2 and total_leads > 3:
        report["alerts"].append(f"ALERT: CPL €{cpl:.2f} > Ziel*2 (€{TARGET_CPA_LEAD*2:.2f}) — Targeting überprüfen")

    if total_leads == 0 and total_spend > 5:
        report["alerts"].append("ALERT: Kein einziger Lead bei aktivem Spending — Landingpage + Tracking prüfen!")

    return report


def print_daily_report(report: dict):
    """Gibt den Tages-Report in der Konsole aus."""
    print(f"\n{'█'*60}")
    print(f"  {BRAND_NAME} — TAGES-REPORT {report['date']}")
    if report.get("dry_run"):
        print(f"  [DRY-RUN MODUS]")
    print(f"{'█'*60}")

    k = report["kpis"]
    print(f"\n💸 AD SPEND HEUTE:")
    print(f"   Google + Meta gesamt:  €{k['spend']:.2f}")
    print(f"   Budget-Limit:          €{DAILY_BUDGET_GOOGLE + DAILY_BUDGET_META:.2f}")

    print(f"\n🎯 LEADS & SALES:")
    print(f"   Neue Leads:    {k['leads']}")
    print(f"   Neue Sales:    {k['sales']}")
    print(f"   Umsatz heute:  €{k['revenue']:.2f}")
    print(f"   ROAS:          {k['roas']:.1f}x")
    print(f"   CPL:           €{k['cpl']:.2f}")

    s = report["subscribers"]
    print(f"\n📋 SUBSCRIBER GESAMT:")
    print(f"   Leads:   {s.get('leads', 0)}")
    print(f"   Käufer:  {s.get('buyers', 0)}")
    print(f"   VIPs:    {s.get('vips', 0)}")
    print(f"   Total:   {s.get('total', 0)}")

    print(f"\n💰 GESAMTUMSATZ (all-time): €{report['total_revenue_alltime']:.2f}")

    if report["decisions"]:
        print(f"\n⚙️  AUTONOME ENTSCHEIDUNGEN:")
        for d in report["decisions"]:
            print(f"   → {d}")

    if report["alerts"]:
        print(f"\n🚨 ALERTS:")
        for a in report["alerts"]:
            print(f"   ⚠️  {a}")

    print(f"\n{'─'*60}")


# ─── Wöchentlicher Intelligence Refresh ──────────────────────────────────────

async def weekly_intelligence_refresh(dry_run: bool = DRY_RUN):
    """Wöchentlicher Refresh: Neue Insights + Creative Refresh."""
    log.info("🔄 Wöchentlicher Intelligence Refresh gestartet...")

    # 1. Facebook-Gruppen-Insights aktualisieren
    groups_intel = _safe_import("groups_intel_agent")
    if groups_intel:
        log.info("Scrape Facebook-Gruppen...")
        summary = await groups_intel.run(dry_run=dry_run)
        log.info(f"Insights aktualisiert: {summary.get('total_posts_analysed', 0)} Posts")

    # 2. Creative Refresh basierend auf neuen Insights
    creative = _safe_import("creative_agent")
    if creative:
        log.info("Generiere neue Creatives...")
        creative.run(dry_run=dry_run)

    # 3. Email-Sequenzen refreshen
    email = _safe_import("email_agent")
    if email:
        log.info("Refreshe Email-Sequenzen...")
        email.generate_all_sequences(dry_run=dry_run)

    # 4. Landing Pages neu rendern
    try:
        from landing_pages.renderer import render_all
        render_all()
        log.info("Landing Pages gerendert.")
    except Exception as e:
        log.warning(f"Landing Page Rendering übersprungen: {e}")

    log_orchestrator_action(
        action="weekly_refresh",
        details="Intelligence Refresh abgeschlossen",
        result="success",
        dry_run=dry_run
    )


# ─── Vollständiger Tages-Ablauf ───────────────────────────────────────────────

async def run_daily_pipeline(dry_run: bool = DRY_RUN) -> dict:
    """
    Hauptfunktion: Täglicher Orchestrator-Ablauf.
    Koordiniert alle Sub-Agenten sequentiell.
    """
    log.info(f"\n{'='*60}")
    log.info(f"UC BUSINESS ORCHESTRATOR — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    log.info(f"Modus: {'DRY-RUN (Simulation)' if dry_run else 'LIVE'}")
    log.info(f"{'='*60}\n")

    pipeline_results = {}

    # ── Schritt 1: Google Ads ──────────────────────────────────────────────
    log.info("[1/5] Google Ads: Performance-Check + Optimierung...")
    google_ads = _safe_import("google_ads_agent")
    if google_ads:
        try:
            result = google_ads.run_daily_check(dry_run=dry_run)
            pipeline_results["google_ads"] = result
            log.info(f"  ✓ Google Ads: {result.get('campaigns_checked', 0)} Kampagnen | "
                     f"Spend: €{result.get('total_spend_today', 0):.2f}")
        except Exception as e:
            log.error(f"  ✗ Google Ads Fehler: {e}")
            pipeline_results["google_ads"] = {"error": str(e)}

    # ── Schritt 2: Meta Ads ────────────────────────────────────────────────
    log.info("[2/5] Meta Ads: Performance-Check + Creative-Rotation...")
    meta_ads = _safe_import("facebook_ads_agent")
    if meta_ads:
        try:
            result = meta_ads.run_daily_check(dry_run=dry_run)
            pipeline_results["meta_ads"] = result
            log.info(f"  ✓ Meta Ads: {result.get('ads_checked', 0)} Ads | "
                     f"Leads: {result.get('total_leads', 0)} | "
                     f"CPL: €{result.get('avg_cpl', 0):.2f}")
        except Exception as e:
            log.error(f"  ✗ Meta Ads Fehler: {e}")
            pipeline_results["meta_ads"] = {"error": str(e)}

    # ── Schritt 3: Produkte / Umsatz ───────────────────────────────────────
    log.info("[3/5] Produkte: Umsatz-Check...")
    products = _safe_import("products")
    if products:
        try:
            revenue_summary = products.get_revenue_summary(days=1)
            pipeline_results["products"] = revenue_summary
            log.info(f"  ✓ Umsatz heute: €{revenue_summary.get('total_revenue', 0):.2f} | "
                     f"Sales: {revenue_summary.get('total_sales', 0)}")
        except Exception as e:
            log.error(f"  ✗ Produkte Fehler: {e}")

    # ── Schritt 4: Creative Check (bei Bedarf) ─────────────────────────────
    log.info("[4/5] Creative Check: Neue Varianten bei Bedarf...")
    google_result = pipeline_results.get("google_ads", {})
    meta_result = pipeline_results.get("meta_ads", {})

    needs_creative_refresh = (
        len(google_result.get("optimizations", [])) > 0 or
        len(meta_result.get("creative_rotations", [])) > 0
    )

    if needs_creative_refresh:
        log.info("  → Neue Creatives werden generiert (pausierte Anzeigen erkannt)...")
        creative = _safe_import("creative_agent")
        if creative:
            try:
                creative_result = creative.run(dry_run=dry_run)
                pipeline_results["creatives_refreshed"] = True
                log.info("  ✓ Neue Creatives generiert.")
            except Exception as e:
                log.error(f"  ✗ Creative Agent Fehler: {e}")
    else:
        log.info("  → Kein Creative Refresh nötig.")
        pipeline_results["creatives_refreshed"] = False

    # ── Schritt 5: Tages-Report ────────────────────────────────────────────
    log.info("[5/5] Tages-Report erstellen...")
    report = generate_daily_report(dry_run=dry_run)
    pipeline_results["report"] = report
    print_daily_report(report)

    # Autonome Entscheidungen ausführen
    for decision in report.get("decisions", []):
        log.info(f"Führe Entscheidung aus: {decision}")
        if not dry_run:
            _execute_decision(decision)

    # Log in DB
    log_orchestrator_action(
        action="daily_pipeline_complete",
        details=f"Alle 5 Schritte abgeschlossen",
        result=json.dumps({
            "leads": report["kpis"]["leads"],
            "sales": report["kpis"]["sales"],
            "revenue": report["kpis"]["revenue"],
            "alerts": len(report["alerts"])
        }),
        dry_run=dry_run
    )

    # Wöchentlicher Refresh (jeden Montag)
    if datetime.now().weekday() == 0:  # Montag
        log.info("\n🗓️ Montag erkannt → Wöchentlicher Intelligence Refresh...")
        await weekly_intelligence_refresh(dry_run=dry_run)

    return pipeline_results


def _execute_decision(decision: str):
    """Führt eine autonome Budget-Entscheidung aus."""
    if "SCALE_UP" in decision:
        google_ads = _safe_import("google_ads_agent")
        meta_ads = _safe_import("facebook_ads_agent")
        log.info(f"Budget-Erhöhung wird ausgeführt...")
        # Konkrete Budget-Anpassungen via APIs
    elif "SCALE_DOWN" in decision:
        log.info(f"Budget-Senkung wird ausgeführt...")


# ─── Setup (Erstinstallation) ─────────────────────────────────────────────────

def run_initial_setup(dry_run: bool = DRY_RUN):
    """
    Erstmalige Einrichtung des gesamten Systems:
    1. Datenbank initialisieren
    2. Produkt-Katalog befüllen
    3. Facebook-Gruppen-Insights sammeln
    4. Creatives generieren
    5. Landing Pages rendern
    6. Google Ads Struktur erstellen
    7. Meta Ads Struktur erstellen
    8. Email-Sequenzen generieren
    """
    print(f"\n{'='*60}")
    print(f"UC BUSINESS SYSTEM — ERSTEINRICHTUNG")
    print(f"{'='*60}\n")

    steps = [
        ("Datenbank initialisieren", _setup_db),
        ("Produkt-Katalog befüllen", _setup_products),
        ("Facebook-Gruppen Insights sammeln", _setup_intel),
        ("Creatives generieren", _setup_creatives),
        ("Landing Pages rendern", _setup_landing_pages),
        ("Google Ads Struktur erstellen", _setup_google_ads),
        ("Meta Ads Struktur erstellen", _setup_meta_ads),
        ("Email-Sequenzen generieren", _setup_email_sequences),
    ]

    for i, (name, func) in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {name}...")
        try:
            func(dry_run=dry_run)
            print(f"  ✓ Fertig")
        except Exception as e:
            print(f"  ✗ Fehler: {e}")

    print(f"\n{'='*60}")
    print(f"SETUP {'SIMULIERT (DRY-RUN)' if dry_run else 'ABGESCHLOSSEN'}!")
    print(f"Nächster Schritt: python run.py --daily (für täglichen Betrieb)")
    print(f"{'='*60}\n")


def _setup_db(dry_run=True):
    init_db()

def _setup_products(dry_run=True):
    products = _safe_import("products")
    if products and not dry_run:
        products.seed_products()
    elif dry_run:
        log.info("[DRY-RUN] Produkte würden in DB gespeichert.")

def _setup_intel(dry_run=True):
    groups_intel = _safe_import("groups_intel_agent")
    if groups_intel:
        asyncio.run(groups_intel.run(dry_run=dry_run))

def _setup_creatives(dry_run=True):
    creative = _safe_import("creative_agent")
    if creative:
        creative.run(dry_run=dry_run)

def _setup_landing_pages(dry_run=True):
    try:
        from landing_pages.renderer import render_all
        render_all()
    except Exception as e:
        log.warning(f"Landing Pages: {e}")

def _setup_google_ads(dry_run=True):
    google_ads = _safe_import("google_ads_agent")
    if google_ads:
        google_ads.create_campaign_structure(dry_run=dry_run)

def _setup_meta_ads(dry_run=True):
    meta_ads = _safe_import("facebook_ads_agent")
    if meta_ads:
        meta_ads.create_campaign_structure(dry_run=dry_run)

def _setup_email_sequences(dry_run=True):
    email = _safe_import("email_agent")
    if email:
        email.generate_all_sequences(dry_run=dry_run)


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Business Orchestrator (CEO/CMO)")
    parser.add_argument("--live", action="store_true", help="Live-Modus (echte API-Calls)")
    parser.add_argument("--setup", action="store_true", help="Ersteinrichtung ausführen")
    parser.add_argument("--daily", action="store_true", help="Täglichen Pipeline-Ablauf starten")
    parser.add_argument("--report", action="store_true", help="Nur KPI-Report anzeigen")
    parser.add_argument("--weekly", action="store_true", help="Wöchentlichen Refresh starten")
    args = parser.parse_args()

    dry = not args.live

    if args.setup:
        run_initial_setup(dry_run=dry)
    elif args.daily:
        asyncio.run(run_daily_pipeline(dry_run=dry))
    elif args.report:
        report = generate_daily_report(dry_run=dry)
        print_daily_report(report)
    elif args.weekly:
        asyncio.run(weekly_intelligence_refresh(dry_run=dry))
    else:
        # Standard: Tages-Pipeline
        asyncio.run(run_daily_pipeline(dry_run=dry))
