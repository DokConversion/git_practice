"""
UC Business — Psychology Expert Agent
========================================
Beherrscht folgende Frameworks in Perfektion und wendet sie auf
die CU-Zielgruppe und alle Marketing-Touchpoints an:

  1. Limbic Map (Häusel) — Emotionssysteme & Kaufmotive
  2. Motivkompass — Grundbedürfnisse hinter dem Kaufverhalten
  3. Spiral Dynamics (Graves/Beck/Cowan) — Wertesysteme/Bewusstseinsstufen
  4. Awareness-Stufen nach Eugene Schwartz — Markt-Bewusstsein
  5. Grundwerte nach Shalom Schwartz — 10 universelle Wertedimensionen

Verwendung:
  python run.py --psychology           → Vollständige Psycho-Analyse der Zielgruppe
  python run.py --psychology --text "..." → Beliebigen Text psychologisch optimieren
"""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK 1: LIMBIC MAP (Häusel)
# ═══════════════════════════════════════════════════════════════════════════════

LIMBIC_TYPES = {
    "Harmoniser": {
        "core_motive": "Geborgenheit, Verbundenheit, Fürsorge",
        "fear": "Ablehnung, Einsamkeit, Konflikte",
        "keywords": ["gemeinsam", "verstanden", "sicher", "begleitet", "Familie", "Gemeinschaft"],
        "design": "Warme Farben, organische Formen, Menschen-Bilder",
        "uc_relevance": "HOCH — viele CU-Patienten fühlen sich isoliert, unverstanden",
        "messaging_hook": "Du musst das nicht alleine durchmachen.",
    },
    "Offener": {
        "core_motive": "Neugier, Abwechslung, Entdeckung",
        "fear": "Langeweile, Stillstand, Einschränkung",
        "keywords": ["neu", "entdecken", "anders", "überraschend", "spannend"],
        "design": "Lebhafte Farben, dynamisch, unkonventionell",
        "uc_relevance": "MITTEL — Selbstoptimierer-Segment",
        "messaging_hook": "Was die Forschung gerade erst herausfindet.",
    },
    "Hedonist": {
        "core_motive": "Genuss, Spaß, Lebensfreude",
        "fear": "Entbehrung, Verzicht, Freudlosigkeit",
        "keywords": ["genießen", "wieder", "Lebensqualität", "Freiheit", "Spaß"],
        "design": "Warm, einladend, sinnlich — Essen, Bewegung, Leben",
        "uc_relevance": "SEHR HOCH — CU raubt Lebensfreude (Essen, Reisen, Spontanität)",
        "messaging_hook": "Wieder essen, was du liebst. Wieder reisen. Wieder leben.",
    },
    "Abenteurer": {
        "core_motive": "Thrill, Risikobereitschaft, Dominanz",
        "fear": "Schwäche, Kontrolle verlieren",
        "keywords": ["stark", "überwinden", "herausfordern", "gewinnen"],
        "design": "Kontrastreiche Bilder, mutige Typographie",
        "uc_relevance": "NIEDRIG/MITTEL — eher bei männlichen Selbstoptimierern",
        "messaging_hook": "CU hat dich verändert. Jetzt veränderst du den Umgang damit.",
    },
    "Performer": {
        "core_motive": "Leistung, Status, Effizienz",
        "fear": "Versagen, Ineffizienz, Bedeutungslosigkeit",
        "keywords": ["effektiv", "schnell", "Ergebnis", "System", "Methode"],
        "design": "Clean, minimalistisch, professionell",
        "uc_relevance": "MITTEL — Patienten die ins Arbeitsleben zurück wollen",
        "messaging_hook": "Ein klares System für einen unklaren Darm.",
    },
    "Gleichgewicht": {
        "core_motive": "Sicherheit, Kontrolle, Stabilität",
        "fear": "Chaos, Unvorhersehbarkeit, Kontrollverlust",
        "keywords": ["sicher", "verstehen", "Kontrolle", "Plan", "wissen warum"],
        "design": "Ruhige Farben, klare Struktur, Vertrauenssignale",
        "uc_relevance": "SEHR HOCH — Schub = totaler Kontrollverlust → größter Pain",
        "messaging_hook": "Endlich verstehen, was in deinem Körper passiert — und was du tun kannst.",
    },
}

