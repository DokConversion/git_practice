"""
Funnel Architect Agent
Generiert und optimiert:
- Tiny Offer Landing Page (Thrive Architect-ready HTML-Blöcke)
- Order Bump Copy
- Upsell 1 + 2 Pages
- Komplette Email-Sequenz (Post-Purchase Onboarding → Upsell → Retention)

Psychologisch fundiert: Limbic Map + Motivkompass.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    ANTHROPIC_API_KEY, CLAUDE_SONNET,
    LIMBIC_PROFILE, TIEFMOTIVE, VALUE_LADDER,
    PROJECT_NAME, ZIELGRUPPE, FUNNEL_OUTPUT_DIR, REPORTS_DIR
)
from db_colitis import get_recent_insights, init_db

try:
    import anthropic
except ImportError:
    print("[FEHLER] anthropic nicht installiert.")
    sys.exit(1)


# ─── System Prompt ──────────────────────────────────────────────────────────────

def erstelle_system_prompt(mediabuy_kontext: str = "", kb_kontext: str = "") -> str:
    return f"""Du bist ein World-Class Conversion Copywriter und Funnel-Stratege
für digitale Health-Produkte im DACH-Raum.

PROJEKT: {PROJECT_NAME}
ZIELGRUPPE: {ZIELGRUPPE}
VALUE LADDER:
- Tiny Offer: {VALUE_LADDER['tiny_offer']['name']} — €{VALUE_LADDER['tiny_offer']['preis']}
- Order Bump: {VALUE_LADDER['order_bump']['name']} — €{VALUE_LADDER['order_bump']['preis']}
- Upsell 1: {VALUE_LADDER['upsell_1']['name']} — €{VALUE_LADDER['upsell_1']['preis']}
- Upsell 2: {VALUE_LADDER['upsell_2']['name']} — €{VALUE_LADDER['upsell_2']['preis']}/Monat

═══════════════════════════════════════════════════════
VERKAUFSPSYCHOLOGIE (PFLICHTANWENDUNG)
═══════════════════════════════════════════════════════

LIMBIC MAP — Funnel-Architektur:
• Tiny Offer Page: BALANCE öffnen (Schmerz/Unsicherheit) → KOMPETENZ liefern
• Order Bump: AUTONOMIE + Knappheit ("Komplettiere dein Arsenal")
• Upsell 1: ZUGEHÖRIGKEIT ("Du bist nicht allein") → Community
• Upsell 2: DOMINANZ ("Behalte die Kontrolle jeden Monat")
• Email Tag 1–3: Balance-Motive (Sicherheit, Schutz)
• Email Tag 4–5: Dominanz-Motive (Kontrolle, Stärke)
• Email Tag 6–7: Kompetenz + Upsell-Pitch

MOTIVKOMPASS — Tiefe Motive:
{chr(10).join(f'• {m}' for m in TIEFMOTIVE)}

TECHNISCHE ANFORDERUNGEN:
- Thrive Architect kompatibel → HTML-Blöcke mit Klassen-Kommentaren
- Mobile-first Formulierungen
- Keine medizinischen Versprechen (DSGVO/HWG-konform)
- "Erfahrungen können variieren" wo nötig

{mediabuy_kontext}
{kb_kontext}
"""


# ─── Landing Page Generator ─────────────────────────────────────────────────────

def generiere_landing_page(client: anthropic.Anthropic,
                            system_prompt: str,
                            pain_points: list[dict]) -> dict:
    """Generiert Tiny Offer Landing Page Copy."""

    pain_text = "\n".join([f"- {p.get('inhalt', '')}" for p in pain_points[:8]])

    prompt = f"""Schreibe die komplette Tiny Offer Landing Page für "{VALUE_LADDER['tiny_offer']['name']}" (€{VALUE_LADDER['tiny_offer']['preis']}).

ECHTE PAIN POINTS DER ZIELGRUPPE:
{pain_text}

