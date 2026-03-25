"""
UC Business — Brand Agent
===========================
Entwickelt eine resonante Marke für die CU-Zielgruppe.
Arbeitet eng mit dem Psychology Expert zusammen.

Aufgaben:
  1. Brand Identity entwickeln (Name, Claim, Tonalität, Visual Direction)
  2. Brand Voice Guidelines generieren
  3. Messaging-Hierarchie erstellen (für welche Awareness-Stufe welche Botschaft)
  4. Bestehende Assets bewerten und Optimierungsempfehlungen geben
  5. Brand-Konsistenz über alle Touchpoints sichern

Verwendung:
  python run.py --brand             → Vollständiges Brand-Briefing generieren
  python run.py --brand --audit     → Bestehende Assets (URL/Text) auditieren
"""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# ─── Zielgruppen-Segmente ──────────────────────────────────────────────────────

AUDIENCE_SEGMENTS = {
    "akut_betroffen": {
        "beschreibung": "Person im aktiven Schub oder kurz danach",
        "emotionaler_zustand": "Angst, Erschöpfung, Kontrollverlust, Hoffnungslosigkeit",
        "primäres_bedürfnis": "Sofortige Linderung, Kontrolle zurückgewinnen",
        "sprache": "Direkt, empathisch, konkreter Nutzen, keine Versprechungen",
        "limbic_typ": "Gleichgewicht/Sicherheit",
        "awareness_stufe": 2,  # Problem Aware
    },
    "remission_suchend": {
        "beschreibung": "Person zwischen Schüben, sucht nachhaltige Lösung",
        "emotionaler_zustand": "Vorsichtige Hoffnung, Frustration über Rückfälle",
        "primäres_bedürfnis": "Stabilität, Vorhersehbarkeit, Normalität",
        "sprache": "Strukturiert, evidenzbasiert, Langzeit-Fokus",
        "limbic_typ": "Balance/Harmonie",
        "awareness_stufe": 3,  # Solution Aware
    },
    "neudiagnostiziert": {
        "beschreibung": "Frisch diagnostiziert (0-12 Monate), overwhelmed",
        "emotionaler_zustand": "Überwältigung, Informations-Chaos, Identitätskrise",
        "primäres_bedürfnis": "Orientierung, Verständnis, Community",
        "sprache": "Beruhigend, strukturiert, Schritt-für-Schritt",
        "limbic_typ": "Gleichgewicht/Fürsorge",
        "awareness_stufe": 2,
    },
    "selbstoptimierer": {
        "beschreibung": "Schon länger krank, experimentierfreudig, gut informiert",
        "emotionaler_zustand": "Neugier, Selbstwirksamkeit, Kontroll-Fokus",
        "primäres_bedürfnis": "Neue Erkenntnisse, Verfeinerung der eigenen Strategie",
        "sprache": "Detailliert, wissenschaftlich fundiert, Peer-Kommunikation",
        "limbic_typ": "Stimulanz/Dominanz",
        "awareness_stufe": 4,  # Product Aware
    },
}

# ─── Brand-Frameworks ─────────────────────────────────────────────────────────

BRAND_ARCHETYPES = {
    "Begleiter": "Geht den Weg mit dir — ohne Urteile, ohne Versprechen",
    "Wegweiser": "Zeigt den Weg — klar, strukturiert, orientierend",
    "Entdecker": "Findet neue Wege — Forschung, Neugier, Optimierung",
    "Beschützer": "Steht auf deiner Seite — gegen Einschränkungen, für Lebensqualität",
}

FORBIDDEN_BRAND_ELEMENTS = [
    "Heilungsversprechen",
    "Medizinische Autorität ohne Credentials",
    "Angst als primärer Treiber (manipulativ)",
    "Generische Wellness-Ästhetik (zu ähnlich zu Yoga/Mindfulness-Marken)",
    "Infantilisierende Sprache",
    "Übertriebene Positivität (toxic positivity)",
]


# ─── Datenstrukturen ──────────────────────────────────────────────────────────

