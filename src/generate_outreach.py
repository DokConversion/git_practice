"""
Generiert personalisierte Outreach-Nachrichten fuer Instagram DMs.

Nutzt die Claude API um authentische "Dabei-gewesen"-Nachrichten zu erstellen,
basierend auf Landing-Page-Inhalten und Webinar-Thema.

Verwendung:
    python src/generate_outreach.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from src.db import (
    get_connection, init_db, get_yesterdays_webinars,
    get_contact_for_ad, insert_outreach, get_pending_outreach,
)


# Fallback-Template falls keine API verfuegbar
TEMPLATE_INSTAGRAM = """Hey {name},

war gestern bei deinem Webinar zu "{topic}" dabei. {specific_hook}

Eine Sache, die mir aufgefallen ist: Der Raum war ziemlich duenn besetzt im Verhaeltnis zu dem, was du sicher an Anmeldungen hattest, oder?

Das hoere ich mega oft von {target_label} — 500 Anmeldungen, 80 kommen, und du stehst trotzdem 2 Stunden live da und gibst Vollgas.

Ich helfe Leuten wie dir dabei, diese Abhaengigkeit von Live-Terminen komplett loszuwerden — ohne auf Umsatz zu verzichten. Haettest du Bock, da mal kurz drueber zu quatschen?

LG Marc"""


def generate_specific_hook(topic: str, landing_page_content: str) -> str:
    """
    Generiert einen spezifischen Bezug zum Webinar-Inhalt
    basierend auf Landing-Page-Informationen.
    """
    content = (topic + " " + landing_page_content).lower()

    # Themen-spezifische Hooks
    hooks = {
        "skalier": "Richtig guter Ansatz, wie du das Thema Skalierung angegangen bist.",
        "umsatz": "Besonders der Teil zum Thema Umsatzsteigerung war stark.",
        "kunden": "Der Punkt zur Kundengewinnung war richtig gut auf den Punkt gebracht.",
        "leads": "Dein Ansatz zur Lead-Generierung war echt spannend.",
        "mindset": "Dein Mindset-Ansatz hat mich echt abgeholt.",
        "positionier": "Wie du das Thema Positionierung erklaert hast, war richtig stark.",
        "social media": "Deine Social-Media-Strategie war mega interessant.",
        "marketing": "Dein Marketing-Ansatz war richtig gut strukturiert.",
        "verkauf": "Der Teil zum Thema Verkaufen war echt auf den Punkt.",
        "coaching": "Dein Framework fuer Coaching-Prozesse war echt durchdacht.",
        "funnel": "Wie du das Thema Funnel erklaert hast, war richtig stark.",
        "ads": "Dein Ansatz zu Werbeanzeigen war mega praxisnah.",
        "content": "Dein Content-Ansatz war richtig gut erklaert.",
        "automatisier": "Der Teil zur Automatisierung war besonders spannend.",
    }

    for keyword, hook in hooks.items():
        if keyword in content:
            return hook

    return "Richtig guter Content, war mega praxisnah."


def guess_target_label(ad_text: str, topic: str) -> str:
    """Erratet die Zielgruppen-Bezeichnung basierend auf dem Anzeigentext."""
    text = (ad_text + " " + topic).lower()

    if any(x in text for x in ["coach", "coaching"]):
        return "Coaches"
    if any(x in text for x in ["berater", "beratung", "consulting"]):
        return "Beratern"
    if any(x in text for x in ["trainer", "training"]):
        return "Trainern"
    if any(x in text for x in ["agentur", "agency"]):
        return "Agentur-Inhabern"
    if any(x in text for x in ["therapeut", "therapie", "heilpraktiker"]):
        return "Therapeuten"
    if any(x in text for x in ["immobili"]):
        return "Immobilien-Profis"

    return "Dienstleistern"


async def generate_message_with_llm(name: str, topic: str,
                                      landing_page_content: str,
                                      ad_text: str) -> str | None:
    """
    Generiert eine personalisierte Nachricht mit der Claude API.
    Gibt None zurueck falls keine API verfuegbar.
    """
    if not config.ANTHROPIC_API_KEY:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        prompt = f"""Du bist Marc von quantum-bsl.com. Schreibe eine kurze, persoenliche Instagram-DM
