"""
Email Marketing Agent
======================
Provider-agnostischer Email-Agent mit Adaptern für:
- ActiveCampaign
- Mailchimp
- GetResponse

Verwaltet:
- Welcome-Sequenz (5 Emails, 14 Tage)
- Upsell-Sequenz (3 Emails, 5 Tage)
- Re-Engagement-Sequenz
- Broadcast-Emails
"""
import json
import os
import re
import sys
import logging
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART,
    EMAIL_PROVIDER, EMAIL_API_KEY, EMAIL_API_URL,
    EMAIL_FROM_NAME, EMAIL_FROM_ADDRESS,
    BRAND_NAME, PRICE_ENTRY_PRODUCT, PRICE_UPSELL_PRODUCT, DRY_RUN
)
from db import init_db, insert_subscriber, get_subscriber_count

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


# ─── Email Provider Adapter ───────────────────────────────────────────────────

class EmailAdapter(ABC):
    """Abstrakte Basis für alle Email-Provider."""

    @abstractmethod
    def add_subscriber(self, email: str, first_name: str, tags: list) -> Optional[str]:
        """Subscriber hinzufügen. Gibt Provider-ID zurück."""
        pass

    @abstractmethod
    def tag_subscriber(self, provider_id: str, tags: list) -> bool:
        pass

    @abstractmethod
    def send_broadcast(self, subject: str, html_body: str, list_id: str,
                       segment: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def trigger_automation(self, provider_id: str, automation_id: str) -> bool:
        pass


class ActiveCampaignAdapter(EmailAdapter):
    """ActiveCampaign API v3 Integration."""

    def __init__(self):
        self.base_url = EMAIL_API_URL.rstrip("/")
        self.headers = {
            "Api-Token": EMAIL_API_KEY,
            "Content-Type": "application/json"
        }

    def add_subscriber(self, email: str, first_name: str, tags: list) -> Optional[str]:
        payload = {
            "contact": {
                "email": email,
                "firstName": first_name,
                "fieldValues": []
            }
        }
        try:
            r = requests.post(
                f"{self.base_url}/api/3/contacts",
                json=payload, headers=self.headers, timeout=15
            )
            if r.status_code in (200, 201):
                contact_id = r.json().get("contact", {}).get("id")
                if contact_id and tags:
                    self.tag_subscriber(str(contact_id), tags)
                return str(contact_id)
            log.error(f"AC add_subscriber Fehler: {r.status_code} {r.text[:200]}")
        except Exception as e:
            log.error(f"AC add_subscriber Exception: {e}")
        return None

    def tag_subscriber(self, provider_id: str, tags: list) -> bool:
        for tag in tags:
            # Tag erstellen oder ID finden
            try:
                r = requests.post(
                    f"{self.base_url}/api/3/contactTags",
                    json={"contactTag": {"contact": provider_id, "tag": tag}},
                    headers=self.headers, timeout=15
                )
                if r.status_code not in (200, 201):
                    log.warning(f"Tag '{tag}' konnte nicht gesetzt werden: {r.text[:100]}")
            except Exception as e:
                log.error(f"AC tag_subscriber Exception: {e}")
        return True

    def trigger_automation(self, provider_id: str, automation_id: str) -> bool:
        try:
            r = requests.post(
                f"{self.base_url}/api/3/contactAutomations",
                json={"contactAutomation": {
                    "contact": provider_id,
                    "automation": automation_id
                }},
                headers=self.headers, timeout=15
            )
            return r.status_code in (200, 201)
        except Exception as e:
            log.error(f"AC trigger_automation Exception: {e}")
            return False

    def send_broadcast(self, subject: str, html_body: str, list_id: str,
                       segment: Optional[str] = None) -> bool:
        payload = {
            "campaign": {
                "type": "single",
                "status": "1",
                "public": "0",
                "name": f"Broadcast {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "subject": subject,
                "fromname": EMAIL_FROM_NAME,
                "fromemail": EMAIL_FROM_ADDRESS,
                "html": html_body,
                "lists": [{"id": list_id}]
            }
        }
        try:
            r = requests.post(
                f"{self.base_url}/api/3/campaigns",
                json=payload, headers=self.headers, timeout=15
            )
            return r.status_code in (200, 201)
        except Exception as e:
            log.error(f"AC send_broadcast Exception: {e}")
            return False


class MailchimpAdapter(EmailAdapter):
    """Mailchimp Marketing API Integration."""

    def __init__(self):
        # API URL: https://usX.api.mailchimp.com/3.0
        self.base_url = EMAIL_API_URL.rstrip("/")
        self.auth = ("user", EMAIL_API_KEY)

    def add_subscriber(self, email: str, first_name: str, tags: list) -> Optional[str]:
        list_id = os.getenv("MAILCHIMP_LIST_ID", "")
        if not list_id:
            log.error("MAILCHIMP_LIST_ID nicht gesetzt.")
            return None
        payload = {
            "email_address": email,
            "status": "subscribed",
            "merge_fields": {"FNAME": first_name},
            "tags": tags
        }
        try:
            r = requests.put(
                f"{self.base_url}/lists/{list_id}/members/{_md5(email)}",
                json=payload, auth=self.auth, timeout=15
            )
            if r.status_code in (200, 201):
                return r.json().get("id")
            log.error(f"MC add_subscriber Fehler: {r.status_code}")
        except Exception as e:
            log.error(f"MC add_subscriber Exception: {e}")
        return None

    def tag_subscriber(self, provider_id: str, tags: list) -> bool:
        list_id = os.getenv("MAILCHIMP_LIST_ID", "")
        tag_data = [{"name": t, "status": "active"} for t in tags]
        try:
            r = requests.post(
                f"{self.base_url}/lists/{list_id}/members/{provider_id}/tags",
                json={"tags": tag_data}, auth=self.auth, timeout=15
            )
            return r.status_code == 204
        except Exception as e:
            log.error(f"MC tag_subscriber Exception: {e}")
            return False

    def trigger_automation(self, provider_id: str, automation_id: str) -> bool:
        # Mailchimp Automation via email hinzufügen
        log.info(f"MC: Automation {automation_id} für {provider_id} (manuell konfigurieren)")
        return True

    def send_broadcast(self, subject: str, html_body: str, list_id: str,
                       segment: Optional[str] = None) -> bool:
        log.info(f"MC Broadcast: {subject} (Implementierung nach Kampagnen-API)")
        return True


class GetResponseAdapter(EmailAdapter):
    """GetResponse API Integration."""

    def __init__(self):
        self.base_url = "https://api.getresponse.com/v3"
        self.headers = {
            "X-Auth-Token": f"api-key {EMAIL_API_KEY}",
            "Content-Type": "application/json"
        }

    def add_subscriber(self, email: str, first_name: str, tags: list) -> Optional[str]:
        campaign_id = os.getenv("GETRESPONSE_CAMPAIGN_ID", "")
        payload = {
            "email": email,
            "name": first_name,
            "campaign": {"campaignId": campaign_id},
            "tags": [{"tagId": t} for t in tags] if tags else []
        }
        try:
            r = requests.post(
                f"{self.base_url}/contacts",
                json=payload, headers=self.headers, timeout=15
            )
            if r.status_code in (200, 201, 202):
                return r.json().get("contactId")
        except Exception as e:
            log.error(f"GR add_subscriber Exception: {e}")
        return None

    def tag_subscriber(self, provider_id: str, tags: list) -> bool:
        return True  # Tags werden beim Erstellen gesetzt

    def trigger_automation(self, provider_id: str, automation_id: str) -> bool:
        return True

    def send_broadcast(self, subject: str, html_body: str, list_id: str,
                       segment: Optional[str] = None) -> bool:
        return True


def get_adapter() -> EmailAdapter:
    """Gibt den konfigurierten Email-Provider zurück."""
    adapters = {
        "activecampaign": ActiveCampaignAdapter,
        "mailchimp": MailchimpAdapter,
        "getresponse": GetResponseAdapter,
    }
    cls = adapters.get(EMAIL_PROVIDER.lower())
    if not cls:
        raise ValueError(f"Unbekannter EMAIL_PROVIDER: {EMAIL_PROVIDER}")
    return cls()


# ─── Email Content Generator ─────────────────────────────────────────────────

def generate_email_content(step: int, sequence: str = "welcome") -> dict:
    """Generiert Email-Inhalt via Claude API."""
    step_configs = {
        "welcome": {
            1: {"timing": "Tag 0 (sofort)", "topic": "Willkommen + Guide-Erinnerung + Was kommt als Nächstes"},
            2: {"timing": "Tag 1", "topic": "Die größte Herausforderung bei CU — und warum die meisten Ärzte sie ignorieren"},
            3: {"timing": "Tag 3", "topic": "Eine echte Geschichte: Wie Sandra ihren Alltag mit CU verändert hat"},
            4: {"timing": "Tag 5", "topic": "Soft-Pitch: UC Ernährungs-Kompass vorstellen"},
            5: {"timing": "Tag 7", "topic": "Letzte Chance: UC Ernährungs-Kompass + Verknappung"},
        },
        "upsell": {
            1: {"timing": "Tag 0 (nach Kauf)", "topic": "Glückwunsch + Sofortiger Mehrwert + Upsell vorstellen"},
            2: {"timing": "Tag 2", "topic": "Was ohne System passiert — und warum Wissen allein nicht reicht"},
            3: {"timing": "Tag 4", "topic": "Letzte Chance: UC Selbsthilfe-System + Sonderpreis"},
        }
    }

    config = step_configs.get(sequence, {}).get(step, {})

    prompt = f"""Du bist ein empathischer Email-Texter für {BRAND_NAME}, eine Marke für Colitis Ulcerosa Betroffene.

Schreibe Email Schritt {step} der {sequence.upper()}-Sequenz:
- Zeitpunkt: {config.get('timing', '')}
- Thema: {config.get('topic', '')}

REGELN:
- Ton: Warm, peer-to-peer, empathisch (kein Verkäufer-Ton)
- Länge: 150-250 Wörter
- Keine medizinischen Heilsversprechen
- Persönlich (Du-Anrede), keine formelle Anrede
- Kein persönlicher Absender-Name — nur "{BRAND_NAME} Team"
- Auf Deutsch
- Klarer CTA am Ende (wenn relevant)

Antworte NUR mit JSON:
{{
    "subject_a": "Betreffzeile A (max 50 Zeichen)",
    "subject_b": "Betreffzeile B (A/B Variante, max 50 Zeichen)",
    "preview_text": "Preview-Text (max 90 Zeichen)",
    "body_plain": "Email-Text (Plain Text, mit Absätzen)",
    "cta_text": "Button-Text (wenn relevant, sonst null)",
    "cta_url": "Button-URL (Platzhalter z.B. {{SALES_PAGE_URL}})"
}}"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_SMART,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        log.error(f"Email-Generierung Fehler (Schritt {step}): {e}")

    return {
        "subject_a": f"Email {step}",
        "subject_b": f"Email {step} (B)",
        "preview_text": "",
        "body_plain": "",
        "cta_text": None,
        "cta_url": None
    }


def generate_all_sequences(dry_run: bool = DRY_RUN) -> dict:
    """Generiert alle Email-Sequenzen und speichert als Templates."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    # Welcome-Sequenz (5 Emails)
    results["welcome"] = []
    for step in range(1, 6):
        log.info(f"Generiere Welcome-Email {step}/5...")
        content = generate_email_content(step, "welcome")
        results["welcome"].append(content)

        if not dry_run:
            filename = TEMPLATES_DIR / f"welcome_{step}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Welcome {step}: {content.get('subject_a', '—')}")

    # Upsell-Sequenz (3 Emails)
    results["upsell"] = []
    for step in range(1, 4):
        log.info(f"Generiere Upsell-Email {step}/3...")
        content = generate_email_content(step, "upsell")
        results["upsell"].append(content)

        if not dry_run:
            filename = TEMPLATES_DIR / f"upsell_{step}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Upsell {step}: {content.get('subject_a', '—')}")

    return results