STRUKTUR (alle Sektionen als JSON):
{{
  "hero": {{
    "headline": "Haupt-Überschrift (Scroll-Stopper, max 10 Wörter)",
    "subheadline": "Unterstützende Zeile (verstärkt die Headline)",
    "hero_cta": "CTA-Text des Buttons"
  }},
  "problem_sektion": {{
    "ueberschrift": "Erkennst du dich wieder?",
    "punkte": ["Problem 1", "Problem 2", "Problem 3", "Problem 4", "Problem 5"]
  }},
  "agitation": {{
    "text": "2-3 Sätze: Was passiert wenn sich nichts ändert? Emotional, nicht medizinisch."
  }},
  "loesung": {{
    "ueberschrift": "Überschrift für die Lösung",
    "intro": "Was der Leitfaden bietet (2-3 Sätze)",
    "benefits": [
      {{"icon": "✓", "text": "Konkreter Nutzen 1"}},
      {{"icon": "✓", "text": "Konkreter Nutzen 2"}},
      {{"icon": "✓", "text": "Konkreter Nutzen 3"}},
      {{"icon": "✓", "text": "Konkreter Nutzen 4"}},
      {{"icon": "✓", "text": "Konkreter Nutzen 5"}}
    ]
  }},
  "vertrauen": {{
    "ueberschrift": "Über den Autor / Warum vertrauen?",
    "text": "2-3 Sätze Credibility-Building (ohne falsche Versprechungen)"
  }},
  "angebot": {{
    "ueberschrift": "Dein Angebot",
    "preis_text": "Nur €{VALUE_LADDER['tiny_offer']['preis']}",
    "wert_erklaerung": "Warum dieser Preis ein No-Brainer ist (1-2 Sätze)",
    "cta_haupt": "Jetzt für nur €{VALUE_LADDER['tiny_offer']['preis']} sichern",
    "garantie": "30-Tage Geld-zurück-Garantie ohne Fragen"
  }},
  "faq": [
    {{"frage": "Häufige Frage 1", "antwort": "Antwort"}},
    {{"frage": "Häufige Frage 2", "antwort": "Antwort"}},
    {{"frage": "Häufige Frage 3", "antwort": "Antwort"}}
  ],
  "limbic_analyse": "Welches Limbic-Segment & Motiv dominiert diese Page?"
}}

Antworte NUR mit dem JSON-Objekt."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Funnel LP] Fehler: {e}")
        return {}


# ─── Order Bump + Upsell Generator ──────────────────────────────────────────────

def generiere_upsells(client: anthropic.Anthropic, system_prompt: str) -> dict:
    """Generiert Order Bump + Upsell 1 + 2 Copy."""

    prompt = f"""Generiere Copy für den kompletten Upsell-Stack als JSON:

{{
  "order_bump": {{
    "headline": "Kurze, urgente Headline (max 8 Wörter)",
    "text": "2-3 Sätze: Was bekommt der Käufer zusätzlich? Warum JETZT?",
    "preis_text": "Nur €{VALUE_LADDER['order_bump']['preis']} dazu",
    "checkbox_text": "Ja, ich möchte [Produkt] für nur €{VALUE_LADDER['order_bump']['preis']} dazunehmen",
    "limbic": "Welches Motiv wird aktiviert?"
  }},
  "upsell_1": {{
    "video_headline": "VSL-Headline für Upsell 1 Page",
    "hook": "Erster Satz des VSL-Scripts (Pattern Interrupt)",
    "brücke": "Übergang von Tiny Offer zu Upsell (warum brauchen sie mehr?)",
    "angebot_text": "Was ist {VALUE_LADDER['upsell_1']['name']}? (3-5 Bullets)",
    "preis_text": "Nur €{VALUE_LADDER['upsell_1']['preis']} — einmalig",
    "ja_cta": "Ja! Ich will den {VALUE_LADDER['upsell_1']['name']}",
    "nein_link": "Nein danke, ich verzichte auf den Bonus-Kurs",
    "limbic": "Zugehörigkeit + Kompetenz"
  }},
  "upsell_2": {{
    "headline": "Mitgliedschaft Headline",
    "beschreibung": "Was bekommt man monatlich? (3-4 Bullets)",
    "preis_text": "Nur €{VALUE_LADDER['upsell_2']['preis']}/Monat — jederzeit kündbar",
    "ja_cta": "Ja, ich bin dabei",
    "nein_link": "Nein danke, ohne Community-Support",
    "limbic": "Zugehörigkeit + Dominanz (monatliche Kontrolle)"
  }}
}}

Antworte NUR mit dem JSON-Objekt."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=1800,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Funnel Upsell] Fehler: {e}")
        return {}


# ─── Email Sequenz Generator ─────────────────────────────────────────────────────

def generiere_email_sequenz(client: anthropic.Anthropic,
                             system_prompt: str,
                             pain_points: list[dict]) -> list[dict]:
    """Generiert 7-tägige Post-Purchase Email-Sequenz."""

    pain_text = "\n".join([f"- {p.get('inhalt', '')}" for p in pain_points[:5]])

    prompt = f"""Schreibe eine 7-E-Mail Post-Purchase-Sequenz für Käufer des Tiny Offers.

LIMBIC-SEQUENZ:
- E-Mail 1–3: BALANCE (Sicherheit, "Du hast die richtige Entscheidung getroffen")
- E-Mail 4–5: DOMINANZ/AUTONOMIE (Kontrolle, Empowerment)
- E-Mail 6: KOMPETENZ ("Du verstehst jetzt deinen Körper")
- E-Mail 7: UPSELL-PITCH (Upsell 1: {VALUE_LADDER['upsell_1']['name']})