@dataclass
class BrandIdentity:
    brand_name: str = ""
    claim: str = ""
    sub_claim: str = ""
    archetype: str = ""
    brand_promise: str = ""
    tone_of_voice: list[str] = field(default_factory=list)
    forbidden_tone: list[str] = field(default_factory=list)
    color_direction: str = ""
    typography_direction: str = ""
    imagery_direction: str = ""
    messaging_by_segment: dict = field(default_factory=dict)
    brand_story: str = ""


@dataclass
class BrandAuditResult:
    url: str = ""
    overall_score: int = 0      # 0-100
    strengths: list[str] = field(default_factory=list)
    critical_issues: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    limbic_alignment: str = ""
    awareness_match: str = ""
    gender_inclusivity: str = ""
    ai_rewrite_suggestions: dict = field(default_factory=dict)


# ─── Brand Identity generieren ────────────────────────────────────────────────

def generate_brand_identity(dry_run: bool = True) -> BrandIdentity:
    """Entwickelt eine vollständige Brand Identity via Claude API."""
    if dry_run:
        logger.info("[DRY-RUN] Brand Identity nicht generiert.")
        return _get_default_identity()

    from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART  # noqa

    knowledge_path = Path(__file__).parent.parent / "knowledge"
    psychology_context = ""
    if (knowledge_path / "psychology_framework.md").exists():
        psychology_context = (knowledge_path / "psychology_framework.md").read_text()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Du bist ein erstklassiger Brand-Stratege für Gesundheitsmarken im deutschsprachigen Markt.

AUFGABE: Entwickle eine vollständige Brand Identity für ein anonymes Online-Business rund um 
Colitis Ulcerosa (CU) im DACH-Markt.

RAHMENBEDINGUNGEN:
- Kein Gesicht, kein persönlicher Coach — anonyme Marke
- Produkte: PDF-Guide (€37) + Video-Kurs (€247)
- Zielmarkt: DACH (DE/AT/CH), Deutsch
- CU betrifft Männer und Frauen gleichermaßen (je 50%)
- Kein Heilsversprechen, keine medizinischen Claims
- Konkurrenz: Generische Wellness-Marken ohne CU-Spezialisierung

AKTUELLE WEBSITE (kritisch bewertet):
- lebenmitcolitis.de
- Problem: Zu feminin (Yoga-Ästhetik, Lachs/Beige, Script-Fonts)
- Problem: "7-Tage-Plan" trivialiert chronische Erkrankung
- Problem: "Mein Name ist [egal]" — kein Vertrauen, keine Story
- Stärke: Pain-Point-Struktur ansatzweise vorhanden

PSYCHOLOGIE-KONTEXT:
{psychology_context[:2000] if psychology_context else "Nicht verfügbar — nutze allgemeines Wissen"}

ZIELGRUPPEN-SEGMENTE:
1. Akut Betroffen (Schub): Angst, Kontrollverlust → Sicherheit/Gleichgewicht
2. Remission-Suchend: Vorsichtige Hoffnung → Balance/Stabilität  
3. Neu Diagnostiziert: Overwhelm → Orientierung/Community
4. Selbstoptimierer: Neugier, Kontrolle → Stimulanz/Dominanz

Liefere:
1. Markenname (2 Varianten, auf Deutsch, ohne "Colitis" im Namen — warum: Stigma)
2. Claim (max. 8 Wörter)
3. Marken-Archetype (eine der 4 Kategorien + Begründung)
4. Tonalität (5 Adjektive + 5 verbotene Töne)
5. Visuelle Richtung (Farbpalette: inklusiv, nicht-klinisch, nicht-feminin-dominant)
6. Kern-Botschaft für jedes Segment (1 Satz je Segment)
7. Anonym bleiben: Wie baut man Vertrauen ohne Gesicht? (3 konkrete Maßnahmen)

