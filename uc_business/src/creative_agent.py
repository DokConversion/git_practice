"""
Creative Agent — Content & Copy Generator
==========================================
Generiert alle Marketing-Texte via Claude API:
- Google Ads RSA (Headlines + Descriptions)
- Meta Ad Copy (Primary Text, mehrere Varianten)
- Landing Page Texte (Headlines, Benefits, CTAs)
- Email Betreffzeilen (A/B Varianten)

Nutzt Insights aus dem Groups Intel Agent als Basis.
"""
import json
import re
import sys
import os
import logging
from typing import Optional

import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART, BRAND_NAME, WEBSITE_DOMAIN, \
    PRICE_ENTRY_PRODUCT, PRICE_UPSELL_PRODUCT, DRY_RUN
from db import init_db, insert_creative, insert_campaign, get_top_insights
from groups_intel_agent import load_saved_insights

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Verbotene Begriffe (medizinische Versprechen / Werberichtlinien)
FORBIDDEN_TERMS = [
    "heilt", "kuriert", "medizinisch geprüft", "klinisch bewiesen",
    "garantiert", "100% wirksam", "FDA", "CE-zertifiziert",
    "Heilmittel", "Therapie ersetzt", "statt Medikamente",
]

COMPLIANCE_REPLACEMENTS = {
    "heilt": "kann unterstützen",
    "kuriert": "hilft bei",
    "garantiert": "nach Erfahrung vieler Betroffener",
    "100%": "nachhaltig",
}


def compliance_check(text: str) -> tuple[str, list[str]]:
    """Prüft Text auf verbotene Claims und ersetzt diese."""
    warnings = []
    for term in FORBIDDEN_TERMS:
        if term.lower() in text.lower():
            warnings.append(f"Verbotener Begriff: '{term}'")
            replacement = COMPLIANCE_REPLACEMENTS.get(term, "")
            if replacement:
                text = re.sub(re.escape(term), replacement, text, flags=re.IGNORECASE)
    return text, warnings


def load_insights_context() -> str:
    """Lädt gespeicherte Insights als Kontext für Claude."""
    data = load_saved_insights()
    if not data or "summary" not in data:
        return ""

    summary = data["summary"]
    context_parts = []

    if summary.get("top_pain_points"):
        context_parts.append("TOP PAIN POINTS DER ZIELGRUPPE:\n" +
                             "\n".join(f"- {p}" for p in summary["top_pain_points"][:5]))

    if summary.get("top_keywords"):
        context_parts.append("ECHTE SPRACHE DER BETROFFENEN:\n" +
                             ", ".join(summary["top_keywords"][:10]))

    return "\n\n".join(context_parts)


# ─── Google Ads RSA ───────────────────────────────────────────────────────────

