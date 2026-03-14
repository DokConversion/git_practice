"""
Extrahiert Webinar-Daten (Datum, Thema) von Landing Pages.

Besucht die Landing Pages der gefundenen Anzeigen und versucht,
Datum/Uhrzeit und Thema des Webinars zu extrahieren.

Verwendung:
    python src/extract_webinar_dates.py
"""

import re
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import get_connection, init_db, insert_webinar


# Deutsche Monatsnamen fuer Datum-Parsing
MONTHS_DE = {
    "januar": 1, "februar": 2, "maerz": 3, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
    "oktober": 10, "november": 11, "dezember": 12,
    "jan": 1, "feb": 2, "mär": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}


def parse_german_date(text: str) -> str | None:
    """
    Versucht ein deutsches Datum aus Text zu extrahieren.
    Gibt ISO-Format (YYYY-MM-DD) zurueck oder None.
    """
    text = text.lower()
    current_year = datetime.now().year

    # Pattern: "15. März 2025" oder "15. Maerz" oder "15.03.2025"
    patterns = [
        # "15. März 2025" / "15. März"
        r"(\d{1,2})\.\s*("
        + "|".join(MONTHS_DE.keys())
        + r")\.?\s*(\d{4})?",
        # "15.03.2025" oder "15.03."
        r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            day = int(groups[0])

            if groups[1] in MONTHS_DE:
                month = MONTHS_DE[groups[1]]
            else:
                try:
                    month = int(groups[1])
                except (ValueError, TypeError):
                    continue

            year = current_year
            if len(groups) > 2 and groups[2]:
                year = int(groups[2])
                if year < 100:
                    year += 2000

            try:
                date = datetime(year, month, day)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def extract_time(text: str) -> str | None:
    """Extrahiert eine Uhrzeit aus dem Text."""
    match = re.search(r"(\d{1,2})[:\.](\d{2})\s*(?:uhr|Uhr)?", text)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"

    match = re.search(r"(\d{1,2})\s*Uhr", text, re.IGNORECASE)
    if match:
        return f"{int(match.group(1)):02d}:00"

    return None


def extract_topic_from_text(text: str) -> str:
    """
    Extrahiert das Webinar-Thema aus dem Seitentext.
    Sucht nach typischen Headings/Patterns.
    """
    # Suche nach typischen Webinar-Titel-Patterns
    patterns = [
        r"(?:webinar|workshop|training|masterclass|seminar)\s*[:\-–]\s*[\"']?(.+?)[\"']?\s*(?:\n|$)",
        r"(?:lerne|erfahre|entdecke)\s+(.+?)(?:\n|$|\.|!)",
        r"(?:wie du|wie sie)\s+(.+?)(?:\n|$|\.|!)",
        r"<h1[^>]*>(.+?)</h1>",
        r"<title>(.+?)</title>",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            # Begrenze auf sinnvolle Laenge
            if 10 < len(topic) < 200:
                return topic

    # Fallback: Erste nicht-leere Zeile die lang genug ist
    for line in text.split("\n"):
        line = line.strip()
        if 20 < len(line) < 200 and not line.startswith(("http", "<", "{", "//", "/*")):
            return line

    return "Unbekanntes Thema"


async def scrape_landing_page(url: str) -> dict:
    """
    Besucht eine Landing Page und extrahiert Webinar-Informationen.
    """
    from playwright.async_api import async_playwright

    result = {
        "date": None,
        "time": None,
        "topic": "",
        "raw_text": "",
    }

    if not url or not url.startswith("http"):
        return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(2000)

            # Extrahiere gesamten sichtbaren Text
            text = await page.inner_text("body")
            result["raw_text"] = text[:5000]

            # Extrahiere Datum und Uhrzeit
            result["date"] = parse_german_date(text)
            result["time"] = extract_time(text)

            # Extrahiere Thema
            title = await page.title()
            result["topic"] = extract_topic_from_text(title + "\n" + text)

            # Versuche auch Meta-Tags
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                desc = await meta_desc.get_attribute("content")
                if desc and not result["date"]:
                    result["date"] = parse_german_date(desc)

        except Exception as e:
            print(f"  Fehler beim Laden von {url}: {e}")
        finally:
            await browser.close()

    return result


async def process_unscanned_ads():
    """
    Verarbeitet alle Anzeigen in der DB, die noch kein Webinar-Datum haben.
    """
    conn = get_connection()
    try:
        ads = conn.execute("""
            SELECT a.* FROM ads a
            LEFT JOIN webinars w ON a.id = w.ad_id
            WHERE w.id IS NULL
            AND a.landing_page_url != ''
        """).fetchall()
    finally:
        conn.close()

    print(f"Zu verarbeitende Anzeigen: {len(ads)}")

    for ad in ads:
        ad = dict(ad)
        print(f"\nVerarbeite: {ad['advertiser_name']}")
        print(f"  URL: {ad['landing_page_url']}")

        # Versuche zuerst Datum aus dem Anzeigentext
        date_from_ad = parse_german_date(ad.get("ad_text", ""))
        time_from_ad = extract_time(ad.get("ad_text", ""))

        # Scrape Landing Page fuer mehr Details
        lp_data = await scrape_landing_page(ad["landing_page_url"])

        # Kombiniere Ergebnisse (Landing Page hat Prioritaet)
        webinar_date = lp_data["date"] or date_from_ad
        webinar_topic = lp_data["topic"] or extract_topic_from_text(ad.get("ad_text", ""))

        if webinar_date:
            webinar_id = insert_webinar(
                ad_id=ad["id"],
                webinar_date=webinar_date,
                webinar_topic=webinar_topic,
                landing_page_content=lp_data.get("raw_text", "")[:3000],
            )
            time_str = lp_data["time"] or time_from_ad or "?"
            print(f"  -> Webinar am {webinar_date} um {time_str}: {webinar_topic[:80]}")
        else:
            print(f"  -> Kein Datum gefunden, uebersprungen")

        # Pause zwischen Requests
        import asyncio
        await asyncio.sleep(1)


async def main():
    init_db()
    await process_unscanned_ads()

    # Zusammenfassung
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM webinars").fetchone()[0]
        upcoming = conn.execute(
            "SELECT COUNT(*) FROM webinars WHERE date(webinar_date) >= date('now')"
        ).fetchone()[0]
    finally:
        conn.close()

    print(f"\n--- Zusammenfassung ---")
    print(f"Webinare in DB: {count}")
    print(f"Davon zukuenftig: {upcoming}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
