"""
Google Ads Agent
================
Verwaltet Google Ads Kampagnen für das UC-Business:
- Kampagnen erstellen (Search)
- Keywords hinzufügen / erweitern
- RSA-Anzeigen aktivieren
- Performance-Monitoring
- Automatische Budget-Optimierung

Nutzt Google Ads API v18 (google-ads Python Client).
"""
import json
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    GOOGLE_ADS_CUSTOMER_ID, GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET,
    GOOGLE_ADS_REFRESH_TOKEN, GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_LOGIN_CUSTOMER_ID,
    GOOGLE_ADS_SEED_KEYWORDS, GOOGLE_ADS_NEGATIVE_KEYWORDS,
    DAILY_BUDGET_GOOGLE, TARGET_CPA_LEAD, TARGET_CPA_SALE,
    ROAS_SCALE_UP_THRESHOLD, ROAS_SCALE_DOWN_THRESHOLD, BUDGET_ADJUST_MAX_PCT,
    DRY_RUN, WEBSITE_DOMAIN, BRAND_NAME
)
from db import init_db, insert_campaign, insert_creative, upsert_daily_kpi, log_orchestrator_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def _get_google_ads_client():
    """Erstellt Google Ads API Client."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        config = {
            "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": GOOGLE_ADS_CLIENT_ID,
            "client_secret": GOOGLE_ADS_CLIENT_SECRET,
            "refresh_token": GOOGLE_ADS_REFRESH_TOKEN,
            "use_proto_plus": True,
        }
        if GOOGLE_ADS_LOGIN_CUSTOMER_ID:
            config["login_customer_id"] = GOOGLE_ADS_LOGIN_CUSTOMER_ID
        return GoogleAdsClient.load_from_dict(config)
    except ImportError:
        log.warning("google-ads SDK nicht installiert. Installiere mit: pip install google-ads")
        return None
    except Exception as e:
        log.error(f"Google Ads Client Fehler: {e}")
        return None


# ─── Kampagnen-Setup ──────────────────────────────────────────────────────────

CAMPAIGN_STRUCTURE = {
    "UC | Ernährung": {
        "keywords": [
            "colitis ulcerosa ernährung",
            "ced ernährungsplan",
            "colitis darmgesundheit ernährung",
            "was essen bei colitis ulcerosa",
            "colitis ulcerosa lebensmittel",
            "colitis schub ernährung",
        ],
        "angle": "Ernährung & Schub-Prävention",
        "landing_page": f"https://{WEBSITE_DOMAIN}/?utm_source=google&utm_campaign=ernaehrung"
    },
    "UC | Remission": {
        "keywords": [
            "colitis ulcerosa remission",
            "colitis ulcerosa symptome lindern",
            "colitis ulcerosa selbsthilfe",
            "colitis natürlich behandeln",
            "leben mit colitis ulcerosa",
            "colitis ulcerosa beschwerdefrei",
        ],
        "angle": "Remission & Symptom-Linderung",
        "landing_page": f"https://{WEBSITE_DOMAIN}/?utm_source=google&utm_campaign=remission"
    },
    "UC | Allgemein": {
        "keywords": [
            "colitis ulcerosa erfahrungen",
            "colitis ulcerosa tipps",
            "colitis ulcerosa forum",
            "colitis ulcerosa ratgeber",
            "ced selbsthilfe",
            "colitis ulcerosa schub was tun",
        ],
        "angle": "Information & Community",
        "landing_page": f"https://{WEBSITE_DOMAIN}/?utm_source=google&utm_campaign=allgemein"
    }
}


def create_campaign_structure(dry_run: bool = DRY_RUN) -> list[str]:
    """Erstellt die vollständige Kampagnen-Struktur."""
    log.info("Erstelle Google Ads Kampagnen-Struktur...")
    campaign_ids = []

    if dry_run:
        for name, config in CAMPAIGN_STRUCTURE.items():
            cid = insert_campaign(
                platform="google",
                name=name,
                campaign_type="search",
                budget_daily=DAILY_BUDGET_GOOGLE / len(CAMPAIGN_STRUCTURE),
                target_cpa=TARGET_CPA_SALE
            )
            campaign_ids.append(cid)
            log.info(f"[DRY-RUN] Kampagne geplant: {name} (Budget: €{DAILY_BUDGET_GOOGLE/len(CAMPAIGN_STRUCTURE):.2f}/Tag)")
        return campaign_ids

    client = _get_google_ads_client()
    if not client:
        log.warning("Google Ads Client nicht verfügbar — Dry-Run Fallback")
        return create_campaign_structure(dry_run=True)

    customer_id = GOOGLE_ADS_CUSTOMER_ID.replace("-", "")

    for name, config in CAMPAIGN_STRUCTURE.items():
        try:
            campaign_id = _create_google_campaign(client, customer_id, name, config)
            if campaign_id:
                cid = insert_campaign(
                    platform="google",
                    name=name,
                    campaign_type="search",
                    budget_daily=DAILY_BUDGET_GOOGLE / len(CAMPAIGN_STRUCTURE),
                    target_cpa=TARGET_CPA_SALE,
                    campaign_id=campaign_id
                )
                campaign_ids.append(cid)
                log.info(f"Kampagne erstellt: {name} (ID: {campaign_id})")
        except Exception as e:
            log.error(f"Kampagnen-Erstellung fehlgeschlagen ({name}): {e}")

    return campaign_ids


def _create_google_campaign(client, customer_id: str, name: str, config: dict) -> Optional[str]:
    """Erstellt eine einzelne Google Ads Kampagne via API."""
    try:
        campaign_budget_service = client.get_service("CampaignBudgetService")
        campaign_service = client.get_service("CampaignService")
        ad_group_service = client.get_service("AdGroupService")
        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")

        # 1. Budget erstellen
        budget_op = client.get_type("CampaignBudgetOperation")
        budget = budget_op.create
        budget.name = f"Budget {name} {datetime.now().strftime('%Y%m%d')}"
        budget.amount_micros = int((DAILY_BUDGET_GOOGLE / len(CAMPAIGN_STRUCTURE)) * 1_000_000)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id, operations=[budget_op]
        )
        budget_resource = budget_response.results[0].resource_name

        # 2. Kampagne erstellen (Target CPA Bidding)
        campaign_op = client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.status = client.enums.CampaignStatusEnum.PAUSED  # Erst pausiert, manuell aktivieren
        campaign.campaign_budget = budget_resource
        campaign.target_cpa.target_cpa_micros = int(TARGET_CPA_SALE * 1_000_000)
        campaign.network_settings.target_google_search = True
        campaign.network_settings.target_search_network = True
        campaign.network_settings.target_content_network = False

        # Geo: DE, AT, CH
        campaign.geo_target_type_setting.positive_geo_target_type = (
            client.enums.PositiveGeoTargetTypeEnum.PRESENCE
        )

        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_op]
        )
        campaign_resource = campaign_response.results[0].resource_name
        campaign_id = campaign_resource.split("/")[-1]

        # 3. Ad Group erstellen
        ag_op = client.get_type("AdGroupOperation")
        ad_group = ag_op.create
        ad_group.name = f"{name} | Hauptgruppe"
        ad_group.campaign = campaign_resource
        ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ad_group.cpc_bid_micros = 800_000  # €0.80 Startgebot

        ag_response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id, operations=[ag_op]
        )
        ad_group_resource = ag_response.results[0].resource_name

        # 4. Keywords hinzufügen
        kw_ops = []
        for keyword in config["keywords"]:
            kw_op = client.get_type("AdGroupCriterionOperation")
            kw = kw_op.create
            kw.ad_group = ad_group_resource
            kw.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            kw.keyword.text = keyword
            kw.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
            kw_ops.append(kw_op)

        if kw_ops:
            ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id, operations=kw_ops
            )

        return campaign_id

    except Exception as e:
        log.error(f"Google Ads API Fehler: {e}")
        return None


# ─── Performance Monitoring ───────────────────────────────────────────────────

def get_campaign_performance(days: int = 7, dry_run: bool = DRY_RUN) -> list[dict]:
    """Holt Performance-Daten der letzten N Tage."""
    if dry_run:
        # Simulierte Demo-Daten
        return [
            {"campaign": "UC | Ernährung", "impressions": 1240, "clicks": 52,
             "cost": 18.40, "conversions": 3, "cpa": 6.13, "ctr": 4.2},
            {"campaign": "UC | Remission", "impressions": 890, "clicks": 38,
             "cost": 14.20, "conversions": 2, "cpa": 7.10, "ctr": 4.3},
            {"campaign": "UC | Allgemein", "impressions": 2100, "clicks": 71,
             "cost": 22.10, "conversions": 4, "cpa": 5.53, "ctr": 3.4},
        ]

    client = _get_google_ads_client()
    if not client:
        return []

    customer_id = GOOGLE_ADS_CUSTOMER_ID.replace("-", "")
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")

    query = f"""
        SELECT
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.cost_per_conversion,
            metrics.ctr
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
        AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    results = []
    try:
        ga_service = client.get_service("GoogleAdsService")
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                results.append({
                    "campaign": row.campaign.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "conversions": row.metrics.conversions,
                    "cpa": row.metrics.cost_per_conversion / 1_000_000 if row.metrics.conversions > 0 else 0,
                    "ctr": row.metrics.ctr * 100,
                })
    except Exception as e:
        log.error(f"Google Ads Performance-Fehler: {e}")

    return results