# Primäre Limbic-Typen für CU-Zielgruppe (priorisiert)
UC_PRIMARY_LIMBIC = ["Gleichgewicht", "Harmoniser", "Hedonist"]
UC_SECONDARY_LIMBIC = ["Performer", "Offener"]


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK 2: AWARENESS-STUFEN (Eugene Schwartz)
# ═══════════════════════════════════════════════════════════════════════════════

AWARENESS_LEVELS = {
    1: {
        "name": "Unaware",
        "beschreibung": "Person weiß nicht, dass sie ein Problem hat (oder verdrängt es)",
        "wer_ist_das": "Frisch Symptomatische die noch keine Diagnose haben",
        "richtige_botschaft": "Storytelling, Symptom-Identifikation ('Kennst du das?')",
        "falsche_botschaft": "Produktpitch, Lösungsversprechen",
        "kanal": "Meta Ads (Broad Targeting), Content Marketing",
        "beispiel_headline": "5 Zeichen, die dein Darm dir schon lange sendet",
    },
    2: {
        "name": "Problem Aware",
        "beschreibung": "Weiß dass CU ein Problem ist, kennt aber keine Lösung",
        "wer_ist_das": "Neudiagnostizierte, akut Betroffene im Schub",
        "richtige_botschaft": "Problem benennen, validieren, Ursachen erklären",
        "falsche_botschaft": "Direkt zum Produkt — zu früh",
        "kanal": "Google Search ('colitis ulcerosa schub was tun'), Meta",
        "beispiel_headline": "Warum herkömmliche Ratschläge bei CU oft scheitern",
    },
    3: {
        "name": "Solution Aware",
        "beschreibung": "Sucht aktiv nach Lösungsansätzen, kennt aber dein Produkt nicht",
        "wer_ist_das": "Patienten die Ernährung/Lifestyle als Hebel erkannt haben",
        "richtige_botschaft": "Deinen Ansatz als überlegene Lösung positionieren",
        "falsche_botschaft": "Produktdetails ohne Differenzierung",
        "kanal": "Google Search ('colitis ulcerosa ernährungsplan'), Retargeting",
        "beispiel_headline": "Der Unterschied zwischen CU-Ernährung und echter CU-Ernährung",
    },
    4: {
        "name": "Product Aware",
        "beschreibung": "Kennt dein Produkt, hat es aber noch nicht gekauft",
        "wer_ist_das": "Retargeting-Zielgruppe, Email-Subscriber",
        "richtige_botschaft": "Einwände überwinden, sozialer Beweis, Garantie",
        "falsche_botschaft": "Neue Problemdefinition — sie wissen es schon",
        "kanal": "Email-Sequenz Tag 4-7, Retargeting Ads",
        "beispiel_headline": "Was andere CU-Betroffene nach 4 Wochen sagen",
    },
    5: {
        "name": "Most Aware",
        "beschreibung": "Kennt und vertraut deiner Marke — braucht nur einen Anlass",
        "wer_ist_das": "Käufer des Einstiegsprodukts (für Upsell), treue Subscriber",
        "richtige_botschaft": "Nächster Schritt, exklusives Angebot, Community",
        "falsche_botschaft": "Überzeugung — sie sind schon überzeugt",
        "kanal": "Post-Purchase Email, VIP-Liste",
        "beispiel_headline": "Als Compass-Leser: Der nächste Schritt für dich",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK 3: SPIRAL DYNAMICS (Graves/Beck/Cowan)
# ═══════════════════════════════════════════════════════════════════════════════

SPIRAL_LEVELS = {
    "Beige": {
        "meme": "Überleben",
        "uc_relevanz": "Akuter Schub — purer Überlebensmodus",
        "marketing_ansatz": "Sofortige Linderung, Sicherheit, Basis-Bedürfnisse",
    },
    "Purpur": {
        "meme": "Magie, Stammeszugehörigkeit",
        "uc_relevanz": "Community-Suche, 'Warum ich?', Ritualisierung von Symptomen",
        "marketing_ansatz": "Community-Gefühl, 'Du gehörst dazu', geteilte Erfahrungen",
    },
    "Rot": {
        "meme": "Macht, Autonomie, Impulsivität",
        "uc_relevanz": "Frustration, Wut auf den Körper, Kontrollbedürfnis",
        "marketing_ansatz": "Empowerment, 'Nimm dein Leben zurück', direkte Sprache",
    },
    "Blau": {
        "meme": "Ordnung, Regeln, Bedeutung",
        "uc_relevanz": "Suche nach dem 'richtigen' Weg, Arzt-Vertrauen, Protokoll-Befolgung",
        "marketing_ansatz": "Struktur, klare Regeln, Schritt-für-Schritt, Autorität",
    },
    "Orange": {
        "meme": "Leistung, Strategie, Erfolg",
        "uc_relevanz": "Karriere-Sorgen, Effizienz-Fokus, Selbstoptimierung",
        "marketing_ansatz": "Ergebnisse, ROI, System, Methode, messbare Verbesserungen",
    },
    "Grün": {
        "meme": "Gemeinschaft, Gleichheit, Empathie",
        "uc_relevanz": "Peer-Support-Suche, Ablehnung von Mainstream-Medizin",
        "marketing_ansatz": "Community, Peer-Erfahrungen, Holismus, 'together'",
    },
    "Gelb": {
        "meme": "Systemdenken, Integration, Flexibilität",
        "uc_relevanz": "Ganzheitliches Verständnis, widerspruchsfähig",
        "marketing_ansatz": "Komplexität anerkennen, 'es hängt von vielem ab'",
    },
}

# Dominante Spiral-Levels bei CU-Patienten (empirisch geschätzt)
UC_DOMINANT_SPIRAL = {
    "Beige": "5%",   # Nur im akuten Schub
    "Blau": "30%",   # Suche nach Ordnung/Struktur
    "Orange": "35%", # Selbstoptimierer-Mehrheit
    "Grün": "25%",   # Community-orientiert
    "Gelb": "5%",    # Systemdenker
}


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK 4: SCHWARTZ-WERTE (Shalom Schwartz)
# ═══════════════════════════════════════════════════════════════════════════════

SCHWARTZ_VALUES = {
    "Selbstbestimmung": {
        "kern": "Unabhängigkeit, Freiheit, eigene Entscheidungen",
        "uc_relevanz": "SEHR HOCH — CU schränkt Selbstbestimmung massiv ein",
        "messaging": "Du entscheidest wieder selbst, was du isst und wann.",
    },
    "Sicherheit": {
        "kern": "Stabilität, Ordnung, Schutz",
        "uc_relevanz": "SEHR HOCH — Schub = Sicherheitsverlust",
        "messaging": "Weißt du endlich wieder, was als nächstes kommt.",
    },
    "Konformismus": {
        "kern": "Normen befolgen, nicht auffallen",
        "uc_relevanz": "HOCH — Scheu öffentlich darüber zu reden",
        "messaging": "Kein Mut zur Krankheit nötig — nur ein klarer Plan.",
    },
    "Wohlbefinden": {
        "kern": "Genuss, körperliches Wohlbefinden",
        "uc_relevanz": "SEHR HOCH — primärer Wunsch",
        "messaging": "Wieder Tage haben, an denen der Bauch kein Thema ist.",
    },
    "Leistung": {
        "kern": "Persönlicher Erfolg, Kompetenz",
        "uc_relevanz": "MITTEL — Karriere durch CU eingeschränkt",
        "messaging": "Nicht mehr krank sein, um erfolgreich sein zu können.",
    },
    "Universalismus": {
        "kern": "Gerechtigkeit, Naturschutz, Breites Wohlbefinden",
        "uc_relevanz": "MITTEL — holistische Weltanschauung vieler Patienten",
        "messaging": "Ein Ansatz der deinen ganzen Körper — nicht nur Symptome — sieht.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSE & TEXT-OPTIMIERUNG
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PsychProfile:
    """Psychologisches Profil der Zielgruppe."""
    dominant_limbic_types: list[str] = field(default_factory=list)
    primary_awareness_level: int = 2
    dominant_spiral_levels: dict = field(default_factory=dict)
    top_schwartz_values: list[str] = field(default_factory=list)
    core_fears: list[str] = field(default_factory=list)
    core_desires: list[str] = field(default_factory=list)
    messaging_matrix: dict = field(default_factory=dict)


def build_uc_psych_profile() -> PsychProfile:
    """Erstellt das Psycho-Profil der CU-Zielgruppe aus allen Frameworks."""
    return PsychProfile(
        dominant_limbic_types=UC_PRIMARY_LIMBIC,
        primary_awareness_level=2,
        dominant_spiral_levels=UC_DOMINANT_SPIRAL,
        top_schwartz_values=["Selbstbestimmung", "Sicherheit", "Wohlbefinden", "Konformismus"],
        core_fears=[
            "Kontrollverlust über den eigenen Körper",
            "Soziale Isolation / Ausgrenzung durch Krankheit",
            "Berufs- und Lebensqualitätsverlust",
            "Der nächste Schub kommt überraschend",
            "Abhängigkeit von Medikamenten auf Dauer",
        ],
        core_desires=[
            "Einen normalen Alltag führen (essen, reisen, spontan sein)",
            "Kontrolle und Vorhersehbarkeit zurückgewinnen",
            "Verstehen, warum der Körper so reagiert",
            "Nicht dauernd ans Klo denken müssen",
            "Eine Gemeinschaft die wirklich versteht",
        ],
        messaging_matrix={
            "cold_traffic_google": {
                "awareness": 2,
                "limbic": "Gleichgewicht",
                "spiral": "Blau/Orange",
                "hook": "Endlich verstehen warum — und was wirklich hilft.",
                "cta": "Gratis Guide: Die 5 häufigsten Fehler bei CU-Ernährung",
            },
            "cold_traffic_meta": {
                "awareness": 1,
                "limbic": "Hedonist + Harmoniser",
                "spiral": "Grün",
                "hook": "Du vermisst das Gefühl von normalem Essen.",
                "cta": "Erfahre was anderen CU-Betroffenen wirklich geholfen hat.",
            },
            "email_welcome": {
                "awareness": 2,
                "limbic": "Gleichgewicht",
                "spiral": "Blau",
                "hook": "Du hast den ersten Schritt gemacht. Hier kommt Schritt 2.",
                "cta": "Dein kostenloser Guide wartet auf dich.",
            },
            "email_pitch": {
                "awareness": 4,
                "limbic": "Performer + Hedonist",
                "spiral": "Orange",
                "hook": "Was 100+ Betroffene in 4 Wochen umgesetzt haben.",
                "cta": "Colitis Compass jetzt holen (37 €)",
            },
            "sales_page": {
                "awareness": 3,
                "limbic": "Gleichgewicht + Hedonist",
                "spiral": "Orange + Grün",
                "hook": "Nie wieder raten. Endlich ein System das zu deinem Alltag passt.",
                "cta": "Jetzt starten — 37 €, 30 Tage Garantie",
            },
        }
    )


def optimize_text_psychologically(
    text: str,
    target_awareness: int = 2,
    target_limbic: str = "Gleichgewicht",
    dry_run: bool = True
) -> dict:
    """Optimiert einen beliebigen Text nach den Psychologie-Frameworks."""
    if dry_run:
        return {"optimized": "[DRY-RUN] Text nicht optimiert.", "original": text}

    from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART  # noqa
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    awareness = AWARENESS_LEVELS.get(target_awareness, AWARENESS_LEVELS[2])
    limbic = LIMBIC_TYPES.get(target_limbic, LIMBIC_TYPES["Gleichgewicht"])

    prompt = f"""Du bist ein Experte für psychologisches Marketing, insbesondere:
- Limbic Map (Häusel)
- Awareness-Stufen nach Eugene Schwartz
- Spiral Dynamics (Beck/Cowan)
- Grundwerte nach Shalom Schwartz

AUFGABE: Optimiere folgenden Text psychologisch für die CU-Zielgruppe.

ZIEL-AWARENESS-STUFE: {target_awareness} — "{awareness['name']}"
  Wer ist das: {awareness['wer_ist_das']}
  Richtige Botschaft: {awareness['richtige_botschaft']}
  Falsche Botschaft: {awareness['falsche_botschaft']}

ZIEL-LIMBIC-TYP: {target_limbic}
  Kern-Motiv: {limbic['core_motive']}
  Kern-Angst: {limbic['fear']}
  CU-Relevanz: {limbic['uc_relevanz']}
  Messaging-Hook: {limbic['messaging_hook']}

DOMINANT SCHWARTZ-WERTE bei CU: Selbstbestimmung, Sicherheit, Wohlbefinden

ORIGINAL-TEXT:
---
{text}
---

Liefere:
1. OPTIMIERTER TEXT (direkt ersetzbar)
2. BEGRÜNDUNG (max. 3 Punkte — was und warum geändert)
3. PSYCHO-SCORE (0-100, wie gut trifft der Originaltext die Zielgruppe)

Schreibe auf Deutsch, authentisch, kein generisches Marketing-Deutsch."""

    resp = client.messages.create(
        model=CLAUDE_MODEL_SMART,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "original": text,
        "optimized_response": resp.content[0].text,
        "target_awareness": target_awareness,
        "target_limbic": target_limbic,
    }


# ─── Report ausgeben ──────────────────────────────────────────────────────────

def print_psych_profile(profile: PsychProfile):
    print("""
╔══════════════════════════════════════════════════════════════╗
║  PSYCHOLOGY EXPERT — CU-Zielgruppen-Profil
╚══════════════════════════════════════════════════════════════╝

── LIMBIC MAP ────────────────────────────────────────────────""")
    for lt in profile.dominant_limbic_types:
        data = LIMBIC_TYPES[lt]
        print(f"  [{lt}] → {data['core_motive']}")
        print(f"    CU-Hook: \"{data['messaging_hook']}\"")

    print("\n── AWARENESS-STUFEN (Schwartz) ──────────────────────────────")
    print(f"  Cold Traffic (Google): Stufe 2 — Problem Aware")
    print(f"  Cold Traffic (Meta):   Stufe 1-2 — Un/Problem Aware")
    print(f"  Email-Subscriber:      Stufe 3-4 — Solution/Product Aware")
    print(f"  Käufer Einstieg:       Stufe 5 — Most Aware")

    print("\n── SPIRAL DYNAMICS ──────────────────────────────────────────")
    for level, pct in profile.dominant_spiral_levels.items():
        data = SPIRAL_LEVELS.get(level, {})
        print(f"  [{level:6} {pct:4}] {data.get('meme', '')} → {data.get('marketing_ansatz', '')}")

    print("\n── CORE FEARS (Kauftreiber) ──────────────────────────────────")
    for f in profile.core_fears:
        print(f"  ✗  {f}")

    print("\n── CORE DESIRES (Kaufversprechen) ───────────────────────────")
    for d in profile.core_desires:
        print(f"  ✓  {d}")

    print("\n── MESSAGING-MATRIX (Kanal → Hook) ──────────────────────────")
    for channel, data in profile.messaging_matrix.items():
        print(f"\n  [{channel.upper()}]")
        print(f"    Awareness: Stufe {data['awareness']} | Limbic: {data['limbic']}")
        print(f"    Hook: \"{data['hook']}\"")
        print(f"    CTA:  \"{data['cta']}\"")
    print()


# ─── Haupt-Einstiegspunkt ─────────────────────────────────────────────────────

def run(text_to_optimize: Optional[str] = None, dry_run: bool = True):
    """Psychology Expert Haupt-Funktion."""
    print("\n[PSYCHOLOGY EXPERT] Analysiere CU-Zielgruppe...")

    profile = build_uc_psych_profile()
    print_psych_profile(profile)

    # Profil in knowledge-Datei speichern
    output_path = Path(__file__).parent.parent / "knowledge" / "psych_profile_uc.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "dominant_limbic": profile.dominant_limbic_types,
            "primary_awareness": profile.primary_awareness_level,
            "spiral_levels": profile.dominant_spiral_levels,
            "schwartz_values": profile.top_schwartz_values,
            "core_fears": profile.core_fears,
            "core_desires": profile.core_desires,
            "messaging_matrix": profile.messaging_matrix,
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"Psycho-Profil gespeichert: {output_path}")

    # Optional: Text optimieren
    if text_to_optimize:
        print(f"\n[PSYCHOLOGY EXPERT] Optimiere Text...")
        result = optimize_text_psychologically(
            text_to_optimize,
            target_awareness=2,
            target_limbic="Gleichgewicht",
            dry_run=dry_run
        )
        print("\n── TEXT-OPTIMIERUNG ─────────────────────────────────────────")
        print(result.get("optimized_response", result.get("optimized", "")))

    return profile
