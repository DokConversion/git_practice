"""
Media Buying Intelligence Agent
Holt täglich aktuellstes Wissen über Meta + Google Ads via Perplexity API.
Kein veraltetes LLM-Wissen — Echtzeit-Suche aus aktuellen Quellen.

Output: media_buy_briefing.json → wird täglich in alle anderen Agenten injiziert.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    PERPLEXITY_API_KEY, PERPLEXITY_API_URL, PERPLEXITY_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_HAIKU,
    REPORTS_DIR
)
from db_colitis import save_mediabuy_briefing, get_todays_briefing, init_db


# ─── Perplexity Anfragen ────────────────────────────────────────────────────────

SUCHANFRAGEN = [
    {
        "plattform": "meta",
        "kategorie": "update",
        "frage": (
            "Was sind die neuesten Änderungen und Best Practices für Meta Facebook "
            "Ads im März 2026? Fokus auf: Algorithmus-Änderungen, Targeting, "
            "Advantage+ Kampagnen, Creative-Trends für Health/Info-Produkte im DACH-Raum."
        ),
    },
    {
        "plattform": "google",
        "kategorie": "update",
        "frage": (
            "Was sind die neuesten Google Ads Best Practices und Änderungen März 2026? "
            "Fokus auf: Performance Max, Search Ads, Conversion-Optimierung für "
            "digitale Produkte und Health-Nische."
        ),
    },
    {
        "plattform": "meta",
        "kategorie": "creative_trend",
        "frage": (
            "Welche Creative-Formate und Hook-Strategien funktionieren aktuell am besten "
            "auf Meta/Instagram für direkte Verkaufs-Ads (keine Lead-Gen)? "
            "Was sind die Top-Performer im Health/Wellness Bereich 2026?"
        ),
    },
    {
        "plattform": "allgemein",
        "kategorie": "strategie",
        "frage": (
            "Was sind die effektivsten Strategien für Self-Liquidating Offer (SLO) Funnels "
            "mit Tiny Offers im digitalen Produkt-Bereich? Aktuelle Benchmarks für "
            "CVR, Order Bump Take Rate, Upsell Rate 2025/2026."
        ),
    },
    {
        "plattform": "allgemein",
        "kategorie": "warnung",
        "frage": (
            "Welche Meta Ads Praktiken und Google Ads Strategien sollte man aktuell "
            "VERMEIDEN? Was führt zu Account-Sperrungen oder schlechter Performance "
            "in der Health/Medical-Nische?"
        ),
    },
]


def perplexity_anfrage(frage: str, modell: str = PERPLEXITY_MODEL) -> str:
    """Sendet eine Anfrage an Perplexity Sonar Pro und gibt die Antwort zurück."""
    if not PERPLEXITY_API_KEY:
        return "[Perplexity API Key fehlt — bitte in .env setzen: PERPLEXITY_API_KEY]"

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": modell,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Du bist ein Performance Marketing Experte mit aktuellem Wissen. "
                    "Antworte präzise, strukturiert und auf Deutsch. "
                    "Nenne konkrete Zahlen und Quellen wenn verfügbar."
                ),
            },
            {"role": "user", "content": frage},
        ],
        "max_tokens": 800,
        "temperature": 0.2,
        "search_recency_filter": "month",
        "return_citations": True,
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(PERPLEXITY_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            inhalt = data["choices"][0]["message"]["content"]
            # Quellen anhängen wenn vorhanden
            quellen = data.get("citations", [])
            if quellen:
                inhalt += "\n\nQuellen: " + ", ".join(quellen[:3])
            return inhalt
    except httpx.HTTPStatusError as e:
        return f"[Perplexity Fehler {e.response.status_code}]: {e.response.text[:200]}"
    except Exception as e:
        return f"[Perplexity Fehler]: {str(e)}"


# ─── Briefing zusammenstellen ────────────────────────────────────────────────────

def erstelle_briefing() -> dict:
    """
    Ruft alle Suchanfragen ab und erstellt das tägliche Media Buying Briefing.
    Gibt strukturiertes Dict zurück.
    """
    print(f"\n{'='*60}")
    print(f"[MediaBuy Intel] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    briefing = {
        "datum": datetime.now().strftime("%Y-%m-%d"),
        "meta_updates": [],
        "google_updates": [],
        "creative_trends": [],
        "winning_strategies": [],
        "avoid_now": [],
        "roher_inhalt": {},
    }

    ids_gespeichert = []

    for anfrage in SUCHANFRAGEN:
        print(f"  [Perplexity] {anfrage['plattform']} / {anfrage['kategorie']}...")
        antwort = perplexity_anfrage(anfrage["frage"])

        # In strukturierte Felder einsortieren
        if anfrage["plattform"] == "meta" and anfrage["kategorie"] == "update":
            briefing["meta_updates"].append(antwort[:600])
        elif anfrage["plattform"] == "google" and anfrage["kategorie"] == "update":
            briefing["google_updates"].append(antwort[:600])
        elif anfrage["kategorie"] == "creative_trend":
            briefing["creative_trends"].append(antwort[:600])
        elif anfrage["kategorie"] == "strategie":
            briefing["winning_strategies"].append(antwort[:600])
        elif anfrage["kategorie"] == "warnung":
            briefing["avoid_now"].append(antwort[:600])

        briefing["roher_inhalt"][f"{anfrage['plattform']}_{anfrage['kategorie']}"] = antwort

        # In DB speichern
        db_id = save_mediabuy_briefing(
            plattform=anfrage["plattform"],
            kategorie=anfrage["kategorie"],
            inhalt=antwort,
        )
        ids_gespeichert.append(db_id)

    print(f"  → {len(ids_gespeichert)} Briefing-Einträge gespeichert")
    return briefing


def formatiere_fuer_agent_prompt(briefing: dict) -> str:
    """
    Formatiert das Briefing als kompakten System-Prompt-Kontext
    für andere Agenten (Ad Copy, Creative, Funnel).
    """
    teile = [
        "=== AKTUELLES MEDIA BUYING BRIEFING (Stand: heute) ===",
        "",
        "META ADS — Aktuelle Updates:",
    ]
    for update in briefing.get("meta_updates", [])[:1]:
        teile.append(update[:400])

    teile += ["", "GOOGLE ADS — Aktuelle Updates:"]
    for update in briefing.get("google_updates", [])[:1]:
        teile.append(update[:400])

    teile += ["", "CREATIVE TRENDS — Was aktuell funktioniert:"]
    for trend in briefing.get("creative_trends", [])[:1]:
        teile.append(trend[:400])

    teile += ["", "WINNING STRATEGIES:"]
    for strat in briefing.get("winning_strategies", [])[:1]:
        teile.append(strat[:300])

    teile += ["", "JETZT VERMEIDEN:"]
    for warn in briefing.get("avoid_now", [])[:1]:
        teile.append(warn[:300])

    teile.append("=" * 60)
    return "\n".join(teile)


def lade_heutiges_briefing_als_kontext() -> str:
    """
    Lädt das heutige Briefing aus der DB und gibt es als Agent-Kontext zurück.
    Fallback: Leerer String wenn kein Briefing vorhanden.
    """
    eintraege = get_todays_briefing()
    if not eintraege:
        return ""

    # Komprimierter Kontext aus DB-Einträgen
    teile = ["=== MEDIA BUYING BRIEFING (Heutig) ==="]
    for e in eintraege[:5]:
        teile.append(f"\n[{e['plattform'].upper()} / {e['kategorie']}]")
        teile.append(e["inhalt"][:350])
    teile.append("=" * 60)
    return "\n".join(teile)


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run(force: bool = False) -> dict:
    """
    Führt den Media Buying Intel Agent aus.
    force=True: Auch wenn heute schon ein Briefing erstellt wurde.
    """
    # Prüfen ob heute schon ein Briefing existiert
    if not force:
        heutiges = get_todays_briefing()
        if heutiges:
            print(f"[MediaBuy Intel] Briefing heute bereits vorhanden ({len(heutiges)} Einträge)")
            briefing = {"datum": datetime.now().strftime("%Y-%m-%d")}
            return briefing

    briefing = erstelle_briefing()

    # Als JSON speichern
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    datum = datetime.now().strftime("%Y-%m-%d")
    pfad = f"{REPORTS_DIR}/mediabuy_briefing_{datum}.json"
    Path(pfad).write_text(
        json.dumps(briefing, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  → Briefing gespeichert: {pfad}")

    # Lesbares Markdown
    md_pfad = f"{REPORTS_DIR}/mediabuy_briefing_{datum}.md"
    Path(md_pfad).write_text(
        formatiere_fuer_agent_prompt(briefing),
        encoding="utf-8"
    )

    return briefing


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Media Buying Intelligence Agent")
    parser.add_argument("--force", action="store_true",
                        help="Briefing auch wenn heute schon erstellt")
    args = parser.parse_args()

    init_db()
    briefing = run(force=args.force)
    print("\n" + formatiere_fuer_agent_prompt(briefing))