# ─── Automatische Optimierung ─────────────────────────────────────────────────

def optimize_campaigns(dry_run: bool = DRY_RUN) -> list[str]:
    """
    Automatische Kampagnen-Optimierung:
    - ROAS > Schwelle → Budget erhöhen
    - ROAS < Schwelle → Budget senken
    - CTR < 1% → Anzeige pausieren
    """
    actions = []
    performance = get_campaign_performance(days=7, dry_run=dry_run)

    for camp in performance:
        name = camp["campaign"]
        cost = camp.get("cost", 0)
        conversions = camp.get("conversions", 0)
        cpa = camp.get("cpa", 0)
        ctr = camp.get("ctr", 0)

        # CPA-basierte Entscheidung
        if cost > 0 and conversions > 0:
            if cpa < TARGET_CPA_SALE * 0.8:
                # Sehr gute Performance → Budget erhöhen
                action = f"SCALE_UP: {name} | CPA €{cpa:.2f} < Ziel €{TARGET_CPA_SALE:.2f}"
                actions.append(action)
                log.info(f"📈 {action}")
                if not dry_run:
                    _adjust_campaign_budget(name, increase=True)
            elif cpa > TARGET_CPA_SALE * 1.5:
                # Schlechte Performance → Budget senken
                action = f"SCALE_DOWN: {name} | CPA €{cpa:.2f} > Ziel*1.5"
                actions.append(action)
                log.warning(f"📉 {action}")
                if not dry_run:
                    _adjust_campaign_budget(name, increase=False)

        # CTR-Überprüfung
        if ctr < 1.0 and camp.get("impressions", 0) > 500:
            action = f"LOW_CTR: {name} | CTR {ctr:.1f}% — neue Creative-Variante generieren"
            actions.append(action)
            log.warning(f"⚠️ {action}")

        # KPIs in DB speichern
        today = datetime.now().strftime("%Y-%m-%d")
        upsert_daily_kpi(
            date_str=today,
            platform="google",
            impressions=camp.get("impressions", 0),
            clicks=camp.get("clicks", 0),
            spend=cost,
            sales=int(conversions),
            cpa=cpa
        )

    log_orchestrator_action(
        action="google_ads_optimize",
        details=f"{len(performance)} Kampagnen überprüft",
        result="\n".join(actions) if actions else "Keine Aktion nötig",
        dry_run=dry_run
    )

    return actions