PAIN POINTS ZUM AUFGREIFEN:
{pain_text}

Als JSON-Array:
[
  {{
    "tag": 1,
    "betreff": "E-Mail Betreff (max 50 Zeichen, kein Spam-Trigger)",
    "preheader": "Preview-Text (max 85 Zeichen)",
    "inhalt": "Kompletter E-Mail-Text (informell, 'du', 150-250 Wörter)",
    "cta_text": "Button-Text",
    "cta_ziel": "URL oder Aktion (z.B. 'Kapitel 1 im Guide')",
    "limbic_segment": "balance|dominanz|kompetenz",
    "motiv": "autonomie|zugehoerigkeit|kompetenz",
    "zweck": "Onboarding|Wert-Lieferung|Upsell-Vorbereitung|Upsell"
  }}
]

Antworte NUR mit dem JSON-Array."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Funnel Email] Fehler: {e}")
        return []


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> dict:
    """Führt den Funnel Architect Agent aus."""
    print(f"\n{'='*60}")
    print(f"[Funnel Architect] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # Kontexte laden
    try:
        from agent_mediabuy_intel import lade_heutiges_briefing_als_kontext
        mediabuy_kontext = lade_heutiges_briefing_als_kontext()
    except Exception:
        mediabuy_kontext = ""

    try:
        from knowledge_base.query import hole_wissen
        kb_kontext = hole_wissen("Funnel Tiny Offer Upsell Conversion Optimierung", n=3,
                                  kategorie="funnels")
    except Exception:
        kb_kontext = ""

    pain_points = get_recent_insights(tage=14, typ="pain")
    if not pain_points:
        pain_points = [
            {"inhalt": "Ich weiß nie was ich essen darf ohne einen Schub zu riskieren"},
            {"inhalt": "Jeder Ausflug wird zur Planung — wo ist die nächste Toilette"},
            {"inhalt": "Meine Ärzte geben mir kaum praktische Alltagstipps"},
        ]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system_prompt = erstelle_system_prompt(mediabuy_kontext, kb_kontext)

    Path(FUNNEL_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    datum = datetime.now().strftime("%Y-%m-%d")

    # Landing Page
    print("[Funnel] Generiere Landing Page...")
    lp = generiere_landing_page(client, system_prompt, pain_points)
    if lp:
        pfad = f"{FUNNEL_OUTPUT_DIR}/landing_page_{datum}.json"
        Path(pfad).write_text(json.dumps(lp, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"  → Landing Page: {pfad}")
        print(f"  Headline: {lp.get('hero', {}).get('headline', '?')}")

    # Upsells
    print("[Funnel] Generiere Upsell-Stack...")
    upsells = generiere_upsells(client, system_prompt)
    if upsells:
        pfad = f"{FUNNEL_OUTPUT_DIR}/upsell_stack_{datum}.json"
        Path(pfad).write_text(json.dumps(upsells, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"  → Upsell Stack: {pfad}")

    # Email-Sequenz
    print("[Funnel] Generiere Email-Sequenz (7 Tage)...")
    emails = generiere_email_sequenz(client, system_prompt, pain_points)
    if emails:
        pfad = f"{FUNNEL_OUTPUT_DIR}/email_sequenz_{datum}.json"
        Path(pfad).write_text(json.dumps(emails, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"  → {len(emails)} Emails generiert: {pfad}")

        # Lesbares Markdown
        md_lines = [f"# Email-Sequenz — {datum}\n"]
        for email in emails:
            md_lines += [
                f"## E-Mail Tag {email.get('tag', '?')} [{email.get('limbic_segment', '').upper()}]",
                f"**Zweck:** {email.get('zweck', '')}",
                f"**Betreff:** {email.get('betreff', '')}",
                f"**Preheader:** {email.get('preheader', '')}",
                "",
                email.get("inhalt", ""),
                "",
                f"**CTA:** [{email.get('cta_text', '')}]({email.get('cta_ziel', '')})",
                "",
                "---",
                "",
            ]
        md_pfad = f"{FUNNEL_OUTPUT_DIR}/email_sequenz_{datum}.md"
        Path(md_pfad).write_text("\n".join(md_lines), encoding="utf-8")

    return {"landing_page": lp, "upsells": upsells, "emails": emails}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Funnel Architect Agent")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--nur-emails", action="store_true",
                        help="Nur Email-Sequenz generieren")
    args = parser.parse_args()

    init_db()
    run(dry_run=args.dry_run)
