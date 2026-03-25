"""
Facebook-Gruppen Intelligence Agent
====================================
Sammelt echte Insights aus öffentlichen UC-Facebook-Gruppen:
- Pain Points der Betroffenen
- Echte Sprache / Formulierungen
- Emotionale Trigger
- Content-Ideen für Ads, Emails und Landing Pages

Nutzt Playwright (headless Browser) + Claude API für Analyse.
"""
import asyncio
import json
import re
import sys
import os
import logging
from datetime import datetime
from typing import Optional

import anthropic
from playwright.async_api import async_playwright, Page

sys.path.insert(0, os.path.dirname(__file__))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART, UC_FACEBOOK_GROUPS, DRY_RUN
from db import init_db, insert_group_insight, get_top_insights

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─── Playwright Scraping ──────────────────────────────────────────────────────

async def scrape_public_group_posts(page: Page, group_name: str, max_posts: int = 30) -> list[str]:
    """Lädt öffentliche Posts einer Facebook-Gruppe (ohne Login, wenn öffentlich)."""
    posts = []
    url = f"https://www.facebook.com/groups/{group_name}"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        # Seite prüfen — öffentlich oder Login nötig?
        content = await page.content()
        if "anmelden" in content.lower() or "log in" in content.lower():
            log.warning(f"Gruppe {group_name} erfordert Login — überspringe.")
            return posts

        # Posts scrollen und extrahieren
        for _ in range(5):
            # Post-Texte extrahieren
            elements = await page.query_selector_all("[data-ad-comet-preview='message'], [role='article'] div[dir='auto']")
            for el in elements:
                text = await el.inner_text()
                text = text.strip()
                if len(text) > 80:  # Nur relevante Posts (keine Kurzkommentare)
                    posts.append(text)

            if len(posts) >= max_posts:
                break

            # Weiter scrollen
            await page.keyboard.press("End")
            await asyncio.sleep(2)

    except Exception as e:
        log.error(f"Fehler beim Scrapen von {group_name}: {e}")

    # Deduplizierung
    seen = set()
    unique_posts = []
    for p in posts:
        key = p[:100]
        if key not in seen:
            seen.add(key)
            unique_posts.append(p)

    log.info(f"[{group_name}] {len(unique_posts)} einzigartige Posts gefunden.")
    return unique_posts[:max_posts]


