"""
Tracking & Analytics
=====================
Zentrale Tracking-Verwaltung:
- UTM-Parameter-Generierung für alle Kanäle
- GA4 Measurement Protocol (Server-Side Events)
- Meta Conversion API (Server-Side Pixel)
- KPI-Dashboard aus DB
"""
import hashlib
import json
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    GA4_MEASUREMENT_ID, GA4_API_SECRET,
    META_PIXEL_ID, META_ACCESS_TOKEN,
    WEBSITE_DOMAIN, DRY_RUN
)
from db import get_kpi_summary, get_subscriber_count, get_total_revenue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ─── UTM-Parameter Generator ──────────────────────────────────────────────────

UTM_TEMPLATES = {
    "google_search_ernaehrung": {
        "utm_source": "google",
        "utm_medium": "cpc",
        "utm_campaign": "uc-ernaehrung",
        "utm_content": "rsa",
    },
    "google_search_remission": {
        "utm_source": "google",
        "utm_medium": "cpc",
        "utm_campaign": "uc-remission",
        "utm_content": "rsa",
    },
    "meta_lead_gen_v1": {
        "utm_source": "meta",
        "utm_medium": "paid_social",
        "utm_campaign": "uc-lead-gen",
        "utm_content": "variant-1",
    },
    "meta_lead_gen_v2": {
        "utm_source": "meta",
        "utm_medium": "paid_social",
        "utm_campaign": "uc-lead-gen",
        "utm_content": "variant-2",
    },
    "meta_retargeting": {
        "utm_source": "meta",
        "utm_medium": "paid_social",
        "utm_campaign": "uc-retargeting",
        "utm_content": "visitors-30d",
    },
    "email_welcome": {
        "utm_source": "email",
        "utm_medium": "email",
        "utm_campaign": "welcome-sequence",
    },
    "email_upsell": {
        "utm_source": "email",
        "utm_medium": "email",
        "utm_campaign": "upsell-sequence",
    },
}


def build_utm_url(base_url: str, channel: str, utm_term: str = "") -> str:
    """Erstellt eine vollständige URL mit UTM-Parametern."""
    params = UTM_TEMPLATES.get(channel, {}).copy()
    if utm_term:
        params["utm_term"] = utm_term
    return f"{base_url}?{urlencode(params)}"


def get_all_tracking_urls() -> dict:
    """Gibt alle Tracking-URLs für Ads und Emails zurück."""
    optin_url = f"https://{WEBSITE_DOMAIN}/"
    sales_url = f"https://{WEBSITE_DOMAIN}/uc-ernaehrungs-kompass"

    urls = {}
    for channel in UTM_TEMPLATES:
        base = sales_url if "retargeting" in channel else optin_url
        urls[channel] = build_utm_url(base, channel)

    return urls


# ─── GA4 Measurement Protocol ─────────────────────────────────────────────────

def send_ga4_event(client_id: str, event_name: str, params: dict = {},
                   dry_run: bool = DRY_RUN) -> bool:
    """Sendet ein Server-Side Event an GA4."""
    if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
        if not dry_run:
            log.warning("GA4 Measurement ID oder API Secret nicht konfiguriert.")
        return False

    payload = {
        "client_id": client_id,
        "events": [{
            "name": event_name,
            "params": {
                "session_id": hashlib.md5(client_id.encode()).hexdigest()[:10],
                "engagement_time_msec": 1,
                **params
            }
        }]
    }

    if dry_run:
        log.info(f"[DRY-RUN] GA4 Event: {event_name} | Params: {params}")
        return True

    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 204
    except Exception as e:
        log.error(f"GA4 Event Fehler: {e}")
        return False


def track_lead(email: str, utm_source: str = "", utm_campaign: str = "",
               dry_run: bool = DRY_RUN):
    """Trackt einen neuen Lead in GA4 und Meta."""
    client_id = hashlib.md5(email.encode()).hexdigest()

    send_ga4_event(client_id, "generate_lead", {
        "event_category": "optin",
        "utm_source": utm_source,
        "utm_campaign": utm_campaign,
    }, dry_run=dry_run)

    send_meta_conversion_event(email, "Lead", value=0, dry_run=dry_run)


