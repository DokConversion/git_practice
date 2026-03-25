"""
Facebook / Meta Ads Agent
==========================
Verwaltet Meta-Kampagnen für das UC-Business:
- Lead Generation (Optin-Kampagne)
- Traffic-Kampagnen (Sales Page)
- Retargeting (Websitebesucher)
- Creative-Rotation (A/B Testing)
- Performance-Monitoring

Nutzt facebook-business Python SDK.
"""
import json
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PIXEL_ID, META_PAGE_ID,
    DAILY_BUDGET_META, TARGET_CPA_LEAD, TARGET_CPA_SALE,
    WEBSITE_DOMAIN, BRAND_NAME, DRY_RUN
)
from db import init_db, insert_campaign, insert_creative, upsert_daily_kpi, log_orchestrator_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def _get_meta_client():
    """Initialisiert Meta Business SDK."""
    try:
        from facebook_business.api import FacebookAdsApi
        FacebookAdsApi.init(access_token=META_ACCESS_TOKEN)
        return True
    except ImportError:
        log.warning("facebook-business SDK nicht installiert. Installiere mit: pip install facebook-business")
        return False
    except Exception as e:
        log.error(f"Meta API Init Fehler: {e}")
        return False


# ─── Targeting-Konfigurationen ────────────────────────────────────────────────

TARGETING_CONFIGS = {
    "cold_uc_interests": {
        "description": "Cold Audience: UC-Interessen",
        "age_min": 25,
        "age_max": 65,
        "genders": [],  # Alle
        "locales": [4, 5, 29],   # DE, AT, CH
        "flexible_spec": [
            {
                "interests": [
                    {"id": "6003397006116", "name": "Colitis ulcerosa"},
                    {"id": "6003232518145", "name": "Morbus Crohn"},
                    {"id": "6003129668853", "name": "Darmgesundheit"},
                    {"id": "6003008238581", "name": "Chronische Erkrankung"},
                ]
            }
        ]
    },
    "health_health_nutrition": {
        "description": "Health & Nutrition Zielgruppe",
        "age_min": 28,
        "age_max": 60,
        "flexible_spec": [
            {
                "interests": [
                    {"id": "6003088755965", "name": "Gesunde Ernährung"},
                    {"id": "6002925228754", "name": "Naturheilkunde"},
                    {"id": "6003026108951", "name": "Darmflora"},
                ]
            }
        ]
    },
    "retargeting_website": {
        "description": "Retargeting: Websitebesucher letzte 30 Tage",
        "custom_audiences": [
            {"id": "PIXEL_CUSTOM_AUDIENCE_ID", "name": "Website Visitors 30d"}
        ],
        "exclusions": [
            {"id": "BUYERS_CUSTOM_AUDIENCE_ID", "name": "Buyers"}
        ]
    }
}

CAMPAIGN_TYPES = {
    "lead_gen": {
        "objective": "LEAD_GENERATION",
        "name": "UC | Lead Gen | Opt-in",
        "budget_pct": 0.5,  # 50% des Meta-Budgets
        "targeting": "cold_uc_interests",
        "destination": f"https://{WEBSITE_DOMAIN}/?utm_source=meta&utm_campaign=lead_gen"
    },
    "traffic": {
        "objective": "LINK_CLICKS",
        "name": "UC | Traffic | Sales Page",
        "budget_pct": 0.3,
        "targeting": "health_health_nutrition",
        "destination": f"https://{WEBSITE_DOMAIN}/uc-ernaehrungs-kompass?utm_source=meta&utm_campaign=traffic"
    },
    "retargeting": {
        "objective": "CONVERSIONS",
        "name": "UC | Retargeting | Käufer",
        "budget_pct": 0.2,
        "targeting": "retargeting_website",
        "destination": f"https://{WEBSITE_DOMAIN}/uc-ernaehrungs-kompass?utm_source=meta&utm_campaign=retargeting"
    }
}


# ─── Kampagnen erstellen ──────────────────────────────────────────────────────

