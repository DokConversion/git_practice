"""
Findet Kontaktdaten (Instagram, LinkedIn, E-Mail) fuer Webinar-Anbieter.

Strategie:
1. Website des Anbieters besuchen (Landing Page Domain)
2. Impressum finden und E-Mail extrahieren
3. Social-Media-Links (Instagram, LinkedIn) von der Website extrahieren
4. Falls kein Instagram gefunden: Fallback auf Advertiser-Name Suche

Verwendung:
    python src/find_contact_info.py
"""

import re
import sys
import os
from urllib.parse import urlparse, urljoin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import get_connection, init_db, insert_contact


def extract_domain(url: str) -> str:
    """Extrahiert die Domain aus einer URL."""
    if not url:
        return ""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""


def extract_emails(text: str) -> list[str]:
    """Extrahiert E-Mail-Adressen aus Text."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    emails = re.findall(pattern, text)
    # Filtere offensichtliche Nicht-Kontakt-Adressen
    filtered = []
    for email in emails:
        lower = email.lower()
        if not any(x in lower for x in ["example.com", "sentry.io", "wixpress",
                                         ".png", ".jpg", ".js", ".css"]):
            filtered.append(email)
    return list(set(filtered))


def extract_instagram(text: str, html: str = "") -> str | None:
    """Extrahiert Instagram-Handle aus Text oder HTML."""
    # Suche nach Instagram-Links
    patterns = [
        r"instagram\.com/([a-zA-Z0-9_.]+)",
        r"instagr\.am/([a-zA-Z0-9_.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html or text)
        if match:
            handle = match.group(1)
            if handle not in ("p", "reel", "stories", "explore", "accounts"):
                return handle
    return None


def extract_linkedin(text: str, html: str = "") -> str | None:
    """Extrahiert LinkedIn-URL aus Text oder HTML."""
    patterns = [
        r"(https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9\-_%]+/?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html or text)
        if match:
            return match.group(1)
    return None


async def scrape_contact_info(website_url: str) -> dict:
    """
    Besucht eine Website und extrahiert Kontaktdaten.
    Sucht auf der Hauptseite und im Impressum.
    """
    from playwright.async_api import async_playwright

    result = {
        "instagram_handle": "",
        "linkedin_url": "",
        "email": "",
        "name": "",
    }

    if not website_url:
        return result

    domain = extract_domain(website_url)
    if not domain:
        return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            # 1. Hauptseite laden
            await page.goto(domain, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1500)

            html = await page.content()
            text = await page.inner_text("body")

            # Social Media Links von der Hauptseite
            result["instagram_handle"] = extract_instagram(text, html) or ""
            result["linkedin_url"] = extract_linkedin(text, html) or ""

            # 2. Impressum suchen und laden
            impressum_urls = []

            # Suche nach Impressum-Links
            links = await page.query_selector_all("a")
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    link_text = await link.inner_text()
                    if href and any(x in (link_text + href).lower()
                                    for x in ["impressum", "imprint", "legal"]):
                        full_url = urljoin(domain, href)
                        impressum_urls.append(full_url)
                except Exception:
                    continue

            # Besuche Impressum
            for imp_url in impressum_urls[:2]:
                try:
                    await page.goto(imp_url, wait_until="networkidle", timeout=10000)
                    await page.wait_for_timeout(1000)

                    imp_html = await page.content()
                    imp_text = await page.inner_text("body")

                    # E-Mail aus Impressum
                    emails = extract_emails(imp_text)
                    if emails:
                        result["email"] = emails[0]

                    # Ergaenze Social Media falls noch nicht gefunden
                    if not result["instagram_handle"]:
                        result["instagram_handle"] = extract_instagram(imp_text, imp_html) or ""
                    if not result["linkedin_url"]:
                        result["linkedin_url"] = extract_linkedin(imp_text, imp_html) or ""

                    # Versuche Name zu extrahieren (Inhaber/Geschaeftsfuehrer)
                    name_patterns = [
                        r"(?:inhaber|geschäftsführer|geschaeftsfuehrer|vertreten durch|verantwortlich)[:\s]+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)",
                        r"(?:Angaben gemäß|Angaben gemaess).*?([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)",
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, imp_text, re.IGNORECASE)
                        if match:
                            result["name"] = match.group(1).strip()
                            break

                    break  # Impressum gefunden, nicht weiter suchen

                except Exception:
                    continue

        except Exception as e:
            print(f"  Fehler beim Laden von {domain}: {e}")
        finally:
            await browser.close()

    return result


async def process_ads_without_contacts():
    """
    Verarbeitet alle Anzeigen, die noch keine Kontaktdaten haben.
    """
    conn = get_connection()
    try:
        ads = conn.execute("""
            SELECT a.* FROM ads a
            LEFT JOIN contacts c ON a.id = c.ad_id
            WHERE c.id IS NULL
            AND a.landing_page_url != ''
        """).fetchall()
    finally:
        conn.close()

    print(f"Anzeigen ohne Kontaktdaten: {len(ads)}")

    for ad in ads:
        ad = dict(ad)
        print(f"\nSuche Kontakt fuer: {ad['advertiser_name']}")
        print(f"  Landing Page: {ad['landing_page_url']}")

        contact = await scrape_contact_info(ad["landing_page_url"])

        # Name: Fallback auf Advertiser-Name
        name = contact.get("name") or ad["advertiser_name"]

        contact_id = insert_contact(
            ad_id=ad["id"],
            name=name,
            instagram_handle=contact.get("instagram_handle", ""),
            linkedin_url=contact.get("linkedin_url", ""),
            email=contact.get("email", ""),
            website_url=extract_domain(ad["landing_page_url"]),
        )

        channels = []
        if contact.get("instagram_handle"):
            channels.append(f"IG: @{contact['instagram_handle']}")
        if contact.get("linkedin_url"):
            channels.append("LinkedIn")
        if contact.get("email"):
            channels.append(f"E-Mail: {contact['email']}")

        if channels:
            print(f"  -> {name}: {', '.join(channels)}")
        else:
            print(f"  -> {name}: Keine Kontaktdaten gefunden")

        # Pause
        import asyncio
        await asyncio.sleep(1)


async def main():
    init_db()
    await process_ads_without_contacts()

    # Zusammenfassung
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        with_ig = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE instagram_handle != ''"
        ).fetchone()[0]
        with_email = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE email != ''"
        ).fetchone()[0]
    finally:
        conn.close()

    print(f"\n--- Kontakte ---")
    print(f"Gesamt: {total}")
    print(f"Mit Instagram: {with_ig}")
    print(f"Mit E-Mail: {with_email}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