an {name}, der/die gestern ein Live-Webinar zum Thema "{topic}" gehalten hat.

Kontext von der Landing Page:
{landing_page_content[:1500]}

Regeln:
- Du tust so als waerst du beim Webinar dabei gewesen
- Beziehe dich auf 1-2 spezifische Aspekte die auf der Landing Page versprochen wurden
- Sprich das Problem der geringen Show-up-Rate bei Live-Webinaren an
- Biete deine Hilfe an, die Abhaengigkeit von Live-Webinaren zu reduzieren
- Duze den Empfaenger
- Schreibe maximal 6-8 kurze Saetze
- Kein Emoji-Overkill, maximal 0-1 Emoji
- Ton: locker, authentisch, nicht verkaeufisch
- Unterschreibe mit "LG Marc"
- KEIN Betreff, direkt mit "Hey {name}" starten"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    except Exception as e:
        print(f"  LLM-Fehler: {e}")
        return None


async def generate_messages_for_yesterdays_webinars():
    """
    Generiert Outreach-Nachrichten fuer alle Webinare von gestern.
    """
    webinars = get_yesterdays_webinars()
    print(f"Webinare von gestern ohne Outreach: {len(webinars)}")

    for webinar in webinars:
        contact = get_contact_for_ad(webinar["ad_id"])
        if not contact:
            print(f"  Kein Kontakt fuer: {webinar['advertiser_name']} — uebersprungen")
            continue

        name = contact["name"] or webinar["advertiser_name"]
        topic = webinar["webinar_topic"]
        ad_text = webinar.get("ad_text", "")
        lp_content = webinar.get("landing_page_content", "")

        print(f"\nGeneriere Nachricht fuer: {name}")
        print(f"  Thema: {topic}")

        # Bestimme Kanal
        if contact.get("instagram_handle"):
            channel = "instagram"
        elif contact.get("linkedin_url"):
            channel = "linkedin"
        elif contact.get("email"):
            channel = "email"
        else:
            print(f"  Kein Kontaktkanal verfuegbar — uebersprungen")
            continue

        # Versuche LLM-generierte Nachricht
        message = await generate_message_with_llm(name, topic, lp_content, ad_text)

        # Fallback auf Template
        if not message:
            target_label = guess_target_label(ad_text, topic)
            specific_hook = generate_specific_hook(topic, lp_content)
            message = TEMPLATE_INSTAGRAM.format(
                name=name,
                topic=topic,
                specific_hook=specific_hook,
                target_label=target_label,
            )

        # Speichere in DB
        outreach_id = insert_outreach(
            contact_id=contact["id"],
            webinar_id=webinar["id"],
            channel=channel,
            message_text=message,
        )

        contact_info = ""
        if channel == "instagram":
            contact_info = f"@{contact['instagram_handle']}"
        elif channel == "linkedin":
            contact_info = contact["linkedin_url"]
        else:
            contact_info = contact["email"]

        print(f"  -> Nachricht generiert (#{outreach_id}, {channel}: {contact_info})")


def show_pending_messages():
    """Zeigt alle noch nicht gesendeten Nachrichten an."""
    messages = get_pending_outreach()

    if not messages:
        print("\nKeine ausstehenden Nachrichten.")
        return

    print(f"\n{'='*60}")
    print(f"AUSSTEHENDE NACHRICHTEN ({len(messages)})")
    print(f"{'='*60}")

    for msg in messages:
        print(f"\n--- #{msg['id']} | {msg['channel'].upper()} ---")
        print(f"An: {msg['name']}", end="")
        if msg.get("instagram_handle"):
            print(f" (@{msg['instagram_handle']})")
        elif msg.get("email"):
            print(f" ({msg['email']})")
        else:
            print()
        print(f"Generiert: {msg['generated_at']}")
        print(f"\n{msg['message_text']}")
        print()


async def main():
    init_db()
    await generate_messages_for_yesterdays_webinars()
    show_pending_messages()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