def create_campaign_structure(dry_run: bool = DRY_RUN) -> list[str]:
    """Erstellt die vollständige Meta-Kampagnen-Struktur."""
    log.info("Erstelle Meta Ads Kampagnen-Struktur...")
    campaign_ids = []

    if dry_run:
        for key, config in CAMPAIGN_TYPES.items():
            budget = DAILY_BUDGET_META * config["budget_pct"]
            cid = insert_campaign(
                platform="meta",
                name=config["name"],
                campaign_type=key,
                budget_daily=budget,
                target_cpa=TARGET_CPA_LEAD if key == "lead_gen" else TARGET_CPA_SALE
            )
            campaign_ids.append(cid)
            log.info(f"[DRY-RUN] Meta Kampagne geplant: {config['name']} (€{budget:.2f}/Tag)")
        return campaign_ids

    if not _get_meta_client():
        log.warning("Meta Client nicht verfügbar — Dry-Run Fallback")
        return create_campaign_structure(dry_run=True)

    for key, config in CAMPAIGN_TYPES.items():
        try:
            campaign_id = _create_meta_campaign(config)
            if campaign_id:
                cid = insert_campaign(
                    platform="meta",
                    name=config["name"],
                    campaign_type=key,
                    budget_daily=DAILY_BUDGET_META * config["budget_pct"],
                    target_cpa=TARGET_CPA_LEAD if key == "lead_gen" else TARGET_CPA_SALE,
                    campaign_id=campaign_id
                )
                campaign_ids.append(cid)
                log.info(f"Meta Kampagne erstellt: {config['name']} (ID: {campaign_id})")
        except Exception as e:
            log.error(f"Meta Kampagnen-Erstellung fehlgeschlagen ({key}): {e}")

    return campaign_ids


def _create_meta_campaign(config: dict) -> Optional[str]:
    """Erstellt eine Meta Kampagne + Ad Set + Ad via API."""
    try:
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.adobjects.adset import AdSet
        from facebook_business.adobjects.ad import Ad
        from facebook_business.adobjects.adcreative import AdCreative

        account = AdAccount(META_AD_ACCOUNT_ID)

        # 1. Kampagne
        campaign = account.create_campaign(fields=[], params={
            "name": config["name"],
            "objective": config["objective"],
            "status": "PAUSED",  # Erst pausiert starten
            "special_ad_categories": [],
        })
        campaign_id = campaign["id"]

        # 2. Ad Set
        targeting = TARGETING_CONFIGS.get(config["targeting"], {})
        budget = int(DAILY_BUDGET_META * config["budget_pct"] * 100)  # Cent

        ad_set_params = {
            "name": f"{config['name']} | Ad Set",
            "campaign_id": campaign_id,
            "daily_budget": budget,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LEAD_GENERATION" if "lead" in config["objective"].lower() else "LINK_CLICKS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "status": "PAUSED",
            "targeting": {
                "age_min": targeting.get("age_min", 25),
                "age_max": targeting.get("age_max", 65),
                "geo_locations": {"countries": ["DE", "AT", "CH"]},
                "flexible_spec": targeting.get("flexible_spec", []),
            }
        }

        if targeting.get("custom_audiences"):
            ad_set_params["targeting"]["custom_audiences"] = targeting["custom_audiences"]
        if targeting.get("exclusions"):
            ad_set_params["targeting"]["excluded_custom_audiences"] = targeting["exclusions"]

        account.create_ad_set(fields=[], params=ad_set_params)
        return campaign_id

    except Exception as e:
        log.error(f"Meta API Fehler: {e}")
        return None


# ─── Creative-Rotation ────────────────────────────────────────────────────────

def rotate_underperforming_creatives(dry_run: bool = DRY_RUN) -> list[str]:
    """Pausiert schlechte Creatives und aktiviert neue Varianten."""
    actions = []
    performance = get_ad_performance(dry_run=dry_run)

    CPM_THRESHOLD = 15.0   # €15 CPM Obergrenze
    CTR_THRESHOLD = 0.8    # 0.8% CTR Untergrenze
    MIN_IMPRESSIONS = 1000  # Erst bei ausreichend Daten entscheiden

    for ad in performance:
        impressions = ad.get("impressions", 0)
        if impressions < MIN_IMPRESSIONS:
            continue

        ctr = ad.get("ctr", 0)
        cpm = ad.get("cpm", 0)
        ad_name = ad.get("name", "Unbekannt")

        if ctr < CTR_THRESHOLD or cpm > CPM_THRESHOLD:
            action = (f"PAUSE_AD: {ad_name} | CTR: {ctr:.2f}% | CPM: €{cpm:.2f} "
                      f"— generiere neue Creative-Variante")
            actions.append(action)
            log.warning(f"⚠️ {action}")
            if not dry_run:
                _pause_meta_ad(ad.get("id", ""))

    if actions:
        log.info(f"{len(actions)} Creatives werden ausgetauscht.")

    return actions


def _pause_meta_ad(ad_id: str):
    """Pausiert eine Meta Anzeige."""
    if not _get_meta_client():
        return
    try:
        from facebook_business.adobjects.ad import Ad
        ad = Ad(ad_id)
        ad.api_update(fields=[], params={"status": "PAUSED"})
        log.info(f"Meta Ad pausiert: {ad_id}")
    except Exception as e:
        log.error(f"Meta Ad pausieren fehlgeschlagen: {e}")