def generate_google_rsa(campaign_angle: str, insights_context: str = "") -> dict:
    """
    Generiert Google RSA (Responsive Search Ad):
    - 15 Headlines (max. 30 Zeichen)
    - 4 Descriptions (max. 90 Zeichen)
    """
    prompt = f"""Du bist ein erfahrener Google Ads Texter für Gesundheitsprodukte im DACH-Markt.

Erstelle eine Responsive Search Ad (RSA) für folgendes Produkt:

PRODUKT: "{BRAND_NAME}" — Digitale Guides & Programme für Colitis Ulcerosa Betroffene
KAMPAGNEN-WINKEL: {campaign_angle}
PREIS EINSTIEG: €{PRICE_ENTRY_PRODUCT:.0f}
ZIEL: Kostenloser Guide als Lead-Magnet → Weiterleitung zur Hauptseite

{f'ZIELGRUPPEN-INSIGHTS:{chr(10)}{insights_context}' if insights_context else ''}

REGELN:
- Headlines: MAX 30 Zeichen (STRENG einhalten!)
- Descriptions: MAX 90 Zeichen
- Keine Heilsversprechen
- Empathische, verständnisvolle Sprache
- Auf Deutsch (DACH-Markt)
- Keyword "Colitis Ulcerosa" mindestens in 3 Headlines

Antworte NUR mit validem JSON:
{{
    "headlines": [
        "Headline 1 (max 30 Zeichen)",
        "... (15 Headlines gesamt)"
    ],
    "descriptions": [
        "Description 1 (max 90 Zeichen)",
        "... (4 Descriptions gesamt)"
    ]
}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            # Compliance-Check auf alle Headlines und Descriptions
            cleaned_headlines = []
            all_warnings = []
            for h in data.get("headlines", [])[:15]:
                h_clean, warnings = compliance_check(h)
                cleaned_headlines.append(h_clean[:30])  # Zeichenlimit erzwingen
                all_warnings.extend(warnings)
            cleaned_descs = []
            for d in data.get("descriptions", [])[:4]:
                d_clean, warnings = compliance_check(d)
                cleaned_descs.append(d_clean[:90])
                all_warnings.extend(warnings)

            if all_warnings:
                log.warning(f"Compliance-Warnungen: {all_warnings}")

            return {
                "headlines": cleaned_headlines,
                "descriptions": cleaned_descs,
                "campaign_angle": campaign_angle
            }
    except Exception as e:
        log.error(f"Fehler bei RSA-Generierung: {e}")

    return {"headlines": [], "descriptions": [], "campaign_angle": campaign_angle}


def generate_all_google_rsa(dry_run: bool = DRY_RUN) -> list[dict]:
    """Generiert RSAs für alle 3 Kampagnen-Winkel."""
    insights_context = load_insights_context()

    angles = [
        "Ernährung & Schub-Prävention (Was essen bei CU?)",
        "Remission & Symptom-Linderung (Beschwerdefrei trotz CU)",
        "Psyche & Stressbewältigung (CU und mentale Gesundheit)"
    ]

    results = []
    for angle in angles:
        log.info(f"Generiere RSA für Winkel: {angle}")
        rsa = generate_google_rsa(angle, insights_context)
        results.append(rsa)

        if not dry_run and rsa["headlines"]:
            campaign_id = insert_campaign(
                platform="google",
                name=f"UC | {angle[:30]}",
                campaign_type="search",
                budget_daily=7.0,  # ~21€ Tagesbudget / 3 Kampagnen
                target_cpa=18.0
            )
            insert_creative(
                campaign_id=campaign_id,
                platform="google",
                format="rsa",
                headline_1=rsa["headlines"][0] if rsa["headlines"] else "",
                headline_2=rsa["headlines"][1] if len(rsa["headlines"]) > 1 else "",
                headline_3=rsa["headlines"][2] if len(rsa["headlines"]) > 2 else "",
                body_text="\n".join(rsa["descriptions"]),
                cta="Kostenlosen Guide sichern"
            )

        # Debug-Ausgabe
        print(f"\n[Google RSA] Winkel: {angle}")
        print(f"  Headlines ({len(rsa['headlines'])}): {rsa['headlines'][:3]}...")
        print(f"  Descriptions: {rsa['descriptions'][:1]}...")

    return results


# ─── Meta Ad Copy ─────────────────────────────────────────────────────────────

def generate_meta_ad_copy(variant: int, insights_context: str = "") -> dict:
    """
    Generiert Meta/Facebook Ad Copy (3 Varianten für A/B-Test):
    - Hook (erste Zeile)
    - Primary Text (3-5 Sätze)
    - Headline (unter dem Bild)
    - CTA
    """
    hooks_inspiration = {
        1: "Problem-Agitation (Beschreibe den Schmerz)",
        2: "Neugier-Hook (Überraschendes Wissen)",
        3: "Sozial-Beweis (Erfahrungsbericht-Stil)"
    }

    prompt = f"""Du bist ein Meta Ads Texter für Gesundheitsprodukte im DACH-Markt.

Erstelle eine Facebook/Instagram Ad (Variante {variant}) für:

PRODUKT: "{BRAND_NAME}" — Kostenloser "UC Starter-Guide" (Lead-Magnet)
ZIEL: E-Mail Adresse sammeln (Lead Generation)
STIL: {hooks_inspiration.get(variant, 'Empathisch & direkt')}

{f'ZIELGRUPPEN-INSIGHTS:{chr(10)}{insights_context}' if insights_context else ''}

REGELN:
- Primary Text: 3-5 Sätze, Hook in erster Zeile
- Empathisch, peer-to-peer (nicht werblich)
- Keine Heilsversprechen
- Klarer Nutzen des kostenlosen Guides
- Auf Deutsch, informell (Du)

Antworte NUR mit JSON:
{{
    "hook": "Erste Zeile (aufmerksamkeitsstark, max 80 Zeichen)",
    "primary_text": "Vollständiger Ad-Text (3-5 Sätze)",
    "headline": "Headline unter dem Bild (max 40 Zeichen)",
    "cta_button": "SIGN_UP oder LEARN_MORE",
    "image_concept": "Beschreibe das ideale Bild (kein Gesicht nötig)"
}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            # Compliance-Check
            for key in ["primary_text", "headline", "hook"]:
                if key in data:
                    data[key], warnings = compliance_check(data[key])
                    if warnings:
                        log.warning(f"Meta Ad Compliance: {warnings}")
            return data
    except Exception as e:
        log.error(f"Fehler bei Meta Ad Generierung: {e}")

    return {"hook": "", "primary_text": "", "headline": "", "cta_button": "SIGN_UP"}


def generate_all_meta_ads(dry_run: bool = DRY_RUN) -> list[dict]:
    """Generiert 3 Meta Ad Varianten für A/B-Test."""
    insights_context = load_insights_context()
    results = []

    for variant in [1, 2, 3]:
        log.info(f"Generiere Meta Ad Variante {variant}/3...")
        ad = generate_meta_ad_copy(variant, insights_context)
        ad["variant"] = variant
        results.append(ad)

        if not dry_run and ad.get("primary_text"):
            campaign_id = insert_campaign(
                platform="meta",
                name=f"UC | Lead Gen | Variante {variant}",
                campaign_type="lead_gen",
                budget_daily=5.0,
                target_cpa=2.5
            )
            insert_creative(
                campaign_id=campaign_id,
                platform="meta",
                format="image",
                headline_1=ad.get("hook", ""),
                body_text=ad.get("primary_text", ""),
                cta=ad.get("cta_button", "SIGN_UP")
            )

        print(f"\n[Meta Ad] Variante {variant}")
        print(f"  Hook: {ad.get('hook', '—')}")
        print(f"  Headline: {ad.get('headline', '—')}")
        print(f"  Bild-Konzept: {ad.get('image_concept', '—')}")

    return results


# ─── Landing Page Texte ───────────────────────────────────────────────────────

def generate_landing_page_copy(page_type: str) -> dict:
    """Generiert alle Texte für eine Landingpage."""
    page_specs = {
        "optin": {
            "goal": "E-Mail Adresse sammeln (Lead-Magnet: Kostenloser UC Starter-Guide)",
            "elements": "Headline, Subheadline, 3 Bullet-Points (Nutzen), CTA-Button-Text, Trust-Signal"
        },
        "sales": {
            "goal": f"Verkauf 'UC Ernährungs-Kompass' PDF für €{PRICE_ENTRY_PRODUCT:.0f}",
            "elements": "Headline, Hook, Problem-Agitation, Lösung, 5 Benefits, Preis-Ankündigung, CTA, FAQ (3 Fragen)"
        },
        "upsell": {
            "goal": f"Upsell 'UC Selbsthilfe-System' Video-Kurs für €{PRICE_UPSELL_PRODUCT:.0f}",
            "elements": "Gratulation, Upsell-Headline, Was sie verpassen, 3 Module-Übersicht, Sonderangebot-CTA"
        }
    }

    spec = page_specs.get(page_type, page_specs["optin"])
    insights_context = load_insights_context()

    prompt = f"""Du bist ein Conversion-Texter für Gesundheitsprodukte (DACH-Markt).

Erstelle alle Texte für diese Landing Page:

TYP: {page_type.upper()}
ZIEL: {spec['goal']}
ELEMENTE: {spec['elements']}
MARKE: {BRAND_NAME}

{f'ZIELGRUPPEN-INSIGHTS:{chr(10)}{insights_context}' if insights_context else ''}

REGELN:
- Keine falschen Heilsversprechen
- Empathisch, verständnisvoll
- Anonym (kein persönliches Gesicht/Name des Betreibers)
- Auf Deutsch (DACH)
- Conversion-optimiert

Antworte NUR mit JSON mit allen angeforderten Elementen."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
    except Exception as e:
        log.error(f"Fehler bei LP Copy Generierung ({page_type}): {e}")

    return {}


# ─── Email Betreffzeilen ─────────────────────────────────────────────────────

def generate_email_subjects(email_step: int, context: str = "") -> list[str]:
    """Generiert 3 A/B-Varianten für Email-Betreffzeilen."""
    prompt = f"""Erstelle 3 verschiedene Email-Betreffzeilen für Schritt {email_step} einer Welcome-Sequenz.

ZIELGRUPPE: Colitis Ulcerosa Betroffene (haben sich für kostenlosen Guide eingetragen)
SCHRITT: {email_step}

{f'KONTEXT: {context}' if context else ''}

Regeln:
- Max. 50 Zeichen
- Neugier weckend oder problemfokussiert
- Keine Spam-Trigger-Wörter
- Auf Deutsch, informell

Antworte NUR mit JSON:
{{"subjects": ["Betreff 1", "Betreff 2", "Betreff 3"]}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("subjects", [])
    except Exception as e:
        log.error(f"Fehler bei Subject-Generierung: {e}")
    return []


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

def run(dry_run: bool = DRY_RUN) -> dict:
    """Generiert alle Creatives: Google RSA, Meta Ads, Landing Page Texte."""
    log.info("=" * 60)
    log.info("UC CREATIVE AGENT — Start")
    log.info(f"Modus: {'DRY-RUN' if dry_run else 'LIVE (speichert in DB)'}")
    log.info("=" * 60)

    results = {}

    # 1. Google RSA
    log.info("\n[1/3] Google Ads RSA generieren...")
    results["google_rsa"] = generate_all_google_rsa(dry_run)

    # 2. Meta Ads
    log.info("\n[2/3] Meta Ad Copy generieren...")
    results["meta_ads"] = generate_all_meta_ads(dry_run)

    # 3. Landing Page Texte
    log.info("\n[3/3] Landing Page Texte generieren...")
    results["landing_pages"] = {}
    for page_type in ["optin", "sales", "upsell"]:
        log.info(f"  → {page_type}")
        copy = generate_landing_page_copy(page_type)
        results["landing_pages"][page_type] = copy

    # Output speichern
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "creatives.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"\nCreatives gespeichert: {output_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Creative Agent")
    parser.add_argument("--live", action="store_true", help="In DB speichern")
    parser.add_argument("--google-only", action="store_true")
    parser.add_argument("--meta-only", action="store_true")
    parser.add_argument("--lp-only", action="store_true")
    args = parser.parse_args()

    init_db()
    if args.google_only:
        generate_all_google_rsa(dry_run=not args.live)
    elif args.meta_only:
        generate_all_meta_ads(dry_run=not args.live)
    elif args.lp_only:
        for pt in ["optin", "sales", "upsell"]:
            print(f"\n=== {pt.upper()} ===")
            print(json.dumps(generate_landing_page_copy(pt), indent=2, ensure_ascii=False))
    else:
        run(dry_run=not args.live)
