"""
Tages-Pipeline: Orchestriert den gesamten Outreach-Workflow.

Fuehrt alle Schritte nacheinander aus:
1. Neue Webinar-Anzeigen in der Facebook Ad Library suchen
2. Landing Pages besuchen und Webinar-Daten extrahieren
3. Kontaktdaten (Instagram, E-Mail) finden
4. Fuer gestrige Webinare: Personalisierte Nachrichten generieren
5. Ausstehende Nachrichten anzeigen (zum manuellen Versenden)

Verwendung:
    python src/daily_pipeline.py              # Kompletter Durchlauf
    python src/daily_pipeline.py --skip-scrape # Nur Nachrichten generieren
    python src/daily_pipeline.py --show-pending # Nur ausstehende anzeigen

Taeglich per Cron ausfuehren:
    0 7 * * * cd /path/to/project && python src/daily_pipeline.py >> logs/daily.log 2>&1
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import init_db, get_connection


def print_banner(step: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{now}] {step}")
    print(f"{'='*60}")


def show_db_stats():
    """Zeigt eine Zusammenfassung der Datenbank."""
    conn = get_connection()
    try:
        ads = conn.execute("SELECT COUNT(*) FROM ads").fetchone()[0]
        webinars = conn.execute("SELECT COUNT(*) FROM webinars").fetchone()[0]
        upcoming = conn.execute(
            "SELECT COUNT(*) FROM webinars WHERE date(webinar_date) >= date('now')"
        ).fetchone()[0]
        yesterday = conn.execute(
            "SELECT COUNT(*) FROM webinars WHERE date(webinar_date) = date('now', '-1 day')"
        ).fetchone()[0]
        contacts = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        contacts_ig = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE instagram_handle != ''"
        ).fetchone()[0]
        outreach_total = conn.execute("SELECT COUNT(*) FROM outreach").fetchone()[0]
        outreach_pending = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE status = 'generated'"
        ).fetchone()[0]
        outreach_sent = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE status = 'sent'"
        ).fetchone()[0]
    finally:
        conn.close()

    print(f"\n--- Datenbank-Statistik ---")
    print(f"Anzeigen:             {ads}")
    print(f"Webinare (gesamt):    {webinars}")
    print(f"  davon zukuenftig:   {upcoming}")
    print(f"  davon gestern:      {yesterday}")
    print(f"Kontakte:             {contacts}")
    print(f"  mit Instagram:      {contacts_ig}")
    print(f"Outreach (gesamt):    {outreach_total}")
    print(f"  ausstehend:         {outreach_pending}")
    print(f"  gesendet:           {outreach_sent}")


async def run_full_pipeline(skip_scrape: bool = False):
    """Fuehrt die gesamte Pipeline aus."""

    init_db()

    if not skip_scrape:
        # Schritt 1: Anzeigen suchen
        print_banner("SCHRITT 1: Webinar-Anzeigen suchen")
        from src.find_webinar_ads import search_all_keywords, save_ads_to_db, filter_webinar_ads

        ads = await search_all_keywords(countries=["DE"], max_ads_per_search=30)
        live_ads = filter_webinar_ads(ads)
        new_count = save_ads_to_db(live_ads)
        print(f"\nGefunden: {len(ads)} Anzeigen, {len(live_ads)} Live-Webinare, {new_count} neu")

        # Schritt 2: Webinar-Daten extrahieren
        print_banner("SCHRITT 2: Webinar-Daten von Landing Pages extrahieren")
        from src.extract_webinar_dates import process_unscanned_ads
        await process_unscanned_ads()

        # Schritt 3: Kontaktdaten finden
        print_banner("SCHRITT 3: Kontaktdaten suchen")
        from src.find_contact_info import process_ads_without_contacts
        await process_ads_without_contacts()

    if config.DRY_RUN:
        # Dry-Run: Zeige Review-Report statt Nachrichten zu generieren
        print_banner("SCHRITT 4: Review-Report (DRY RUN)")
        from src.review_report import get_review_candidates, generate_preview_message, print_report
        candidates = get_review_candidates()
        display = candidates[:config.DAILY_OUTREACH_LIMIT + 5]
        messages = {}
        for c in display:
            messages[c["id"]] = await generate_preview_message(c)
        print_report(display, messages)
        print("\nDRY RUN aktiv — keine Nachrichten gespeichert.")
        print("Freigeben mit: python src/review_report.py --approve 1 2 3")
    else:
        # Live-Modus: Nachrichten generieren (mit Tageslimit)
        print_banner("SCHRITT 4: Outreach-Nachrichten generieren")
        from src.generate_outreach import generate_messages_for_yesterdays_webinars
        from src.review_report import get_todays_outreach_count
        already = get_todays_outreach_count()
        remaining = max(0, config.DAILY_OUTREACH_LIMIT - already)
        if remaining == 0:
            print(f"Tageslimit ({config.DAILY_OUTREACH_LIMIT}) bereits erreicht. Keine neuen Nachrichten.")
        else:
            print(f"Tageslimit: {config.DAILY_OUTREACH_LIMIT} | Heute bereits: {already} | Verbleibend: {remaining}")
            await generate_messages_for_yesterdays_webinars(limit=remaining)

        # Ausstehende Nachrichten anzeigen
        print_banner("SCHRITT 5: Ausstehende Nachrichten")
        from src.generate_outreach import show_pending_messages
        show_pending_messages()

    # Statistik
    show_db_stats()


async def main():
    parser = argparse.ArgumentParser(description="Tages-Pipeline fuer Webinar-Outreach")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Ueberspringe Scraping, nur Nachrichten generieren")
    parser.add_argument("--show-pending", action="store_true",
                        help="Zeige nur ausstehende Nachrichten")
    parser.add_argument("--stats", action="store_true",
                        help="Zeige nur DB-Statistiken")
    parser.add_argument("--mark-sent", type=int, metavar="ID",
                        help="Markiere eine Nachricht als gesendet")
    args = parser.parse_args()

    init_db()

    if args.show_pending:
        from src.generate_outreach import show_pending_messages
        show_pending_messages()
    elif args.stats:
        show_db_stats()
    elif args.mark_sent:
        from src.db import mark_sent
        mark_sent(args.mark_sent)
        print(f"Nachricht #{args.mark_sent} als gesendet markiert.")
    else:
        await run_full_pipeline(skip_scrape=args.skip_scrape)


if __name__ == "__main__":
    asyncio.run(main())
