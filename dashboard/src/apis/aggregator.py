"""
Central aggregator: fetches from all three API clients, merges into a unified
KPI dict, handles caching, and computes derived combined metrics.
"""
import time
from datetime import date, datetime
from calendar import monthrange

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import config
from src.db import cache_repo, client_repo
from src.apis.meta       import MetaAdsClient
from src.apis.ga4        import GA4Client
from src.apis.close_crm  import CloseCRMClient


def _ttl(date_from: date, date_to: date, service: str) -> int:
    today = date.today()
    if date_to >= today:
        if service == "meta":
            return config.CACHE_TTL["today_meta"]
        elif service == "ga4":
            return config.CACHE_TTL["today_ga4"]
        else:
            return config.CACHE_TTL["today_close"]
    days = (today - date_from).days
    if days <= 7:
        return config.CACHE_TTL["recent"]
    if days <= 32:
        return config.CACHE_TTL["month"]
    return config.CACHE_TTL["historical"]


def _date_key(date_from: date, date_to: date) -> str:
    return f"{date_from}_{date_to}"


def _budget_pacing(meta_spend: float, monthly_budget: float, date_from: date, date_to: date) -> float:
    if not monthly_budget:
        return 0.0
    today = date.today()
    days_in_month = monthrange(today.year, today.month)[1]
    days_elapsed  = today.day
    spend_pct  = meta_spend / monthly_budget
    time_pct   = days_elapsed / days_in_month
    return round(spend_pct / time_pct, 3) if time_pct else 0.0


def build_client_kpis(
    client_id: int,
    date_from: date,
    date_to: date,
    force_refresh: bool = False,
    monthly_budget: float = 0.0,
) -> dict:
    """Return merged KPI dict for a client and date range."""
    date_key = _date_key(date_from, date_to)
    merged   = {}

    for service, ClientClass in [
        ("meta",      MetaAdsClient),
        ("ga4",       GA4Client),
        ("close_crm", CloseCRMClient),
    ]:
        if not force_refresh:
            cached = cache_repo.get_cached(client_id, service, date_key)
            if cached:
                merged.update(cached)
                continue

        if not client_repo.has_credentials(client_id, service):
            continue

        t0 = time.time()
        try:
            creds  = client_repo.get_credentials(client_id, service)
            client = ClientClass(client_id, creds)
            data   = client.fetch(date_from, date_to)
            ttl    = _ttl(date_from, date_to, service)
            cache_repo.set_cache(client_id, service, date_key, data, ttl)
            cache_repo.log_refresh(client_id, service, "success", duration_ms=int((time.time()-t0)*1000))
            merged.update(data)
        except Exception as exc:
            cache_repo.log_refresh(client_id, service, "error", str(exc))
            merged[f"_{service}_error"] = str(exc)

    # ── Derived / combined metrics ────────────────────────────────────────────
    spend   = merged.get("meta_spend", 0.0)
    revenue = merged.get("crm_revenue", 0.0)
    deals   = merged.get("crm_won_deals", 0)

    merged["combined_roas"] = round(revenue / spend, 2) if spend else 0.0
    merged["combined_cac"]  = round(spend / deals, 2) if deals else 0.0
    merged["budget_pacing_pct"] = _budget_pacing(spend, monthly_budget, date_from, date_to)

    return merged


def build_timeseries(client_id: int, date_from: date, date_to: date) -> dict:
    """Return {meta: [...], ga4: [...]} daily timeseries for charts."""
    result = {}
    ts_key = _date_key(date_from, date_to) + "_ts"

    for service, ClientClass in [("meta", MetaAdsClient), ("ga4", GA4Client)]:
        cached = cache_repo.get_cached(client_id, service, ts_key)
        if cached:
            result[service] = cached.get("daily", [])
            continue
        if not client_repo.has_credentials(client_id, service):
            continue
        try:
            creds  = client_repo.get_credentials(client_id, service)
            client = ClientClass(client_id, creds)
            daily  = client.fetch_timeseries(date_from, date_to)
            ttl    = _ttl(date_from, date_to, service)
            cache_repo.set_cache(client_id, service, ts_key, {"daily": daily}, ttl)
            result[service] = daily
        except Exception:
            result[service] = []

    return result
