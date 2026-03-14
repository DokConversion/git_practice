"""
Facebook Ad Library Scraper fuer Live-Webinar-Anzeigen im DACH-Raum.

Nutzt die oeffentliche Facebook Ad Library (facebook.com/ads/library),
die Keyword-Suche unterstuetzt. Scraping erfolgt via Playwright (headless Browser),
da die Seite JavaScript-basiert ist.

Verwendung:
    python src/find_webinar_ads.py
    python src/find_webinar_ads.py --keyword "Live Webinar" --country DE
"""

import argparse
import hashlib
import json
import re
import sys
import os
import time
from urllib.parse import urlencode, quote_plus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import init_db, insert_ad


def build_ad_library_url(keyword: str, country: str = "DE") -> str:
    """
    Baut die URL fuer die Facebook Ad Library Suche.
    Die Ad Library unterstuetzt Keyword-Suche ueber den 'q' Parameter.
    """
    params = {
        "active_status": "active",
        "ad_type": "all",
        "country": country,
        "q": keyword,
        "media_type": "all",
    }
    return f"https://www.facebook.com/ads/library/?{urlencode(params)}"


def generate_ad_id(advertiser_name: str, landing_page_url: str) -> str:
    """Generiert eine eindeutige ID fuer eine Anzeige."""
    raw = f"{advertiser_name}:{landing_page_url}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def scrape_ad_library(keyword: str, country: str = "DE", max_ads: int = 50) -> list[dict]:
    """
    Scraped die Facebook Ad Library nach Anzeigen mit dem gegebenen Keyword.
    Gibt eine Liste von Anzeigen-Dicts zurueck.
    """
    from playwright.async_api import async_playwright

    url = build_ad_library_url(keyword, country)
    ads = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="de-DE",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"  Lade Ad Library: {keyword} ({country})...")
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Warte auf Anzeigen-Container
        await page.wait_for_timeout(3000)

        # Scrolle um mehr Ergebnisse zu laden
        scroll_count = 0
        max_scrolls = 5
        while scroll_count < max_scrolls:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            scroll_count += 1

        # Extrahiere Anzeigen-Daten aus dem DOM
        # Facebook Ad Library rendert Anzeigen in div-Containern
        ad_elements = await page.query_selector_all('[class*="xrvj5dj"]')

        if not ad_elements:
            # Fallback: Versuche alternative Selektoren
            ad_elements = await page.query_selector_all('[data-testid="ad_library_card"]')

        if not ad_elements:
            # Zweiter Fallback: Suche nach allgemeineren Containern
            ad_elements = await page.query_selector_all("._7jvw")

        print(f"  Gefunden: {len(ad_elements)} Anzeigen-Elemente")

        for element in ad_elements[:max_ads]:
            try:
                # Extrahiere Text-Inhalt
                text_content = await element.inner_text()

                # Extrahiere Links
                links = await element.query_selector_all("a[href]")
                landing_page_url = ""
                advertiser_name = ""

                for link in links:
                    href = await link.get_attribute("href")
                    link_text = await link.inner_text()

                    if href and "facebook.com" not in href and href.startswith("http"):
                        landing_page_url = href
                    elif href and "/ads/library/" not in href and link_text.strip():
                        if not advertiser_name:
                            advertiser_name = link_text.strip()

                if not advertiser_name:
                    # Versuche den ersten Text-Block als Advertiser-Name
                    lines = [l.strip() for l in text_content.split("\n") if l.strip()]
                    if lines:
                        advertiser_name = lines[0]

                if not landing_page_url:
                    # Suche nach URLs im Text
                    url_match = re.search(r'https?://[^\s<>"]+', text_content)
                    if url_match:
                        landing_page_url = url_match.group(0)

                if advertiser_name:
                    ad = {
                        "advertiser_name": advertiser_name,
                        "ad_text": text_content[:2000],
                        "landing_page_url": landing_page_url,
                        "keyword": keyword,
                        "country": country,
                    }
                    ads.append(ad)

            except Exception as e:
                print(f"  Fehler beim Parsen eines Anzeigen-Elements: {e}")
                continue

        await browser.close()

    return ads


