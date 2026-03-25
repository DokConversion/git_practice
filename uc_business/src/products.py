"""
Produkt-Verwaltung & Auslieferung
===================================
Verwaltet den digitalen Produkt-Katalog und die Auslieferung:
- Produkt-Katalog in DB
- Integration mit Digistore24 / Elopage
- Kauf-Webhooks verarbeiten
- Produkt-Zugang gewähren
- Subscriber-Status aktualisieren (lead → buyer → vip)
"""
import json
import os
import sys
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Optional

import requests

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    PRODUCT_PLATFORM, PRODUCT_API_KEY, PRODUCT_API_SECRET,
    PRICE_ENTRY_PRODUCT, PRICE_UPSELL_PRODUCT, DRY_RUN, BRAND_NAME
)
from db import init_db, get_connection, log_orchestrator_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ─── Produkt-Katalog ──────────────────────────────────────────────────────────

PRODUCT_CATALOG = [
    {
        "name": "UC Starter-Guide",
        "type": "pdf",
        "price": 0.0,
        "description": "Kostenloser Einsteiger-Guide: Die 5 häufigsten Fehler bei Colitis Ulcerosa",
        "delivery_type": "email",
        "platform_product_id": os.getenv("PRODUCT_ID_LEADMAGNET", ""),
    },
    {
        "name": "UC Ernährungs-Kompass",
        "type": "pdf",
        "price": PRICE_ENTRY_PRODUCT,
        "description": "85-seitiger Schritt-für-Schritt-Ernährungsführer für CU-Betroffene",
        "delivery_type": "download_link",
        "platform_product_id": os.getenv("PRODUCT_ID_ENTRY", ""),
    },
    {
        "name": "UC Selbsthilfe-System",
        "type": "course",
        "price": PRICE_UPSELL_PRODUCT,
        "description": "8-Wochen-Video-Programm für Colitis Ulcerosa Betroffene",
        "delivery_type": "course_access",
        "platform_product_id": os.getenv("PRODUCT_ID_UPSELL", ""),
    }
]