Format: Strukturiert, umsetzbar, kein Marketing-Bullshit."""

    resp = client.messages.create(
        model=CLAUDE_MODEL_SMART,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Ergebnis speichern
    output_path = Path(__file__).parent.parent / "knowledge" / "brand_identity_generated.md"
    output_path.write_text(f"# Brand Identity (generiert {__import__('datetime').datetime.now()})\n\n{resp.content[0].text}")
    logger.info(f"Brand Identity gespeichert: {output_path}")

    identity = _get_default_identity()
    identity.brand_story = resp.content[0].text
    return identity


def _get_default_identity() -> BrandIdentity:
    """Fallback-Identity basierend auf manueller Analyse."""
    return BrandIdentity(
        brand_name="Darm in Ruhe",  # Vorschlag — zu validieren
        claim="Wenn der Bauch zur Ruhe kommt, kommt das Leben zurück.",
        archetype="Begleiter",
        brand_promise="Wir begleiten dich auf dem Weg zu mehr Stabilität — ohne Versprechungen, ohne Urteile.",
        tone_of_voice=["empathisch", "direkt", "sachkundig", "ermutigend", "respektvoll"],
        forbidden_tone=["alarmistisch", "mitleidig", "klinisch-kalt", "toxic-positiv", "bevormundend"],
        color_direction=(
            "Tiefes Blaugrün (Vertrauen, Tiefe) + warmes Sand (Wärme ohne feminin) "
            "+ helles Off-White. KEIN Rosa/Lachs/Beige-dominant."
        ),
        imagery_direction=(
            "Menschen in Bewegung (draußen, aktiv) — Natur, Küche, Alltag. "
            "Keine Yoga-Posen, keine isolierten Körperteile, keine Krankenhausbilder. "
            "Geschlechterausgewogen."
        ),
        messaging_by_segment={
            "akut_betroffen": "Endlich einen klaren Plan haben, wenn es wieder losgeht.",
            "remission_suchend": "Nicht nur den nächsten Schub vermeiden — ein Leben gestalten.",
            "neudiagnostiziert": "Du bist nicht allein — und es gibt Dinge, die du jetzt tun kannst.",
            "selbstoptimierer": "Was funktioniert wirklich? Evidenz statt Mythen.",
        }
    )


# ─── Brand Audit ──────────────────────────────────────────────────────────────

def audit_website(url: str, dry_run: bool = True) -> BrandAuditResult:
    """Auditiert eine bestehende Website gegen die Brand-Strategie."""
    result = BrandAuditResult(url=url)

    if url == "https://lebenmitcolitis.de/":
        # Vorab-Analyse basierend auf Screenshot
        result.overall_score = 42
        result.strengths = [
            "Pain-Point-Sektion vorhanden (strukturell richtig)",
            "Dream-Outcome-Sektion ('Stell dir vor...') — guter Ansatz",
            "Anonymes Konzept strategisch klug",
            "Produkt-Name 'Colitis Compass' hat Substanz",
        ]
        result.critical_issues = [
            "SHOWSTOPPER: Template-Text im Footer ('find your place at Java')",
            "SHOWSTOPPER: 'Your Logo' Platzhalter — kein Branding",
            "'Mein Name ist [egal]' — Vertrauen-Vakuum ohne Story",
            "Design-Ästhetik 95% feminin — schließt 50% Zielgruppe aus",
            "'7-Tage Plan' trivialiert chronische Autoimmunerkrankung",
            "Awareness-Mismatch: Seite springt zu schnell zu Solution-Pitch",
            "Sozial-Beweis '100+' zu schwach und zu vage",
            "Kein Proof-of-Mechanism erkennbar",
        ]
        result.improvements = [
            "Footer-Template-Text sofort entfernen",
            "Farb-Palette auf geschlechtsneutral umstellen (Blaugrün + Sand statt Lachs/Beige)",
            "'7-Tage Plan' umbenennen in '4-Wochen-Framework' oder ähnliches",
            "Brand Story entwickeln: Anonyme Herausgeber-Perspektive ('Ein Team aus Betroffenen')",
            "Awareness-Level-Mapping: Cold-Traffic-Version der Seite für Stufe 1-2 bauen",
            "Sozial-Beweis konkretisieren: Spezifische Aussagen statt generische Zahlen",
            "Proof-of-Mechanism ergänzen: Warum funktioniert der Ansatz?",
        ]
        result.limbic_alignment = (
            "Aktuell: Balance/Harmonie (Wellness-Ästhetik). "
            "Ziel: Gleichgewicht/Sicherheit (für Schub-Patienten) + Balance (für Remission). "
            "Fehlt: Stimulanz-Elemente für Selbstoptimierer-Segment."
        )
        result.awareness_match = (
            "Problem: Seite ist für Awareness-Stufe 3-4 optimiert. "
            "Cold Traffic aus Google Ads ist meist Stufe 1-2. "
            "Lösung: Landing Page für Stufe 2 bauen (Problem-Aware Hook) — "
            "Salespage erst NACH dem Opt-in zeigen."
        )
        result.gender_inclusivity = (
            "KRITISCH: Farbpalette, Bildsprache und Typographie schließen Männer praktisch aus. "
            "Lösung: Neutral-inclusive Design + männliche Testimonials ergänzen."
        )

    if not dry_run:
        _generate_rewrite_suggestions(result)

    return result


def _generate_rewrite_suggestions(result: BrandAuditResult):
    """Claude generiert konkrete Rewrite-Vorschläge für kritische Elemente."""
    from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART  # noqa
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""Schreibe für lebenmitcolitis.de folgende Elemente neu (auf Deutsch):

1. HEADLINE (aktuell: "Ein leichteres Leben mit Colitis Ulcerosa – Schritt für Schritt zu mehr Wohlbefinden im Alltag")
   → Neu: Awareness-Stufe 2, inklusiv (nicht-feminin), spezifisch für CU

2. SOCIAL PROOF HEADLINE (aktuell: "100+ Menschen leben bereits mit mehr Ruhe im Bauch")
   → Neu: Spezifischer, glaubwürdiger, emotionaler

3. BIO-SEKTION (aktuell: "Mein Name ist [egal]")
   → Neu: Anonymes Team/Community-Konzept das Vertrauen aufbaut

Liefere je 2 Varianten. Kurz, präzise, conversion-fokussiert."""

        resp = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        result.ai_rewrite_suggestions = {"rewrite": resp.content[0].text}
    except Exception as e:
        logger.error(f"Rewrite-Generierung fehlgeschlagen: {e}")


