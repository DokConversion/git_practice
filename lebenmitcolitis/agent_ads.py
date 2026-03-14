"""
Ad Copy Agent
Generiert täglich neue Meta + Google Ad-Varianten.
Psychologisch fundiert: Limbic Map (Häusel) + Motivkompass.
Nutzt Insider-Wissen aus RAG + tagesaktuelles Perplexity Briefing.

Output: CSV-Dateien → direkt import-ready für Meta/Google Ads Manager
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    ANTHROPIC_API_KEY, CLAUDE_SONNET, ADS_PRO_TAG,
    LIMBIC_PROFILE, TIEFMOTIVE, VALUE_LADDER,
    PROJECT_NAME, ZIELGRUPPE, ADS_OUTPUT_DIR, REPORTS_DIR
)
from db_colitis import (
    save_ad_copy, get_recent_insights, init_db
)

try:
    import anthropic
except ImportError:
    print("[FEHLER] anthropic nicht installiert. Bitte: pip install anthropic")
    sys.exit(1)


# ─── System Prompt (Limbic Map + Motivkompass fest eingebaut) ──────────────────

def erstelle_system_prompt(mediabuy_kontext: str = "", kb_kontext: str = "") -> str:
    return f"""Du bist ein World-Class Direct Response Copywriter spezialisiert auf
Performance Marketing für Health-Produkte im DACH-Raum.

PROJEKT: {PROJECT_NAME}
ZIELGRUPPE: {ZIELGRUPPE}
PRODUKT: {VALUE_LADDER['tiny_offer']['name']} — {VALUE_LADDER['tiny_offer']['beschreibung']}
PREIS: €{VALUE_LADDER['tiny_offer']['preis']}

═══════════════════════════════════════════════════════
VERKAUFSPSYCHOLOGIE — PFLICHTANWENDUNG
═══════════════════════════════════════════════════════

LIMBIC MAP (Häusel) — Profil der Zielgruppe:
{LIMBIC_PROFILE['beschreibung']}
→ Primäres Segment: {LIMBIC_PROFILE['primaer']} (Sicherheit, Harmonie, Angstvermeidung)
→ Sekundäres Segment: {LIMBIC_PROFILE['sekundaer']} (Kontrolle, Stärke, Nicht-ausgeliefert-sein)
→ NICHT ansprechen: Stimulanz/Abenteuer — das passt NICHT zur Zielgruppe

MOTIVKOMPASS (Scheier/Held) — Tiefe Motive:
{chr(10).join(f'→ {m}' for m in TIEFMOTIVE)}

PFLICHT: Vor jedem Ad-Text analysiere:
1. Welches Limbic-Segment wird angesprochen?
2. Welches Tiefmotiv wird aktiviert?
3. Begründe kurz (1 Satz)

═══════════════════════════════════════════════════════
DIREKTES RESPONSE COPYWRITING REGELN
═══════════════════════════════════════════════════════
- Kein Freebie-Frame — der Leser bezahlt sofort (Tiny Offer Direktverkauf)
- Hook in den ersten 3 Wörtern/Zeilen — Scroll-Stopper
- Problem → Agitation → Solution → CTA (PAS-Formel)
- Echte Sprache der Betroffenen nutzen (keine klinische Sprache)
- CTA ist direkt und konkret: "Jetzt für nur €12 holen" nicht "Mehr erfahren"
- Headline: Max 6 Wörter für Google, max 40 Zeichen für Meta

{mediabuy_kontext}

{kb_kontext}
"""


# ─── Meta Ad Generator ──────────────────────────────────────────────────────────

def generiere_meta_ads(client: anthropic.Anthropic,
                        pain_points: list[dict],
                        system_prompt: str,
                        anzahl: int = 3) -> list[dict]:
    """Generiert Meta/Facebook Ad Varianten."""

    pain_text = "\n".join([
        f"- [{p.get('limbic_tag', '?')}] {p.get('inhalt', '')}"
        for p in pain_points[:10]
    ])

    prompt = f"""Generiere {anzahl} verschiedene Meta/Facebook Ad-Varianten für das Tiny Offer.

ECHTE PAIN POINTS DER ZIELGRUPPE (nutze deren Sprache!):
{pain_text}

