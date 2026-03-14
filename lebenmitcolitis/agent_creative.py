"""
Creative Director Agent
Generiert Ad-Creatives via Google Gemini Imagen 3.
Erstellt Scripts für UGC-Style Video-Ads.
Input: Pain Points aus Research Agent + Media Buying Briefing.
"""

import base64
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from config_colitis import (
    ANTHROPIC_API_KEY, CLAUDE_SONNET,
    GOOGLE_AI_API_KEY, IMAGEN_MODEL,
    LIMBIC_PROFILE, VALUE_LADDER,
    PROJECT_NAME, ZIELGRUPPE, CREATIVE_OUTPUT_DIR, REPORTS_DIR
)
from db_colitis import get_recent_insights, init_db

try:
    import anthropic
except ImportError:
    anthropic = None


# ─── Imagen 3 via Google AI API ─────────────────────────────────────────────────

IMAGEN_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{IMAGEN_MODEL}:generateImages"
)


def generiere_bild_imagen3(prompt: str, format: str = "1:1") -> bytes | None:
    """
    Generiert ein Bild via Google Imagen 3.
    format: '1:1' | '9:16' | '16:9'
    """
    if not GOOGLE_AI_API_KEY:
        print("  [Imagen] GOOGLE_AI_API_KEY fehlt — Bild wird nicht generiert")
        return None

    # Aspect Ratio Mapping
    aspect_map = {"1:1": "SQUARE", "9:16": "PORTRAIT", "16:9": "LANDSCAPE"}
    aspect = aspect_map.get(format, "SQUARE")

    payload = {
        "prompt": prompt,
        "number_of_images": 1,
        "aspect_ratio": aspect,
        "safety_filter_level": "BLOCK_MEDIUM_AND_ABOVE",
        "person_generation": "ALLOW_ADULT",
    }

    headers = {"Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{IMAGEN_API_URL}?key={GOOGLE_AI_API_KEY}",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            images = data.get("generatedImages", [])
            if images:
                b64 = images[0].get("image", {}).get("imageBytes", "")
                return base64.b64decode(b64) if b64 else None
    except Exception as e:
        print(f"  [Imagen] Fehler: {e}")
        return None


def speichere_bild(bild_bytes: bytes, dateiname: str) -> str:
    """Speichert generiertes Bild lokal."""
    Path(CREATIVE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    pfad = f"{CREATIVE_OUTPUT_DIR}/{dateiname}"
    Path(pfad).write_bytes(bild_bytes)
    return pfad


# ─── Claude: Creative Briefs + Prompts ──────────────────────────────────────────

def erstelle_imagen_prompts(pain_points: list[dict],
                             mediabuy_kontext: str = "",
                             kb_kontext: str = "") -> list[dict]:
    """Lässt Claude optimierte Imagen 3 Prompts für Ad-Creatives erstellen."""
    if not anthropic or not ANTHROPIC_API_KEY:
        return _fallback_prompts()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    pain_text = "\n".join([f"- {p.get('inhalt', '')}" for p in pain_points[:6]])

    system = f"""Du bist ein Creative Director spezialisiert auf Performance Marketing.
Du erstellt präzise Imagen 3 Prompts für emotionale, conversion-starke Ad-Bilder.

ZIELGRUPPE: {ZIELGRUPPE}
LIMBIC: {LIMBIC_PROFILE['primaer']} (Sicherheit, Kontrolle, Harmonie)
PRODUKT: {VALUE_LADDER['tiny_offer']['name']}

REGELN für Imagen 3 Prompts:
- Hyperrealistisch, photographisch — kein Illustration-Style
- Emotionale Szenen die Pain/Gain der Zielgruppe verkörpern
- Keine Text-Overlays im Bild (wird separat hinzugefügt)
- Keine klinischen/medizinischen Darstellungen
- Menschen: authentisch, nicht model-perfekt
- Warme, hoffnungsvolle Bildsprache (nicht doom-and-gloom)

{mediabuy_kontext}
{kb_kontext}"""

    prompt = f"""Erstelle 6 Imagen 3 Prompts für Ad-Creatives.

PAIN POINTS DER ZIELGRUPPE:
{pain_text}

Je 2 pro Kategorie:
1. PAIN (zeigt das Problem — triggert Balance-Motiv)
2. GAIN (zeigt das Ergebnis — aktiviert Autonomie-Motiv)
3. SOCIAL PROOF STYLE (authentische Person mit Erleichterung/Freude)

Als JSON-Array:
[
  {{
    "nr": 1,
    "kategorie": "pain|gain|social_proof",
    "format": "1:1|9:16",
    "plattform": "meta|google|beide",
    "imagen_prompt": "Detaillierter, präziser englischer Prompt für Imagen 3 (80-120 Wörter)",
    "beschreibung_de": "Deutsche Beschreibung was das Bild zeigt",
    "text_overlay": "Empfohlener Text-Overlay auf dem Bild (kurz, max 8 Wörter)",
    "limbic_verbindung": "Warum dieses Bild das Balance/Dominanz-Motiv anspricht"
  }}
]

Antworte NUR mit dem JSON-Array."""

    try:
        response = client.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Creative] Claude Fehler: {e}")
        return _fallback_prompts()


def _fallback_prompts() -> list[dict]:
    return [
        {
            "nr": 1, "kategorie": "pain", "format": "1:1", "plattform": "meta",
            "imagen_prompt": (
                "Photorealistic portrait of a tired German woman in her 30s sitting on "
                "a bathroom floor at night, phone in hand searching for help, soft bathroom "
                "lighting, candid and authentic, not staged, slight worry on face, "
                "warm indoor light, shallow depth of field, documentary style photography"
            ),
            "beschreibung_de": "Erschöpfte Frau nachts im Bad — zeigt den Pain",
            "text_overlay": "Kennst du das?",
            "limbic_verbindung": "Balance — Unsicherheit, Hilflosigkeit ansprechen",
        },
        {
            "nr": 2, "kategorie": "gain", "format": "9:16", "plattform": "meta",
            "imagen_prompt": (
                "Photorealistic image of a happy German family of four having a relaxed "
                "outdoor barbecue, woman in her 35s laughing freely, sunny summer day, "
                "authentic casual clothes, no stress visible, warm golden hour lighting, "
                "candid photography style, sense of freedom and normality"
            ),
            "beschreibung_de": "Freie, entspannte Frau beim Grillen — zeigt den Gain",
            "text_overlay": "Endlich wieder frei sein",
            "limbic_verbindung": "Autonomie + Balance — Kontrolle und Normalität",
        },
    ]


# ─── UGC Video Script Generator ─────────────────────────────────────────────────

def generiere_ugc_scripts(pain_points: list[dict],
                            client_claude) -> list[dict]:
    """Generiert UGC-Style Video Scripts für Reels/TikTok-Format."""

    pain_text = "\n".join([f"- {p.get('inhalt', '')}" for p in pain_points[:5]])

    prompt = f"""Generiere 3 UGC-Style Video-Scripts (15-30 Sek) für Meta Reels/Stories.

PAIN POINTS:
{pain_text}

PRODUKT: {VALUE_LADDER['tiny_offer']['name']} — €{VALUE_LADDER['tiny_offer']['preis']}

Struktur: Hook (0-3 Sek) → Problem (3-8 Sek) → Lösung (8-20 Sek) → CTA (20-30 Sek)

Als JSON-Array:
[
  {{
    "nr": 1,
    "dauer": "20 Sek",
    "style": "direkt-kamera|testimonial|text-overlay",
    "hook": "Erster Satz/Text (muss in 3 Sek das Scrollen stoppen)",
    "problem": "Problem-Statement (authentisch, Umgangssprache)",
    "loesung": "Lösung vorstellen (kein Hard-Sell, Solution-First)",
    "cta": "Call-to-Action-Text",
    "visuelle_anweisungen": "Was der Creator/die AI visuell zeigen soll",
    "on_screen_text": ["Text 1 als Overlay", "Text 2", "CTA Text"],
    "ton": "empathisch|direkt|enthusiastisch",
    "limbic": "Welches Motiv wird angesprochen?"
  }}
]

Antworte NUR mit dem JSON-Array."""

    if not client_claude:
        return []

    try:
        response = client_claude.messages.create(
            model=CLAUDE_SONNET,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
    except Exception as e:
        print(f"  [Creative UGC] Fehler: {e}")
        return []


# ─── Hauptfunktion ──────────────────────────────────────────────────────────────

def run(generiere_bilder: bool = True) -> dict:
    """
    Führt den Creative Director Agent aus.
    generiere_bilder=False: Nur Briefs/Scripts, keine Imagen-API-Calls.
    """
    print(f"\n{'='*60}")
    print(f"[Creative Director] Start — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # Kontexte laden
    try:
        from agent_mediabuy_intel import lade_heutiges_briefing_als_kontext
        mediabuy_kontext = lade_heutiges_briefing_als_kontext()
    except Exception:
        mediabuy_kontext = ""

    try:
        from knowledge_base.query import hole_wissen
        kb_kontext = hole_wissen("Creative Trends Meta Ads Health Bilder Videos", n=2)
    except Exception:
        kb_kontext = ""

    pain_points = get_recent_insights(tage=14, typ="pain")
    if not pain_points:
        pain_points = [{"inhalt": "Ich weiß nie was ich essen darf ohne einen Schub"}]

    # Claude Client
    claude_client = None
    if anthropic and ANTHROPIC_API_KEY:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    Path(CREATIVE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    datum = datetime.now().strftime("%Y-%m-%d")

    # Imagen Prompts generieren
    print("[Creative] Erstelle Imagen 3 Prompts...")
    prompts = erstelle_imagen_prompts(pain_points, mediabuy_kontext, kb_kontext)
    print(f"  → {len(prompts)} Prompts erstellt")

    # Bilder generieren (wenn Flag gesetzt und API Key vorhanden)
    generierte_bilder = []
    if generiere_bilder and GOOGLE_AI_API_KEY:
        print("[Creative] Generiere Bilder via Imagen 3...")
        for p in prompts[:4]:  # Max 4 Bilder pro Tag (Kosten sparen)
            print(f"  Bild {p['nr']}: {p.get('beschreibung_de', '')[:50]}...")
            bild = generiere_bild_imagen3(p["imagen_prompt"], p.get("format", "1:1"))
            if bild:
                dateiname = f"creative_{datum}_{p['nr']}_{p['kategorie']}.jpg"
                pfad = speichere_bild(bild, dateiname)
                p["lokaler_pfad"] = pfad
                generierte_bilder.append(pfad)
                print(f"  → Gespeichert: {pfad}")
            else:
                print(f"  → Bild {p['nr']} fehlgeschlagen")
    else:
        if not GOOGLE_AI_API_KEY:
            print("  [Imagen] API Key fehlt — nur Briefs werden erstellt")

    # UGC Scripts
    print("[Creative] Generiere UGC Video Scripts...")
    scripts = generiere_ugc_scripts(pain_points, claude_client)
    print(f"  → {len(scripts)} Scripts erstellt")

    # Alles speichern
    output = {
        "imagen_prompts": prompts,
        "ugc_scripts": scripts,
        "generierte_bilder": generierte_bilder,
    }
    json_pfad = f"{CREATIVE_OUTPUT_DIR}/creative_output_{datum}.json"
    Path(json_pfad).write_text(json.dumps(output, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    # Lesbares Briefing
    lines = [f"# Creative Brief — {datum}\n", "## Imagen 3 Prompts\n"]
    for p in prompts:
        lines += [
            f"### Creative {p['nr']} [{p.get('kategorie', '?').upper()}] — {p.get('format', '?')} — {p.get('plattform', '?')}",
            f"**Beschreibung:** {p.get('beschreibung_de', '')}",
            f"**Text-Overlay:** _{p.get('text_overlay', '')}_",
            f"**Limbic:** {p.get('limbic_verbindung', '')}",
            f"**Prompt:** `{p.get('imagen_prompt', '')[:100]}...`",
            f"{'**Datei:** ' + p.get('lokaler_pfad', '') if p.get('lokaler_pfad') else ''}",
            "",
        ]
    lines += ["\n## UGC Video Scripts\n"]
    for s in scripts:
        lines += [
            f"### Script {s.get('nr', '?')} [{s.get('style', '?')}] — {s.get('dauer', '?')}",
            f"**Hook:** {s.get('hook', '')}",
            f"**Problem:** {s.get('problem', '')}",
            f"**Lösung:** {s.get('loesung', '')}",
            f"**CTA:** {s.get('cta', '')}",
            f"**Ton:** {s.get('ton', '')} | **Limbic:** {s.get('limbic', '')}",
            "",
        ]

    brief_pfad = f"{REPORTS_DIR}/creative_brief_{datum}.md"
    Path(brief_pfad).write_text("\n".join(lines), encoding="utf-8")
    print(f"  → Brief: {brief_pfad}")

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Creative Director Agent")
    parser.add_argument("--no-bilder", action="store_true",
                        help="Keine Imagen 3 API Calls (nur Briefs)")
    args = parser.parse_args()

    init_db()
    run(generiere_bilder=not args.no_bilder)