# ─── Report ausgeben ──────────────────────────────────────────────────────────

def print_brand_audit(result: BrandAuditResult):
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  BRAND AUDIT — {result.url[:45]:<45} ║
╚══════════════════════════════════════════════════════════════╝

  Gesamt-Score: {result.overall_score}/100  {"✓ Gut" if result.overall_score >= 70 else "⚠ Verbesserungsbedarf" if result.overall_score >= 50 else "✗ Kritisch"}

── STÄRKEN ───────────────────────────────────────────────────""")
    for s in result.strengths:
        print(f"  ✓  {s}")

    print("\n── KRITISCHE PROBLEME ────────────────────────────────────────")
    for i in result.critical_issues:
        print(f"  ✗  {i}")

    print("\n── VERBESSERUNGEN ────────────────────────────────────────────")
    for i, imp in enumerate(result.improvements, 1):
        print(f"  {i}. {imp}")

    print(f"""
── PSYCHOLOGIE ───────────────────────────────────────────────
  Limbic:      {result.limbic_alignment}
  Awareness:   {result.awareness_match}
  Inklusivität: {result.gender_inclusivity}""")

    if result.ai_rewrite_suggestions:
        print("\n── AI-REWRITE-VORSCHLÄGE ─────────────────────────────────────")
        print(result.ai_rewrite_suggestions.get("rewrite", ""))
    print()


# ─── Haupt-Einstiegspunkt ─────────────────────────────────────────────────────

def run(audit_url: Optional[str] = None, dry_run: bool = True):
    """Brand Agent Haupt-Funktion."""
    print("\n[BRAND AGENT] Starte Brand-Analyse...")

    # 1. Brand Identity
    identity = generate_brand_identity(dry_run=dry_run)
    print(f"\n[BRAND] Archetype: {identity.archetype}")
    print(f"[BRAND] Claim: {identity.claim}")
    print(f"[BRAND] Tonalität: {', '.join(identity.tone_of_voice)}")

    # 2. Audit
    target_url = audit_url or "https://lebenmitcolitis.de/"
    audit = audit_website(target_url, dry_run=dry_run)
    print_brand_audit(audit)

    # Ergebnis speichern
    output_path = Path(__file__).parent.parent / "knowledge" / "brand_audit_latest.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "identity": identity.__dict__,
            "audit": {
                "url": audit.url,
                "score": audit.overall_score,
                "issues": audit.critical_issues,
                "improvements": audit.improvements,
            }
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"Brand-Ergebnisse gespeichert: {output_path}")
    return identity, audit