Für jede Variante, antworte als JSON-Array:
[
  {{
    "variante": 1,
    "headline": "Max 40 Zeichen — Scroll-Stopper",
    "primary_text": "Der Haupt-Werbetext, 2-4 Absätze. Nutze PAS-Formel. Max 300 Zeichen.",
    "description": "Kurze Beschreibung unter dem Bild, max 30 Zeichen",
    "cta_button": "JETZT_KAUFEN|MEHR_ERFAHREN|ANGEBOT_ANFORDERN",
    "format_empfehlung": "1:1 Feed|9:16 Reels|1:1 Stories",
    "limbic_segment": "balance|dominanz",
    "tiefmotiv": "autonomie|zugehoerigkeit|kompetenz",
    "begruendung": "Warum diese psych. Ansprache für diese Zielgruppe?"
  }}
]

Antworte NUR mit dem JSON-Array."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=2500,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Ads Meta] Fehler: {e}")
        return []


# ─── Google Ad Generator ─────────────────────────────────────────────────────────

def generiere_google_ads(client: anthropic.Anthropic,
                          pain_points: list[dict],
                          system_prompt: str,
                          anzahl: int = 2) -> list[dict]:
    """Generiert Google Search Ad Varianten (RSA-Format)."""

    pain_text = "\n".join([f"- {p.get('inhalt', '')}" for p in pain_points[:8]])

    prompt = f"""Generiere {anzahl} Google Search Ad Varianten (Responsive Search Ads).

ZIEL-KEYWORDS: "colitis ernährung", "colitis ulcerosa hilfe", "leben mit colitis",
               "colitis schub was tun", "colitis ernährungsplan"

PAIN POINTS DER SUCHENDEN:
{pain_text}

Für jede Variante als JSON-Array:
[
  {{
    "variante": 1,
    "headline_1": "Max 30 Zeichen",
    "headline_2": "Max 30 Zeichen",
    "headline_3": "Max 30 Zeichen",
    "description_1": "Max 90 Zeichen. Benefit + CTA.",
    "description_2": "Max 90 Zeichen. Vertrauensaufbau oder Dringlichkeit.",
    "keyword_intent": "informational|commercial|transactional",
    "limbic_segment": "balance|dominanz",
    "tiefmotiv": "autonomie|zugehoerigkeit|kompetenz",
    "begruendung": "Kurze Begründung"
  }}
]

Antworte NUR mit dem JSON-Array."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Ads Google] Fehler: {e}")
        return []


# ─── CSV Export ──────────────────────────────────────────────────────────────────

def exportiere_meta_csv(ads: list[dict], pfad: str):
    """Exportiert Meta Ads im Format für Bulk-Upload."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variante", "headline", "primary_text", "description",
            "cta_button", "format_empfehlung", "limbic_segment",
            "tiefmotiv", "begruendung"
        ])
        writer.writeheader()
        writer.writerows(ads)
    print(f"  → Meta CSV: {pfad}")


