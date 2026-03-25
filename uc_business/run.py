#!/usr/bin/env python3
"""
UC Business System — Haupteinstiegspunkt
==========================================
Vollautomatisiertes Marketing-System für Colitis Ulcerosa.

SCHNELLSTART:
  1. cp .env.example .env && nano .env     (API Keys eintragen)
  2. pip install -r requirements.txt
  3. python run.py --setup --dry-run       (System simulieren)
  4. python run.py --setup                 (Live einrichten)
  5. python run.py --daily                 (Täglichen Betrieb starten)

KOMMANDOS:
  --setup           Ersteinrichtung (Kampagnen, Produkte, Emails, Landing Pages)
  --daily           Täglicher Pipeline-Ablauf (Reporting + Optimierungen)
  --intel           Facebook-Gruppen Insights sammeln
  --creatives       Neue Ad-Creatives + Email-Texte generieren
  --pages           Landing Pages rendern
  --dashboard       KPI-Dashboard anzeigen
  --analyst         Data-Analyst: KPI-Analyse + Anomalien + AI-Empfehlungen
  --brand           Brand Agent: Identity generieren + Website-Audit
  --psychology      Psychology Expert: Limbic/Spiral/Schwartz-Analyse
  --report          Nur Tages-Report
  --weekly          Wöchentlicher Intelligence Refresh

FLAGS:
  --live            Live-Modus (echte API-Calls, sonst Dry-Run)
  --no-headless     Browser sichtbar (für Debugging)
"""
import asyncio
import argparse
import sys
import os

# Src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import DRY_RUN, BRAND_NAME
from db import init_db


def print_banner(dry_run: bool):
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   {BRAND_NAME:<54} ║
║   Vollautomatisiertes UC-Marketing-System                ║
║   Modus: {'DRY-RUN (Simulation — kein Live-Zugriff)':<48} ║
╚══════════════════════════════════════════════════════════╝
""" if dry_run else f"""
╔══════════════════════════════════════════════════════════╗
║   {BRAND_NAME:<54} ║
║   Vollautomatisiertes UC-Marketing-System                ║
║   Modus: LIVE — echte API-Calls aktiv                   ║
╚══════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(
        description="UC Business System — CEO/CMO Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Haupt-Kommandos
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--setup", action="store_true",
                       help="Ersteinrichtung des gesamten Systems")
    group.add_argument("--daily", action="store_true",
                       help="Täglicher Pipeline-Ablauf")
    group.add_argument("--intel", action="store_true",
                       help="Facebook-Gruppen Insights sammeln")
    group.add_argument("--creatives", action="store_true",
                       help="Neue Creatives generieren")
    group.add_argument("--pages", action="store_true",
                       help="Landing Pages rendern")
    group.add_argument("--dashboard", action="store_true",
                       help="KPI Dashboard anzeigen")
    group.add_argument("--report", action="store_true",
                       help="Tages-Report anzeigen")
    group.add_argument("--weekly", action="store_true",
                       help="Wöchentlicher Intelligence Refresh")
    group.add_argument("--email-preview", action="store_true",
                       help="Email-Sequenzen als Preview anzeigen")
    group.add_argument("--analyst", action="store_true",
                       help="Data Analyst: KPI-Analyse + Anomalien + AI-Empfehlungen")
    group.add_argument("--brand", action="store_true",
                       help="Brand Agent: Identity generieren + Website-Audit")
    group.add_argument("--psychology", action="store_true",
                       help="Psychology Expert: Limbic/Spiral/Schwartz-Analyse")

    # Flags
    parser.add_argument("--live", action="store_true",
                        help="Live-Modus (sonst Dry-Run)")
    parser.add_argument("--no-headless", action="store_true",
                        help="Browser sichtbar anzeigen")

    args = parser.parse_args()
    dry_run = not args.live

    print_banner(dry_run)
    init_db()

    # ── Kommandos ausführen ────────────────────────────────────────────────

    if args.setup:
        from orchestrator import run_initial_setup
        run_initial_setup(dry_run=dry_run)

    elif args.daily:
        from orchestrator import run_daily_pipeline
        asyncio.run(run_daily_pipeline(dry_run=dry_run))

    elif args.intel:
        from groups_intel_agent import run as intel_run
        asyncio.run(intel_run(
            dry_run=dry_run,
            headless=not args.no_headless
        ))

    elif args.creatives:
        from creative_agent import run as creative_run
        creative_run(dry_run=dry_run)

    elif args.pages:
        from landing_pages.renderer import render_all
        render_all()
        print("✓ Alle Landing Pages gerendert → uc_business/data/rendered_pages/")

    elif args.dashboard:
        from tracking import print_kpi_dashboard
        print_kpi_dashboard(days=7)

    elif args.report:
        from orchestrator import generate_daily_report, print_daily_report
        report = generate_daily_report(dry_run=dry_run)
        print_daily_report(report)

    elif args.weekly:
        from orchestrator import weekly_intelligence_refresh
        asyncio.run(weekly_intelligence_refresh(dry_run=dry_run))

    elif args.email_preview:
        from email_agent import get_sequence_preview
        get_sequence_preview()

    elif args.analyst:
        from data_analyst import run as analyst_run, print_analyst_report
        from config import DB_PATH
        report = analyst_run(db_path=DB_PATH, days=7, dry_run=dry_run)
        print_analyst_report(report)

    elif args.brand:
        from brand_agent import run as brand_run
        brand_run(audit_url="https://lebenmitcolitis.de/", dry_run=dry_run)

    elif args.psychology:
        from psychology_expert import run as psych_run
        psych_run(dry_run=dry_run)

    else:
        # Standard: Dashboard + kurzer Status
        print("Kein Kommando angegeben. Zeige KPI-Dashboard:\n")
        from tracking import print_kpi_dashboard
        print_kpi_dashboard(days=7)
        print("\nVerfügbare Kommandos:")
        print("  python run.py --setup --dry-run   → System-Setup simulieren")
        print("  python run.py --daily --dry-run   → Tages-Pipeline simulieren")
        print("  python run.py --intel             → Facebook-Gruppen-Insights")
        print("  python run.py --creatives         → Neue Werbetexte generieren")
        print("  python run.py --pages             → Landing Pages rendern")
        print("  python run.py --dashboard         → KPI-Dashboard")
        print("\n  Füge --live hinzu für echte API-Calls.")


if __name__ == "__main__":
    main()