def track_purchase(email: str, product_name: str, revenue: float,
                   utm_source: str = "", dry_run: bool = DRY_RUN):
    """Trackt einen Kauf in GA4 und Meta."""
    client_id = hashlib.md5(email.encode()).hexdigest()

    send_ga4_event(client_id, "purchase", {
        "currency": "EUR",
        "value": revenue,
        "items": [{"item_name": product_name, "price": revenue}],
        "utm_source": utm_source,
    }, dry_run=dry_run)

    send_meta_conversion_event(email, "Purchase", value=revenue, dry_run=dry_run)


# ─── Meta Conversion API ──────────────────────────────────────────────────────

def send_meta_conversion_event(email: str, event_name: str, value: float = 0,
                                dry_run: bool = DRY_RUN) -> bool:
    """Sendet ein Server-Side Conversion Event an Meta (Pixel API)."""
    if not META_PIXEL_ID or not META_ACCESS_TOKEN:
        if not dry_run:
            log.warning("Meta Pixel ID oder Access Token nicht konfiguriert.")
        return False

    # Email hashen (SHA256, lowercase, kein Leerzeichen)
    hashed_email = hashlib.sha256(email.lower().strip().encode()).hexdigest()

    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": int(datetime.now().timestamp()),
            "action_source": "website",
            "user_data": {
                "em": [hashed_email]
            },
            "custom_data": {
                "currency": "EUR",
                "value": value
            }
        }]
    }

    if dry_run:
        log.info(f"[DRY-RUN] Meta CAPI Event: {event_name} | Value: €{value}")
        return True

    try:
        url = f"https://graph.facebook.com/v18.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            return True
        log.error(f"Meta CAPI Fehler: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.error(f"Meta CAPI Exception: {e}")

    return False


# ─── KPI Dashboard ────────────────────────────────────────────────────────────

def print_kpi_dashboard(days: int = 7):
    """Gibt ein KPI-Dashboard in der Konsole aus."""
    kpis = get_kpi_summary(days)
    subscribers = get_subscriber_count()
    total_revenue = get_total_revenue()

    print(f"\n{'='*60}")
    print(f"KPI DASHBOARD — Letzte {days} Tage")
    print(f"{'='*60}")

    print(f"\n📊 SUBSCRIBER:")
    print(f"  Gesamt:   {subscribers.get('total', 0)}")
    print(f"  Leads:    {subscribers.get('leads', 0)}")
    print(f"  Käufer:   {subscribers.get('buyers', 0)}")
    print(f"  VIPs:     {subscribers.get('vips', 0)}")
    print(f"\n💰 UMSATZ GESAMT: €{total_revenue:.2f}")

    if kpis:
        print(f"\n📈 AD PERFORMANCE (letzte {days} Tage):")
        print(f"  {'Datum':<12} {'Platform':<10} {'Impressions':>12} {'Klicks':>8} {'Spend':>8} {'Leads':>6} {'Sales':>6} {'ROAS':>6}")
        print(f"  {'-'*70}")
        for kpi in kpis:
            print(f"  {kpi['date']:<12} {kpi['platform']:<10} "
                  f"{kpi['impressions']:>12,} {kpi['clicks']:>8,} "
                  f"€{kpi['spend']:>6.2f} {kpi['leads']:>6} {kpi['sales']:>6} "
                  f"{kpi['roas']:>5.1f}x")
    else:
        print(f"\n  (Noch keine KPI-Daten vorhanden — Agenten starten)")

    print(f"\n🔗 TRACKING URLS:")
    urls = get_all_tracking_urls()
    for channel, url in list(urls.items())[:4]:
        print(f"  {channel:<30} {url[:60]}...")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Tracking")
    parser.add_argument("--dashboard", action="store_true", help="KPI Dashboard anzeigen")
    parser.add_argument("--urls", action="store_true", help="Alle Tracking-URLs ausgeben")
    parser.add_argument("--test-ga4", action="store_true", help="GA4 Test-Event senden")
    parser.add_argument("--test-meta", action="store_true", help="Meta CAPI Test-Event")
    args = parser.parse_args()

    if args.dashboard:
        print_kpi_dashboard()
    elif args.urls:
        urls = get_all_tracking_urls()
        for channel, url in urls.items():
            print(f"{channel}: {url}")
    elif args.test_ga4:
        send_ga4_event("test-client-123", "page_view", {"page_title": "Test"}, dry_run=True)
    elif args.test_meta:
        send_meta_conversion_event("test@example.com", "Lead", dry_run=True)
    else:
        print_kpi_dashboard()