def exportiere_google_csv(ads: list[dict], pfad: str):
    """Exportiert Google Ads im RSA-Format."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variante", "headline_1", "headline_2", "headline_3",
            "description_1", "description_2", "keyword_intent",
            "limbic_segment", "tiefmotiv", "begruendung"
        ])
        writer.writeheader()
        writer.writerows(ads)
    print(f"  → Google CSV: {pfad}")


# ─── Lesbares Output-Format ──────────────────────────────────────────────────────

def formatiere_ads_report(meta_ads: list[dict], google_ads: list[dict]) -> str:
    """Erstellt lesbares Markdown-Report für Marc."""
    lines = [
        f"# Ad Copy Report — {datetime.now().strftime('%d.%m.%Y')}",
        f"Generiert für: {PROJECT_NAME}",
        "",
        "## META ADS",
        "",
    ]

    for ad in meta_ads:
        v = ad.get("variante", "?")
        lines += [
            f"### Variante {v} [{ad.get('limbic_segment', '?').upper()} / {ad.get('tiefmotiv', '?')}]",
            f"**Psychologie:** {ad.get('begruendung', '')}",
            "",
            f"**Headline:** {ad.get('headline', '')}",
            f"**Primary Text:**",
            f"> {ad.get('primary_text', '')}",
            f"**Description:** {ad.get('description', '')}",
            f"**CTA:** {ad.get('cta_button', '')} | **Format:** {ad.get('format_empfehlung', '')}",
            "",
            "---",
            "",
        ]

    lines += ["## GOOGLE ADS (RSA)", ""]
    for ad in google_ads:
        v = ad.get("variante", "?")
        lines += [
            f"### Variante {v} [{ad.get('limbic_segment', '?').upper()}]",
            f"**Psychologie:** {ad.get('begruendung', '')}",
            "",
            f"**H1:** {ad.get('headline_1', '')}",
            f"**H2:** {ad.get('headline_2', '')}",
            f"**H3:** {ad.get('headline_3', '')}",
            f"**Desc 1:** {ad.get('description_1', '')}",
            f"**Desc 2:** {ad.get('description_2', '')}",
            f"**Intent:** {ad.get('keyword_intent', '')}",
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> dict:
    """Führt den Ad Copy Agent aus."""
    print(f"\n{'='*60}")
    print(f"[Ad Copy Agent] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # Kontexte laden
    try:
        from agent_mediabuy_intel import lade_heutiges_briefing_als_kontext
        mediabuy_kontext = lade_heutiges_briefing_als_kontext()
    except Exception:
        mediabuy_kontext = ""

    try:
        from knowledge_base.query import hole_wissen
        kb_kontext = hole_wissen(
            "Meta Ads Direct Response Copy Health Nische Tiny Offer",
            n=3, kategorie="media_buying"
        )
    except Exception:
        kb_kontext = ""

    # Pain Points aus DB
    pain_points = get_recent_insights(tage=7, typ="pain")
    if not pain_points:
        print("  [Hinweis] Keine Pain Points in DB — Research Agent zuerst ausführen")
        pain_points = [
            {"inhalt": "Ich weiß nie was ich essen darf ohne einen Schub zu bekommen",
             "limbic_tag": "balance"},
            {"inhalt": "Spontane Ausflüge sind unmöglich — ich muss immer eine Toilette in der Nähe haben",
             "limbic_tag": "balance"},
            {"inhalt": "Ich will endlich wieder normal mit meiner Familie essen können",
             "limbic_tag": "balance"},
        ]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system_prompt = erstelle_system_prompt(mediabuy_kontext, kb_kontext)

    # Meta Ads generieren
    meta_anzahl = max(2, ADS_PRO_TAG - 2)
    print(f"[Ads] Generiere {meta_anzahl} Meta Ads...")
    meta_ads = generiere_meta_ads(client, pain_points, system_prompt, meta_anzahl)
    print(f"  → {len(meta_ads)} Meta Ads generiert")

    # Google Ads generieren
    google_anzahl = min(2, ADS_PRO_TAG)
    print(f"[Ads] Generiere {google_anzahl} Google Ads...")
    google_ads = generiere_google_ads(client, pain_points, system_prompt, google_anzahl)
    print(f"  → {len(google_ads)} Google Ads generiert")

    # Speichern
    datum = datetime.now().strftime("%Y-%m-%d")
    Path(ADS_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if not dry_run:
        for ad in meta_ads:
            save_ad_copy(
                plattform="meta",
                headline=ad.get("headline", ""),
                primary_text=ad.get("primary_text", ""),
                description=ad.get("description"),
                cta=ad.get("cta_button"),
                limbic_segment=ad.get("limbic_segment"),
                tiefmotiv=ad.get("tiefmotiv"),
                begruendung=ad.get("begruendung"),
            )
        for ad in google_ads:
            save_ad_copy(
                plattform="google",
                headline=ad.get("headline_1", ""),
                primary_text=f"{ad.get('description_1', '')} {ad.get('description_2', '')}",
                limbic_segment=ad.get("limbic_segment"),
                tiefmotiv=ad.get("tiefmotiv"),
                begruendung=ad.get("begruendung"),
            )

    exportiere_meta_csv(meta_ads, f"{ADS_OUTPUT_DIR}/meta_ads_{datum}.csv")
    exportiere_google_csv(google_ads, f"{ADS_OUTPUT_DIR}/google_ads_{datum}.csv")

    report = formatiere_ads_report(meta_ads, google_ads)
    report_pfad = f"{REPORTS_DIR}/ad_report_{datum}.md"
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(report_pfad).write_text(report, encoding="utf-8")
    print(f"  → Report: {report_pfad}")
    print("\n" + report[:600] + "...")

    return {"meta_ads": meta_ads, "google_ads": google_ads}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ad Copy Agent — Meta + Google")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur Output, nicht in DB speichern")
    args = parser.parse_args()

    init_db()
    run(dry_run=args.dry_run)