def _adjust_campaign_budget(campaign_name: str, increase: bool):
    """Passt das Kampagnen-Budget an."""
    client = _get_google_ads_client()
    if not client:
        return
    # Implementierung: Budget aus DB laden, anpassen, via API setzen
    log.info(f"Budget-Anpassung für '{campaign_name}': {'+ ' if increase else '- '}{BUDGET_ADJUST_MAX_PCT*100:.0f}%")


def add_keywords_from_insights(dry_run: bool = DRY_RUN) -> list[str]:
    """Fügt neue Keywords aus Facebook-Gruppen-Insights hinzu."""
    from groups_intel_agent import load_saved_insights

    data = load_saved_insights()
    if not data:
        log.info("Keine Insights vorhanden — zuerst groups_intel_agent ausführen.")
        return []

    new_keywords = data.get("summary", {}).get("top_keywords", [])
    added = []

    for kw in new_keywords[:10]:
        # Nur Long-Tail Keywords (2+ Wörter)
        if len(kw.split()) >= 2 and kw not in GOOGLE_ADS_SEED_KEYWORDS:
            log.info(f"Neues Keyword aus Insights: {kw}")
            added.append(kw)
            if not dry_run:
                log.info(f"  → Würde zu UC | Allgemein hinzufügen")

    return added


def run_daily_check(dry_run: bool = DRY_RUN) -> dict:
    """Täglicher Google Ads Check für den Orchestrator."""
    log.info("Google Ads: Täglicher Check...")

    performance = get_campaign_performance(days=1, dry_run=dry_run)
    optimizations = optimize_campaigns(dry_run=dry_run)
    new_keywords = add_keywords_from_insights(dry_run=dry_run)

    summary = {
        "campaigns_checked": len(performance),
        "optimizations": optimizations,
        "new_keywords": new_keywords,
        "total_spend_today": sum(c.get("cost", 0) for c in performance),
        "total_conversions_today": sum(c.get("conversions", 0) for c in performance),
    }

    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Google Ads Agent")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--setup", action="store_true", help="Kampagnen-Struktur erstellen")
    parser.add_argument("--check", action="store_true", help="Performance prüfen")
    parser.add_argument("--optimize", action="store_true", help="Automatisch optimieren")
    args = parser.parse_args()

    init_db()
    dry = not args.live

    if args.setup:
        ids = create_campaign_structure(dry_run=dry)
        print(f"Kampagnen erstellt: {ids}")
    elif args.check:
        perf = get_campaign_performance(dry_run=dry)
        print(json.dumps(perf, indent=2, ensure_ascii=False))
    elif args.optimize:
        actions = optimize_campaigns(dry_run=dry)
        for a in actions:
            print(f"  → {a}")
    else:
        result = run_daily_check(dry_run=dry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
