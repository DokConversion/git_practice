"""
Review-Report: Zeigt gefundene Profile und geplante Nachrichten zur Freigabe.

Im Dry-Run-Modus (config.DRY_RUN = True) werden keine Nachrichten in der DB
gespeichert. Stattdessen wird ein detaillierter Report generiert, den Marc
reviewen kann. Erst nach Freigabe werden Nachrichten tatsaechlich erstellt.

Verwendung:
    python src/review_report.py                  # Report fuer gestrige Webinare
    python src/review_report.py --approve 1 3 5  # IDs freigeben
    python src/review_report.py --approve-all    # Alle freigeben
    python src/review_report.py --reject 2 4     # IDs ablehnen
    python src/review_report.py --export report.txt  # Report als Datei speichern
"""

import argparse
import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import (
    get_connection, init_db, get_yesterdays_webinars,
    get_contact_for_ad, insert_outreach,
)
from src.generate_outreach import (
    generate_message_with_llm, generate_specific_hook,
    guess_target_label, TEMPLATE_INSTAGRAM,
)


def get_todays_outreach_count() -> int:
    """Zaehlt wie viele Outreach-Nachrichten heute bereits generiert wurden."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE date(generated_at) = date('now')"
        ).fetchone()
        return row[0]
    finally:
        conn.close()


def get_review_candidates() -> list[dict]:
    """
    Sammelt alle Webinare von gestern mit Kontaktdaten und
    bereitet sie als Review-Kandidaten auf.
    """
    webinars = get_yesterdays_webinars()
    candidates = []

    for webinar in webinars:
        contact = get_contact_for_ad(webinar["ad_id"])
        if not contact:
            continue

        # Bestimme Kanal
        if contact.get("instagram_handle"):
            channel = "instagram"
            contact_info = f"@{contact['instagram_handle']}"
        elif contact.get("linkedin_url"):
            channel = "linkedin"
            contact_info = contact["linkedin_url"]
        elif contact.get("email"):
            channel = "email"
            contact_info = contact["email"]
        else:
            continue

        candidate = {
            "id": len(candidates) + 1,
            "name": contact.get("name") or webinar["advertiser_name"],
            "advertiser_name": webinar["advertiser_name"],
            "channel": channel,
            "contact_info": contact_info,
            "website": contact.get("website_url", ""),
            "webinar_topic": webinar["webinar_topic"],
            "webinar_date": webinar["webinar_date"],
            "landing_page_url": webinar.get("landing_page_url", ""),
            "ad_text_preview": webinar.get("ad_text", "")[:300],
            "landing_page_preview": webinar.get("landing_page_content", "")[:500],
            # DB-IDs fuer spaetere Freigabe
            "_contact_id": contact["id"],
            "_webinar_id": webinar["id"],
            "_ad_id": webinar["ad_id"],
        }
        candidates.append(candidate)

    return candidates


async def generate_preview_message(candidate: dict) -> str:
    """Generiert eine Vorschau-Nachricht fuer einen Kandidaten."""
    name = candidate["name"]
    topic = candidate["webinar_topic"]
    lp_content = candidate.get("landing_page_preview", "")
    ad_text = candidate.get("ad_text_preview", "")

    # Versuche LLM
    message = await generate_message_with_llm(name, topic, lp_content, ad_text)

    # Fallback Template
    if not message:
        target_label = guess_target_label(ad_text, topic)
        specific_hook = generate_specific_hook(topic, lp_content)
        message = TEMPLATE_INSTAGRAM.format(
            name=name,
            topic=topic,
            specific_hook=specific_hook,
            target_label=target_label,
        )

    return message


def print_report(candidates: list[dict], messages: dict[int, str]):
    """Gibt den Review-Report auf der Konsole aus."""
    today = datetime.now().strftime("%Y-%m-%d")
    already_sent = get_todays_outreach_count()
    remaining = max(0, config.DAILY_OUTREACH_LIMIT - already_sent)

    print(f"\n{'='*70}")
    print(f"  OUTREACH REVIEW-REPORT — {today}")
    print(f"  Modus: {'DRY RUN (keine Nachrichten gespeichert)' if config.DRY_RUN else 'LIVE'}")
    print(f"  Tageslimit: {config.DAILY_OUTREACH_LIMIT} | Heute bereits: {already_sent} | Verbleibend: {remaining}")
    print(f"  Kandidaten: {len(candidates)}")
    print(f"{'='*70}")

    if not candidates:
        print("\n  Keine Kandidaten fuer heute gefunden.")
        print("  (Keine Webinare von gestern ohne bestehenden Outreach)")
        return

    for candidate in candidates:
        cid = candidate["id"]
        print(f"\n{'─'*70}")
        print(f"  #{cid} | {candidate['name']}")
        print(f"{'─'*70}")
        print(f"  Anbieter:      {candidate['advertiser_name']}")
        print(f"  Website:       {candidate['website']}")
        print(f"  Kanal:         {candidate['channel'].upper()} → {candidate['contact_info']}")
        print(f"  Webinar-Thema: {candidate['webinar_topic'][:80]}")
        print(f"  Webinar-Datum: {candidate['webinar_date']}")
        print(f"  Landing Page:  {candidate['landing_page_url']}")

        # Anzeigen-Text Vorschau
        if candidate["ad_text_preview"]:
            preview = candidate["ad_text_preview"].replace("\n", " ")[:200]
            print(f"\n  Anzeigentext (Auszug):")
            print(f"    \"{preview}...\"")

        # Geplante Nachricht
        if cid in messages:
            print(f"\n  GEPLANTE NACHRICHT:")
            print(f"  {'·'*50}")
            for line in messages[cid].split("\n"):
                print(f"    {line}")
            print(f"  {'·'*50}")

        # Status-Hinweis
        if cid <= remaining:
            print(f"\n  Status: INNERHALB Tageslimit — bereit zur Freigabe")
        else:
            print(f"\n  Status: UEBER Tageslimit — wird auf morgen verschoben")

    print(f"\n{'='*70}")
    print(f"  NAECHSTE SCHRITTE:")
    print(f"  • Freigeben:  python src/review_report.py --approve 1 2 3")
    print(f"  • Alle:       python src/review_report.py --approve-all")
    print(f"  • Ablehnen:   python src/review_report.py --reject 2")
    print(f"  • Exportieren: python src/review_report.py --export report.txt")
    print(f"{'='*70}\n")


def save_report_to_file(candidates: list[dict], messages: dict[int, str], filepath: str):
    """Speichert den Report als Textdatei."""
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    print_report(candidates, messages)
    sys.stdout = old_stdout

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())

    print(f"Report gespeichert: {filepath}")


async def approve_candidates(candidate_ids: list[int], candidates: list[dict],
                               messages: dict[int, str]):
    """Gibt ausgewaehlte Kandidaten frei und erstellt Outreach-Eintraege."""
    already_sent = get_todays_outreach_count()
    remaining = max(0, config.DAILY_OUTREACH_LIMIT - already_sent)

    approved = 0
    for cid in candidate_ids:
        if approved >= remaining:
            print(f"  Tageslimit ({config.DAILY_OUTREACH_LIMIT}) erreicht. "
                  f"Restliche werden auf morgen verschoben.")
            break

        candidate = next((c for c in candidates if c["id"] == cid), None)
        if not candidate:
            print(f"  Kandidat #{cid} nicht gefunden — uebersprungen")
            continue

        if cid not in messages:
            print(f"  Keine Nachricht fuer #{cid} — uebersprungen")
            continue

        outreach_id = insert_outreach(
            contact_id=candidate["_contact_id"],
            webinar_id=candidate["_webinar_id"],
            channel=candidate["channel"],
            message_text=messages[cid],
        )
        approved += 1
        print(f"  #{cid} {candidate['name']} -> Outreach #{outreach_id} erstellt "
              f"({candidate['channel']}: {candidate['contact_info']})")

    print(f"\n{approved} Nachrichten freigegeben und in DB gespeichert.")
    print(f"Anzeigen mit: python src/daily_pipeline.py --show-pending")


async def main():
    parser = argparse.ArgumentParser(description="Review-Report fuer Outreach-Kandidaten")
    parser.add_argument("--approve", nargs="+", type=int, metavar="ID",
                        help="Kandidaten-IDs freigeben")
    parser.add_argument("--approve-all", action="store_true",
                        help="Alle Kandidaten freigeben (bis Tageslimit)")
    parser.add_argument("--reject", nargs="+", type=int, metavar="ID",
                        help="Kandidaten-IDs ablehnen (werden ignoriert)")
    parser.add_argument("--export", type=str, metavar="FILE",
                        help="Report als Textdatei speichern")
    args = parser.parse_args()

    init_db()

    # Sammle Kandidaten
    candidates = get_review_candidates()

    # Begrenze auf Tageslimit fuer den Report
    display_candidates = candidates[:config.DAILY_OUTREACH_LIMIT + 5]

    # Generiere Vorschau-Nachrichten
    messages = {}
    print("Generiere Vorschau-Nachrichten...")
    for candidate in display_candidates:
        msg = await generate_preview_message(candidate)
        messages[candidate["id"]] = msg

    if args.approve or args.approve_all:
        if config.DRY_RUN and not args.approve and not args.approve_all:
            print("HINWEIS: DRY_RUN ist aktiv. Nutze --approve oder --approve-all um freizugeben.")
            return

        ids_to_approve = args.approve if args.approve else [c["id"] for c in candidates]
        await approve_candidates(ids_to_approve, candidates, messages)

    elif args.reject:
        print(f"Abgelehnt: Kandidaten {args.reject}")
        print("(Diese werden beim naechsten Durchlauf nicht erneut angezeigt, "
              "da sie bereits ein Webinar-Datum in der Vergangenheit haben.)")

    elif args.export:
        save_report_to_file(display_candidates, messages, args.export)

    else:
        # Standard: Report anzeigen
        print_report(display_candidates, messages)


if __name__ == "__main__":
    asyncio.run(main())