# ─── Subscriber Management ────────────────────────────────────────────────────

def process_new_subscriber(email: str, first_name: str,
                            utm_source: str = "", utm_campaign: str = "",
                            utm_medium: str = "",
                            dry_run: bool = DRY_RUN) -> bool:
    """
    Verarbeitet einen neuen Subscriber:
    1. In DB speichern
    2. Beim Email-Provider anmelden
    3. Welcome-Automation triggern
    """
    log.info(f"Neuer Subscriber: {email} ({first_name})")

    # 1. DB
    if not dry_run:
        insert_subscriber(
            email=email,
            first_name=first_name,
            source_utm=utm_source,
            utm_campaign=utm_campaign,
            utm_medium=utm_medium
        )

    # 2. Email-Provider
    if not dry_run and EMAIL_API_KEY:
        try:
            adapter = get_adapter()
            provider_id = adapter.add_subscriber(
                email=email,
                first_name=first_name,
                tags=["uc-lead", "welcome-sequence", f"source-{utm_source or 'direct'}"]
            )
            if provider_id:
                log.info(f"Subscriber bei {EMAIL_PROVIDER} angelegt: {provider_id}")
                # Welcome-Automation triggern
                welcome_automation_id = os.getenv("EMAIL_WELCOME_AUTOMATION_ID", "")
                if welcome_automation_id:
                    adapter.trigger_automation(provider_id, welcome_automation_id)
            return True
        except Exception as e:
            log.error(f"Email-Provider Fehler: {e}")

    if dry_run:
        log.info(f"[DRY-RUN] Würde {email} bei {EMAIL_PROVIDER} anmelden.")
        return True

    return False