def seed_products():
    """Befüllt die Produkt-Tabelle mit dem Katalog."""
    conn = get_connection()
    for p in PRODUCT_CATALOG:
        conn.execute("""
            INSERT OR IGNORE INTO products (name, type, price, platform_product_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, (p["name"], p["type"], p["price"], p.get("platform_product_id", ""), p["description"]))
    conn.commit()
    conn.close()
    log.info(f"Produkt-Katalog initialisiert: {len(PRODUCT_CATALOG)} Produkte")


def get_product_by_platform_id(platform_id: str) -> Optional[dict]:
    """Findet ein Produkt anhand der Plattform-Produkt-ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE platform_product_id = ?", (platform_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_name(name: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE name LIKE ?", (f"%{name}%",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Webhook-Verarbeitung ─────────────────────────────────────────────────────

def verify_digistore_webhook(payload: bytes, signature: str) -> bool:
    """Verifiziert Digistore24 Webhook-Signatur."""
    expected = hmac.new(
        PRODUCT_API_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_purchase_webhook(data: dict, platform: str = "digistore24",
                              dry_run: bool = DRY_RUN) -> bool:
    """
    Verarbeitet einen Kauf-Webhook von der Produkt-Plattform.
    Wird von einem Webserver-Endpunkt aufgerufen (z.B. FastAPI/Flask).

    data enthält: email, first_name, product_id, amount, order_id, utm_*
    """
    email = data.get("email", "")
    first_name = data.get("first_name", data.get("name", "").split()[0])
    product_platform_id = data.get("product_id", data.get("product", ""))
    amount = float(data.get("amount", data.get("order_gross", 0)))
    order_id = data.get("order_id", data.get("order", ""))
    utm_source = data.get("utm_source", "")
    utm_campaign = data.get("utm_campaign", "")

    if not email:
        log.error("Webhook ohne E-Mail empfangen.")
        return False

    log.info(f"Kauf verarbeiten: {email} | Produkt-ID: {product_platform_id} | €{amount:.2f}")

    if dry_run:
        log.info(f"[DRY-RUN] Kauf würde verarbeitet: {email}")
        return True

    product = get_product_by_platform_id(product_platform_id)
    if not product:
        log.warning(f"Produkt nicht gefunden: {product_platform_id}")
        product_id = None
    else:
        product_id = product["id"]

    # 1. Subscriber aktualisieren (lead → buyer / vip)
    conn = get_connection()
    existing = conn.execute(
        "SELECT id, status FROM subscribers WHERE email = ?", (email,)
    ).fetchone()

    if existing:
        sub_id = existing["id"]
        new_status = "vip" if existing["status"] == "buyer" else "buyer"
        conn.execute(
            "UPDATE subscribers SET status = ?, last_activity = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), sub_id)
        )
    else:
        cur = conn.execute("""
            INSERT INTO subscribers (email, first_name, source_utm, utm_campaign, status)
            VALUES (?, ?, ?, ?, 'buyer')
        """, (email, first_name, utm_source, utm_campaign))
        sub_id = cur.lastrowid

    # 2. Conversion speichern
    conn.execute("""
        INSERT INTO conversions
            (subscriber_id, product_id, revenue, channel, utm_source, utm_campaign, platform_order_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sub_id, product_id, amount, utm_source or platform, utm_source, utm_campaign, order_id))

    conn.commit()
    conn.close()

    # 3. Email-Automation triggern
    _trigger_post_purchase_email(email, first_name, product, sub_id)

    log_orchestrator_action(
        action="purchase_processed",
        details=f"{email} | {product.get('name', 'Unbekannt') if product else 'Unbekannt'} | €{amount:.2f}",
        result="success",
        dry_run=False
    )

    log.info(f"Kauf erfolgreich verarbeitet: {email} | {order_id}")
    return True


def _trigger_post_purchase_email(email: str, first_name: str,
                                  product: Optional[dict], subscriber_id: int):
    """Triggert die passende Post-Kauf Email-Automation."""
    from email_agent import get_adapter, process_new_subscriber
    import os

    if not product:
        return

    try:
        adapter = get_adapter()
        provider_id = None

        conn = get_connection()
        row = conn.execute(
            "SELECT provider_id FROM subscribers WHERE id = ?", (subscriber_id,)
        ).fetchone()
        conn.close()

        if row and row["provider_id"]:
            provider_id = row["provider_id"]

        if not provider_id:
            # Neu beim Provider anlegen
            provider_id = adapter.add_subscriber(
                email=email,
                first_name=first_name,
                tags=["buyer", f"product-{product.get('type', 'pdf')}"]
            )

        if provider_id:
            # Tag aktualisieren
            adapter.tag_subscriber(provider_id, ["buyer"])

            # Upsell-Automation wenn Entry-Produkt gekauft
            if product.get("price", 0) < PRICE_UPSELL_PRODUCT:
                upsell_automation_id = os.getenv("EMAIL_UPSELL_AUTOMATION_ID", "")
                if upsell_automation_id:
                    adapter.trigger_automation(provider_id, upsell_automation_id)
                    log.info(f"Upsell-Automation getriggert für: {email}")

    except Exception as e:
        log.error(f"Post-Kauf Email Fehler: {e}")


# ─── Revenue Reports ──────────────────────────────────────────────────────────

def get_revenue_summary(days: int = 30) -> dict:
    """Umsatz-Übersicht der letzten N Tage."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            p.name as product_name,
            COUNT(c.id) as sales,
            SUM(c.revenue) as revenue,
            AVG(c.revenue) as avg_order_value
        FROM conversions c
        LEFT JOIN products p ON c.product_id = p.id
        WHERE c.converted_at >= datetime('now', ?)
        GROUP BY p.name
        ORDER BY revenue DESC
    """, (f"-{days} days",)).fetchall()
    conn.close()

    total_revenue = sum(r["revenue"] or 0 for r in rows)
    total_sales = sum(r["sales"] for r in rows)

    return {
        "days": days,
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "by_product": [dict(r) for r in rows]
    }


def print_revenue_report():
    """Gibt einen Umsatz-Report aus."""
    report = get_revenue_summary(30)
    print(f"\n{'='*50}")
    print(f"UMSATZ-REPORT (letzte 30 Tage)")
    print(f"{'='*50}")
    print(f"Gesamtumsatz: €{report['total_revenue']:.2f}")
    print(f"Gesamtverkäufe: {report['total_sales']}")
    if report["by_product"]:
        print("\nNach Produkt:")
        for p in report["by_product"]:
            print(f"  {p['product_name']}: {p['sales']} Verkäufe | €{p['revenue']:.2f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Products Manager")
    parser.add_argument("--seed", action="store_true", help="Produkt-Katalog initialisieren")
    parser.add_argument("--report", action="store_true", help="Umsatz-Report")
    parser.add_argument("--test-webhook", action="store_true", help="Test-Kauf simulieren")
    args = parser.parse_args()

    init_db()
    if args.seed:
        seed_products()
    elif args.report:
        print_revenue_report()
    elif args.test_webhook:
        process_purchase_webhook({
            "email": "test@example.com",
            "first_name": "Max",
            "product_id": "UC-KOMPASS-001",
            "amount": PRICE_ENTRY_PRODUCT,
            "order_id": "TEST-001",
            "utm_source": "google",
            "utm_campaign": "UC | Ernährung"
        }, dry_run=True)