async def scrape_all_groups(headless: bool = True) -> dict[str, list[str]]:
    """Scrapt alle konfigurierten UC-Facebook-Gruppen."""
    results = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--lang=de-DE"]
        )
        context = await browser.new_context(
            locale="de-DE",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for group in UC_FACEBOOK_GROUPS:
            posts = await scrape_public_group_posts(page, group)
            if posts:
                results[group] = posts
            await asyncio.sleep(2)

        await browser.close()

    return results


# ─── Claude API Analyse ───────────────────────────────────────────────────────

def analyse_post_with_claude(post_text: str, group_name: str) -> dict:
    """
    Analysiert einen Facebook-Post mit Claude und extrahiert:
    - Pain Points
    - Emotionen
    - Schlüsselwörter
    - Fertige Ad-Hook-Idee
    - Email-Betreffzeile
    """
    prompt = f"""Du bist Marketing-Experte für Gesundheitsprodukte im DACH-Markt.

Analysiere diesen Post aus einer Colitis Ulcerosa Selbsthilfe-Gruppe:

<post>
{post_text[:800]}
</post>

Extrahiere:
1. pain_points: Liste der konkreten Probleme/Leiden (max. 3, kurze Phrasen)
2. emotions: Emotionen im Post (Angst, Hoffnung, Frustration, Erschöpfung, etc.)
3. keywords: Wörter/Phrasen die Betroffene tatsächlich nutzen (KEINE medizinischen Fachbegriffe)
4. ad_hook: Eine kraftvolle Ad-Headline auf Basis dieses Posts (max. 30 Zeichen, direkt und empathisch)
5. email_subject: Eine Email-Betreffzeile die Neugier weckt (max. 50 Zeichen)

Wichtig:
- Keine falschen medizinischen Versprechen
- Authentische, empathische Sprache
- Aus Betroffenenperspektive formulieren
- Auf Deutsch

Antworte NUR mit validem JSON:
{{
    "pain_points": ["...", "..."],
    "emotions": ["...", "..."],
    "keywords": ["...", "..."],
    "ad_hook": "...",
    "email_subject": "..."
}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

        # JSON extrahieren
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        log.error(f"Claude Analyse-Fehler: {e}")

    return {
        "pain_points": [],
        "emotions": [],
        "keywords": [],
        "ad_hook": "",
        "email_subject": ""
    }


def generate_insights_summary(all_insights: list[dict]) -> dict:
    """Erstellt eine Zusammenfassung aller Insights für den Creative Agent."""
    if not all_insights:
        return {}

    # Top Pain Points aggregieren
    pain_counter = {}
    keyword_counter = {}
    hooks = []
    subjects = []

    for insight in all_insights:
        for pp in insight.get("pain_points", []):
            pain_counter[pp] = pain_counter.get(pp, 0) + 1
        for kw in insight.get("keywords", []):
            keyword_counter[kw] = keyword_counter.get(kw, 0) + 1
        if insight.get("ad_hook"):
            hooks.append(insight["ad_hook"])
        if insight.get("email_subject"):
            subjects.append(insight["email_subject"])

    top_pain_points = sorted(pain_counter.items(), key=lambda x: -x[1])[:10]
    top_keywords = sorted(keyword_counter.items(), key=lambda x: -x[1])[:20]

    return {
        "top_pain_points": [p for p, _ in top_pain_points],
        "top_keywords": [k for k, _ in top_keywords],
        "ad_hooks": hooks[:15],
        "email_subjects": subjects[:15],
        "total_posts_analysed": len(all_insights)
    }


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

async def run(dry_run: bool = DRY_RUN, headless: bool = True) -> dict:
    """
    Haupt-Pipeline:
    1. Facebook-Gruppen scrapen
    2. Posts mit Claude analysieren
    3. Insights in DB speichern
    4. Zusammenfassung für Creative Agent ausgeben
    """
    log.info("=" * 60)
    log.info("UC GROUPS INTEL AGENT — Start")
    log.info(f"Modus: {'DRY-RUN (kein Speichern)' if dry_run else 'LIVE'}")
    log.info("=" * 60)

    # Schritt 1: Gruppen scrapen
    log.info(f"Scrape {len(UC_FACEBOOK_GROUPS)} Facebook-Gruppen...")
    groups_data = await scrape_all_groups(headless=headless)

    if not groups_data:
        log.warning("Keine Daten gescrapt — prüfe ob Gruppen öffentlich zugänglich sind.")
        log.info("Fallback: Nutze Demo-Posts für Analyse...")
        groups_data = _get_demo_posts()

    # Schritt 2: Posts analysieren
    all_insights = []
    for group_name, posts in groups_data.items():
        log.info(f"Analysiere {len(posts)} Posts aus '{group_name}'...")
        for i, post in enumerate(posts, 1):
            insight = analyse_post_with_claude(post, group_name)
            insight["group_name"] = group_name
            insight["post_text"] = post
            all_insights.append(insight)

            if not dry_run and any(insight[k] for k in ["pain_points", "keywords"]):
                insert_group_insight(
                    group_name=group_name,
                    post_text=post,
                    pain_points=insight.get("pain_points", []),
                    emotions=insight.get("emotions", []),
                    keywords=insight.get("keywords", []),
                    ad_hook=insight.get("ad_hook", ""),
                    email_subject=insight.get("email_subject", "")
                )

            log.info(f"  [{i}/{len(posts)}] Hook: {insight.get('ad_hook', '—')}")
            await asyncio.sleep(0.5)  # Rate Limiting

    # Schritt 3: Zusammenfassung
    summary = generate_insights_summary(all_insights)

    # Zusammenfassung ausgeben
    print("\n" + "=" * 60)
    print("INSIGHTS ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"\nPosts analysiert: {summary.get('total_posts_analysed', 0)}")

    print("\n🎯 TOP PAIN POINTS:")
    for pp in summary.get("top_pain_points", []):
        print(f"  → {pp}")

    print("\n📝 TOP KEYWORDS (echte Betroffenen-Sprache):")
    for kw in summary.get("top_keywords", []):
        print(f"  • {kw}")

    print("\n💡 AD HOOKS (fertige Headlines):")
    for hook in summary.get("ad_hooks", [])[:8]:
        print(f"  ✓ {hook}")

    print("\n📧 EMAIL BETREFFZEILEN:")
    for subj in summary.get("email_subjects", [])[:8]:
        print(f"  ✓ {subj}")

    # Zusammenfassung als JSON speichern
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "groups_insights.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "raw_insights": all_insights
        }, f, ensure_ascii=False, indent=2)

    log.info(f"\nInsights gespeichert: {output_path}")
    return summary


def _get_demo_posts() -> dict[str, list[str]]:
    """
    Demo-Posts für Entwicklung/Testing ohne Facebook-Zugang.
    Basieren auf typischen Erfahrungsberichten von CU-Betroffenen.
    """
    return {
        "demo_gruppe": [
            "Ich leide seit 5 Jahren an CU und kein Arzt erklärt mir wirklich was ich essen soll. Ich probiere alles aus aber nichts hilft wirklich. Hat jemand von euch Erfahrungen mit Ernährungsumstellung gemacht die wirklich geholfen hat?",
            "Schub seit 3 Wochen, bin so erschöpft. Kann kaum noch arbeiten. Mein Gastroenterologe sagt nur die Medikamente weiter nehmen aber ich spüre keine Besserung. Fühle mich allein damit.",
            "Endlich in Remission nach 8 Monaten! Was mir geholfen hat: Weizen komplett raus, Stress reduziert und jeden Tag 15 Minuten Meditation. Teile es gerne weil ich so lange gesucht habe.",
            "Weiß jemand was gegen nächtliche Krämpfe hilft? Schlafe seit Wochen kaum. Die Müdigkeit macht mich kaputt. Cortison will ich nicht mehr, die Nebenwirkungen waren schlimmer als die CU.",
            "Reisen mit CU ist eine Katastrophe. Jede Reise = Stress = Schub. Gibt es Tipps wie man das in den Griff kriegt? Will nicht mehr zu Hause festsitzen.",
            "Mein Darm ist seit dem letzten Schub so empfindlich. Selbst wenn ich aufpasse explodiert es manchmal. Welche Lebensmittel vertragt ihr ohne Probleme?",
            "Habe heute mein Blutbild bekommen, Entzündungswerte wieder oben. Dabei hatte ich gedacht es wird besser. So frustrierend wenn man alles richtig machen will und es trotzdem nicht klappt.",
            "Psyche und CU — redet darüber! Mein Arzt ignorierts komplett aber ich glaube der Stress macht meine Schübe schlimmer. Hat jemand damit Erfahrung?",
        ]
    }


def load_saved_insights() -> dict:
    """Lädt gespeicherte Insights aus der JSON-Datei (für andere Agenten)."""
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "groups_insights.json")
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Facebook Groups Intelligence Agent")
    parser.add_argument("--live", action="store_true", help="Live-Modus: Insights in DB speichern")
    parser.add_argument("--no-headless", action="store_true", help="Browser sichtbar anzeigen")
    parser.add_argument("--show-saved", action="store_true", help="Gespeicherte Insights anzeigen")
    args = parser.parse_args()

    if args.show_saved:
        data = load_saved_insights()
        if data:
            print(json.dumps(data.get("summary", {}), indent=2, ensure_ascii=False))
        else:
            print("Keine gespeicherten Insights gefunden. Erst --run ausführen.")
    else:
        asyncio.run(run(
            dry_run=not args.live,
            headless=not args.no_headless
        ))