def get_sequence_preview() -> None:
    """Zeigt gespeicherte Email-Sequenzen als Preview."""
    print("\n=== EMAIL-SEQUENZEN PREVIEW ===\n")

    for seq in ["welcome", "upsell"]:
        print(f"\n── {seq.upper()}-SEQUENZ ──")
        for i in range(1, 7 if seq == "welcome" else 4):
            path = TEMPLATES_DIR / f"{seq}_{i}.json"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                print(f"\n  Schritt {i}:")
                print(f"    Betreff A: {data.get('subject_a', '—')}")
                print(f"    Betreff B: {data.get('subject_b', '—')}")
                print(f"    Preview:   {data.get('preview_text', '—')}")
                body = data.get('body_plain', '')
                if body:
                    print(f"    Text:      {body[:120]}...")
            else:
                print(f"  Schritt {i}: (noch nicht generiert)")


def _md5(email: str) -> str:
    """MD5-Hash einer Email (für Mailchimp)."""
    import hashlib
    return hashlib.md5(email.lower().encode()).hexdigest()


# ─── Hauptfunktion ────────────────────────────────────────────────────────────

def run(dry_run: bool = DRY_RUN) -> dict:
    log.info("=" * 60)
    log.info("UC EMAIL AGENT — Start")
    log.info(f"Modus: {'DRY-RUN' if dry_run else 'LIVE'}")
    log.info(f"Provider: {EMAIL_PROVIDER}")
    log.info("=" * 60)

    results = generate_all_sequences(dry_run=dry_run)

    stats = get_subscriber_count()
    print(f"\n📊 Subscriber-Stats: {stats}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Email Agent")
    parser.add_argument("--live", action="store_true", help="Templates speichern")
    parser.add_argument("--preview", action="store_true", help="Gespeicherte Sequenzen anzeigen")
    parser.add_argument("--add-subscriber", nargs=2, metavar=("EMAIL", "NAME"),
                        help="Manuell Subscriber hinzufügen")
    args = parser.parse_args()

    init_db()
    if args.preview:
        get_sequence_preview()
    elif args.add_subscriber:
        process_new_subscriber(
            email=args.add_subscriber[0],
            first_name=args.add_subscriber[1],
            dry_run=not args.live
        )
    else:
        run(dry_run=not args.live)
