"""
Research & Intelligence Agent
Sammelt Pain Points, Gains und Customer Jobs aus öffentlichen Quellen.
Output wird täglich an alle anderen Agenten als Kontext weitergegeben.

Datenquellen:
- Reddit: r/UlcerativeColitis, r/CrohnsDisease, r/IBD, r/de (Suche)
- Amazon.de: Reviews von Colitis-Büchern
- Foren: chronisch-krank.de, magen-darm.de Kommentare
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    ANTHROPIC_API_KEY, CLAUDE_SONNET, PROJECT_NAME,
    NISCHE, ZIELGRUPPE, LIMBIC_PROFILE, TIEFMOTIVE, REPORTS_DIR
)
from db_colitis import save_research_insight, get_recent_insights, init_db

try:
    import anthropic
except ImportError:
    print("[FEHLER] anthropic nicht installiert. Bitte: pip install anthropic")
    sys.exit(1)


# ─── Konfiguration ──────────────────────────────────────────────────────────────

REDDIT_SUBS = [
    "UlcerativeColitis",
    "CrohnsDisease",
    "IBD",
    "Darmkrankheiten",
]

REDDIT_SUCHBEGRIFFE = [
    "Ernährung Colitis",
    "Schub was hilft",
    "leben mit Colitis",
    "Stress Colitis",
    "Medikamente Nebenwirkungen",
    "endlich wieder normal essen",
    "Angst Ausgang Toilette",
]

# Amazon.de ASINs von relevanten Büchern für Review-Scraping
AMAZON_ASINS = [
    "B07ZPVD8CV",  # Beispiel: Colitis-relevantes Buch
    "3833868767",
]


# ─── Reddit Scraping (ohne API Key via public JSON) ─────────────────────────────

async def scrape_reddit_sub(sub: str, limit: int = 25) -> list[dict]:
    """Scrapt Top-Posts eines Subreddits (öffentliches JSON-Endpunkt)."""
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            return [
                {
                    "titel": p["data"].get("title", ""),
                    "text": p["data"].get("selftext", "")[:500],
                    "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                    "score": p["data"].get("score", 0),
                }
                for p in posts
                if p["data"].get("score", 0) > 5
            ]
        except Exception as e:
            print(f"  [Reddit] Fehler bei r/{sub}: {e}")
            return []


async def scrape_reddit_suche(suchbegriff: str, limit: int = 15) -> list[dict]:
    """Sucht auf Reddit nach einem Begriff."""
    url = f"https://www.reddit.com/search.json?q={suchbegriff}&sort=relevance&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            return [
                {
                    "titel": p["data"].get("title", ""),
                    "text": p["data"].get("selftext", "")[:500],
                    "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                    "subreddit": p["data"].get("subreddit", ""),
                }
                for p in posts
            ]
        except Exception as e:
            print(f"  [Reddit] Suchfehler '{suchbegriff}': {e}")
            return []


async def sammle_alle_reddit_posts() -> list[dict]:
    """Sammelt Posts aus mehreren Subreddits parallel."""
    print("[Research] Scrape Reddit...")
    aufgaben = [scrape_reddit_sub(sub) for sub in REDDIT_SUBS]
    aufgaben += [scrape_reddit_suche(s) for s in REDDIT_SUCHBEGRIFFE[:3]]

    ergebnisse = await asyncio.gather(*aufgaben)
    alle_posts = []
    for batch in ergebnisse:
        alle_posts.extend(batch)

    # Duplikate entfernen
    gesehen = set()
    eindeutig = []
    for p in alle_posts:
        key = p.get("url", "")
        if key not in gesehen:
            gesehen.add(key)
            eindeutig.append(p)

    print(f"  → {len(eindeutig)} einzigartige Reddit-Posts gesammelt")
    return eindeutig


# ─── Claude Analyse ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Du bist ein erfahrener Marktforscher und Copywriter spezialisiert auf
Gesundheits-Marketing für die DACH-Region.

Deine Aufgabe: Analysiere Texte von Betroffenen mit {NISCHE} und extrahiere
strukturierte Marketing-Insights für das Projekt {PROJECT_NAME}.

LIMBIC MAP KONTEXT:
{LIMBIC_PROFILE['beschreibung']}
Primäres Limbic-Segment: {LIMBIC_PROFILE['primaer']}
Sekundäres Segment: {LIMBIC_PROFILE['sekundaer']}

TIEFMOTIVE der Zielgruppe:
{chr(10).join(f'- {m}' for m in TIEFMOTIVE)}

Extrahiere NUR echte, authentische Aussagen und Gefühle — keine Erfindungen.
Wenn kein passendes Material vorhanden, liefere eine leere Liste.
"""


def analysiere_mit_claude(posts: list[dict], wissens_kontext: str = "") -> dict:
    """Lässt Claude die gesammelten Posts analysieren und strukturieren."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    posts_text = "\n\n".join([
        f"POST: {p.get('titel', '')}\n{p.get('text', '')[:300]}"
        for p in posts[:40]  # Maximal 40 Posts analysieren
    ])

    prompt = f"""Analysiere folgende Beiträge von Colitis/Crohn-Betroffenen:

{posts_text}

{wissens_kontext}

Extrahiere und strukturiere die Marketing-Insights als JSON mit folgenden Feldern:

{{
  "pain_points": [
    {{
      "inhalt": "Exakte oder leicht paraphrasierte Aussage des Betroffenen",
      "limbic_tag": "balance|dominanz|stimulanz",
      "motiv_tag": "autonomie|zugehoerigkeit|kompetenz",
      "power_quote": "Wörtliches Zitat wenn verfügbar, sonst null"
    }}
  ],
  "gains": [
    {{
      "inhalt": "Was sich die Person wünscht / erhofft",
      "limbic_tag": "balance|dominanz|stimulanz",
      "motiv_tag": "autonomie|zugehoerigkeit|kompetenz"
    }}
  ],
  "customer_jobs": [
    {{
      "inhalt": "Was die Person zu erledigen versucht (Jobs-to-be-done)",
      "kontext": "Kurze Erklärung"
    }}
  ],
  "key_messages": [
    "Kernbotschaft 1 für Ads/Landing Pages",
    "Kernbotschaft 2",
    "Kernbotschaft 3"
  ],
  "ad_hooks": [
    "Möglicher Ad-Hook basierend auf echten Aussagen",
    "Hook 2",
    "Hook 3"
  ]
}}

Antworte NUR mit dem JSON-Objekt, ohne Erklärungstext."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # JSON extrahieren falls in Markdown-Block
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Claude] Analysefehler: {e}")
        return {"pain_points": [], "gains": [], "customer_jobs": [],
                "key_messages": [], "ad_hooks": []}


# ─── Speichern & Output ─────────────────────────────────────────────────────────

def speichere_insights(insights: dict) -> int:
    """Speichert alle Insights in die Datenbank."""
    gespeichert = 0

    for pain in insights.get("pain_points", []):
        save_research_insight(
            typ="pain",
            inhalt=pain.get("inhalt", ""),
            quelle="Reddit",
            limbic_tag=pain.get("limbic_tag"),
            motiv_tag=pain.get("motiv_tag"),
        )
        if pain.get("power_quote"):
            save_research_insight(
                typ="quote",
                inhalt=pain["power_quote"],
                quelle="Reddit",
                limbic_tag=pain.get("limbic_tag"),
            )
        gespeichert += 1

    for gain in insights.get("gains", []):
        save_research_insight(
            typ="gain",
            inhalt=gain.get("inhalt", ""),
            quelle="Reddit",
            limbic_tag=gain.get("limbic_tag"),
            motiv_tag=gain.get("motiv_tag"),
        )
        gespeichert += 1

    for job in insights.get("customer_jobs", []):
        save_research_insight(
            typ="job",
            inhalt=job.get("inhalt", ""),
            quelle="Reddit",
        )
        gespeichert += 1

    return gespeichert


def erstelle_marketing_brief(insights: dict) -> str:
    """Erstellt ein lesbares Marketing Brief aus den Insights."""
    lines = [
        f"# Research Brief — {PROJECT_NAME}",
        f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        "## Pain Points (Limbic: Balance/Dominanz)",
    ]
    for i, p in enumerate(insights.get("pain_points", [])[:10], 1):
        tag = f"[{p.get('limbic_tag', '?')} / {p.get('motiv_tag', '?')}]"
        lines.append(f"{i}. {p.get('inhalt', '')} {tag}")

    lines += ["", "## Gains (Was sie sich wünschen)"]
    for i, g in enumerate(insights.get("gains", [])[:8], 1):
        lines.append(f"{i}. {g.get('inhalt', '')}")

    lines += ["", "## Customer Jobs (Jobs-to-be-done)"]
    for i, j in enumerate(insights.get("customer_jobs", [])[:8], 1):
        lines.append(f"{i}. {j.get('inhalt', '')}")

    lines += ["", "## Key Messages für Ads & Landing Pages"]
    for i, m in enumerate(insights.get("key_messages", []), 1):
        lines.append(f"{i}. {m}")

    lines += ["", "## Ad Hooks (direkt verwendbar)"]
    for i, h in enumerate(insights.get("ad_hooks", []), 1):
        lines.append(f"{i}. {h}")

    return "\n".join(lines)


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

async def run(dry_run: bool = False) -> dict:
    """
    Führt den Research Agent aus.
    dry_run=True: Kein Speichern in DB, nur Output anzeigen.
    """
    print(f"\n{'='*60}")
    print(f"[Research Agent] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # RAG Kontext laden (falls verfügbar)
    try:
        from knowledge_base.query import hole_wissen
        kb_kontext = hole_wissen("Colitis Zielgruppe Pain Points Marktforschung", n=2)
    except Exception:
        kb_kontext = ""

    # Reddit Posts sammeln
    posts = await sammle_alle_reddit_posts()

    if not posts:
        print("[Research] Keine Posts gesammelt — prüfe Internetverbindung")
        return {}

    # Claude Analyse
    print("[Research] Analysiere mit Claude...")
    insights = analysiere_mit_claude(posts, kb_kontext)

    pain_count = len(insights.get("pain_points", []))
    gain_count = len(insights.get("gains", []))
    job_count  = len(insights.get("customer_jobs", []))
    print(f"  → {pain_count} Pain Points, {gain_count} Gains, {job_count} Jobs gefunden")

    # Brief erstellen
    brief = erstelle_marketing_brief(insights)

    # Output speichern
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    datum = datetime.now().strftime("%Y-%m-%d")
    brief_pfad = f"{REPORTS_DIR}/research_brief_{datum}.md"
    Path(brief_pfad).write_text(brief, encoding="utf-8")
    print(f"  → Brief gespeichert: {brief_pfad}")

    # JSON speichern (für andere Agenten)
    json_pfad = f"{REPORTS_DIR}/research_insights_{datum}.json"
    Path(json_pfad).write_text(json.dumps(insights, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    if not dry_run:
        gespeichert = speichere_insights(insights)
        print(f"  → {gespeichert} Insights in Datenbank gespeichert")

    print(brief[:500] + "...\n")
    return insights


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Research Agent — Pain/Gain Analyse")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur anzeigen, nichts in DB speichern")
    args = parser.parse_args()

    init_db()
    asyncio.run(run(dry_run=args.dry_run))