async def search_all_keywords(countries: list[str] = None, keywords: list[str] = None,
                               max_ads_per_search: int = 50) -> list[dict]:
    """
    Durchsucht die Ad Library fuer alle konfigurierten Keywords und Laender.
    """
    if countries is None:
        countries = config.COUNTRIES
    if keywords is None:
        keywords = config.SEARCH_KEYWORDS

    all_ads = []

    for country in countries:
        for keyword in keywords:
            print(f"\nSuche: '{keyword}' in {country}")
            try:
                ads = await scrape_ad_library(keyword, country, max_ads_per_search)
                all_ads.extend(ads)
                print(f"  -> {len(ads)} Anzeigen gefunden")
            except Exception as e:
                print(f"  -> Fehler: {e}")

            # Pause zwischen Anfragen um Rate-Limiting zu vermeiden
            time.sleep(2)

    return all_ads


def save_ads_to_db(ads: list[dict]) -> int:
    """Speichert gefundene Anzeigen in der Datenbank. Gibt Anzahl neuer Eintraege zurueck."""
    new_count = 0
    for ad in ads:
        ad_id = generate_ad_id(ad["advertiser_name"], ad.get("landing_page_url", ""))
        is_new = insert_ad(
            ad_id=ad_id,
            advertiser_name=ad["advertiser_name"],
            ad_text=ad.get("ad_text", ""),
            landing_page_url=ad.get("landing_page_url", ""),
            search_keyword=ad.get("keyword", ""),
            country=ad.get("country", "DE"),
        )
        if is_new:
            new_count += 1
    return new_count


def filter_webinar_ads(ads: list[dict]) -> list[dict]:
    """
    Filtert Anzeigen, die tatsaechlich Live-Webinare bewerben
    (nicht Evergreen/Aufzeichnungen).
    """
    live_indicators = [
        r"live",
        r"am \d{1,2}\.\s?\d{1,2}\.",
        r"\d{1,2}\.\s?(januar|februar|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)",
        r"(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)",
        r"um \d{1,2}:\d{2}",
        r"uhr",
        r"platze? (begrenzt|limitiert|sichern)",
        r"jetzt anmelden",
        r"sichere? dir",
    ]

    evergreen_indicators = [
        r"jetzt sofort",
        r"sofort ansehen",
        r"aufzeichnung",
        r"replay",
        r"on.demand",
    ]

    filtered = []
    for ad in ads:
        text = ad.get("ad_text", "").lower()

        is_live = any(re.search(p, text) for p in live_indicators)
        is_evergreen = any(re.search(p, text) for p in evergreen_indicators)

        if is_live and not is_evergreen:
            filtered.append(ad)
        elif not is_evergreen:
            # Im Zweifel: mit aufnehmen, wird spaeter beim Date-Parsing gefiltert
            filtered.append(ad)

    return filtered


async def main():
    parser = argparse.ArgumentParser(description="Facebook Ad Library Webinar-Scraper")
    parser.add_argument("--keyword", type=str, help="Einzelnes Keyword zum Suchen")
    parser.add_argument("--country", type=str, default="DE", help="Laendercode (DE, AT, CH)")
    parser.add_argument("--max-ads", type=int, default=50, help="Max Anzeigen pro Suche")
    parser.add_argument("--all", action="store_true", help="Alle Keywords und Laender durchsuchen")
    args = parser.parse_args()

    init_db()

    if args.all:
        ads = await search_all_keywords(max_ads_per_search=args.max_ads)
    elif args.keyword:
        ads = await scrape_ad_library(args.keyword, args.country, args.max_ads)
    else:
        # Standard: Alle Keywords, nur Deutschland
        ads = await search_all_keywords(countries=["DE"], max_ads_per_search=args.max_ads)

    print(f"\n--- Ergebnis ---")
    print(f"Gesamt gefunden: {len(ads)} Anzeigen")

    # Filtere auf Live-Webinare
    live_ads = filter_webinar_ads(ads)
    print(f"Davon Live-Webinare: {len(live_ads)}")

    # Speichere in DB
    new_count = save_ads_to_db(live_ads)
    print(f"Neue Eintraege in DB: {new_count}")

    # Zeige Zusammenfassung
    for ad in live_ads[:10]:
        print(f"\n  Anbieter: {ad['advertiser_name']}")
        print(f"  URL: {ad.get('landing_page_url', 'N/A')}")
        preview = ad.get("ad_text", "")[:150].replace("\n", " ")
        print(f"  Text: {preview}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