# ─── Performance Monitoring ───────────────────────────────────────────────────

def get_ad_performance(days: int = 7, dry_run: bool = DRY_RUN) -> list[dict]:
    """Holt Performance-Daten der letzten N Tage."""
    if dry_run:
        return [
            {"name": "UC Lead Gen Var 1", "impressions": 8400, "clicks": 420,
             "ctr": 5.0, "cpm": 8.20, "spend": 68.88, "leads": 34, "cpl": 2.03},
            {"name": "UC Lead Gen Var 2", "impressions": 7200, "clicks": 288,
             "ctr": 4.0, "cpm": 9.10, "spend": 65.52, "leads": 21, "cpl": 3.12},
            {"name": "UC Traffic Sales", "impressions": 4100, "clicks": 164,
             "ctr": 4.0, "cpm": 7.80, "spend": 31.98, "leads": 5, "cpl": 6.40},
        ]

    if not _get_meta_client():
        return []

    try:
        from facebook_business.adobjects.adaccount import AdAccount
        from facebook_business.adobjects.adobjectdataobjects import DatePreset

        account = AdAccount(META_AD_ACCOUNT_ID)
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        insights = account.get_insights(fields=[
            "ad_name", "impressions", "clicks", "ctr", "cpm", "spend", "actions"
        ], params={
            "time_range": {"since": date_from, "until": date_to},
            "level": "ad"
        })

        results = []
        for insight in insights:
            leads = 0
            for action in insight.get("actions", []):
                if action["action_type"] in ("lead", "complete_registration"):
                    leads += int(action["value"])

            spend = float(insight.get("spend", 0))
            results.append({
                "name": insight.get("ad_name", ""),
                "impressions": int(insight.get("impressions", 0)),
                "clicks": int(insight.get("clicks", 0)),
                "ctr": float(insight.get("ctr", 0)),
                "cpm": float(insight.get("cpm", 0)),
                "spend": spend,
                "leads": leads,
                "cpl": spend / leads if leads > 0 else 0
            })
        return results

    except Exception as e:
        log.error(f"Meta Performance-Fehler: {e}")
        return []


def run_daily_check(dry_run: bool = DRY_RUN) -> dict:
    """Täglicher Meta Ads Check für den Orchestrator."""
    log.info("Meta Ads: Täglicher Check...")

    performance = get_ad_performance(days=1, dry_run=dry_run)
    rotations = rotate_underperforming_creatives(dry_run=dry_run)

    total_spend = sum(a.get("spend", 0) for a in performance)
    total_leads = sum(a.get("leads", 0) for a in performance)

    # KPIs in DB speichern
    today = datetime.now().strftime("%Y-%m-%d")
    if performance:
        upsert_daily_kpi(
            date_str=today,
            platform="meta",
            impressions=sum(a.get("impressions", 0) for a in performance),
            clicks=sum(a.get("clicks", 0) for a in performance),
            spend=total_spend,
            leads=total_leads,
            cpl=total_spend / total_leads if total_leads > 0 else 0
        )

    log_orchestrator_action(
        action="meta_ads_daily_check",
        details=f"{len(performance)} Ads geprüft",
        result=f"Spend: €{total_spend:.2f} | Leads: {total_leads} | Rotationen: {len(rotations)}",
        dry_run=dry_run
    )

    return {
        "ads_checked": len(performance),
        "creative_rotations": rotations,
        "total_spend": total_spend,
        "total_leads": total_leads,
        "avg_cpl": total_spend / total_leads if total_leads > 0 else 0
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UC Meta Ads Agent")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--setup", action="store_true", help="Kampagnen erstellen")
    parser.add_argument("--check", action="store_true", help="Performance prüfen")
    parser.add_argument("--rotate", action="store_true", help="Creatives rotieren")
    args = parser.parse_args()

    init_db()
    dry = not args.live

    if args.setup:
        ids = create_campaign_structure(dry_run=dry)
        print(f"Kampagnen erstellt: {ids}")
    elif args.check:
        perf = get_ad_performance(dry_run=dry)
        print(json.dumps(perf, indent=2, ensure_ascii=False))
    elif args.rotate:
        actions = rotate_underperforming_creatives(dry_run=dry)
        for a in actions:
            print(f"  → {a}")
    else:
        result = run_daily_check(dry_run=dry)
        print(json.dumps(result, indent=2, ensure_ascii=False))
