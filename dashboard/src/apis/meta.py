"""
Meta Marketing API client.

Required credentials:
    ad_account_id  e.g. "act_123456789"
    access_token   System User token with ads_read permission
"""
from datetime import date
from src.apis.base import APIClient, APIError


class MetaAdsClient(APIClient):
    BASE_URL = "https://graph.facebook.com/v19.0"

    def fetch(self, date_from: date, date_to: date) -> dict:
        insights = self._get_insights(date_from, date_to)
        budget   = self._get_budget()
        return {**insights, **budget}

    def fetch_timeseries(self, date_from: date, date_to: date) -> list[dict]:
        """Daily breakdown for chart rendering."""
        return self._get_insights(date_from, date_to, time_increment=1).get("daily", [])

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_insights(self, date_from: date, date_to: date, time_increment: int = 0) -> dict:
        account_id = self.credentials["ad_account_id"]
        token      = self.credentials["access_token"]

        fields = (
            "spend,impressions,reach,frequency,clicks,ctr,cpm,cpc,"
            "actions,action_values,cost_per_action_type"
        )
        params = {
            "access_token":   token,
            "fields":         fields,
            "time_range":     f'{{"since":"{date_from}","until":"{date_to}"}}',
            "time_increment": time_increment,
            "limit":          500,
        }
        resp = self._request("GET", f"{self.BASE_URL}/{account_id}/insights", params=params)
        data = resp.json().get("data", [])

        if time_increment == 1:
            return {"daily": [self._parse_row(r) for r in data]}

        if not data:
            return self._empty_insights()

        return self._parse_row(data[0])

    def _get_budget(self) -> dict:
        account_id = self.credentials["ad_account_id"]
        token      = self.credentials["access_token"]
        params = {
            "access_token": token,
            "fields": "amount_spent,spend_cap,balance",
        }
        try:
            resp = self._request("GET", f"{self.BASE_URL}/{account_id}", params=params)
            d = resp.json()
            spend_cap = float(d.get("spend_cap") or 0) / 100  # Meta returns cents
            amount_spent = float(d.get("amount_spent") or 0) / 100
            return {
                "meta_budget_cap":       spend_cap,
                "meta_budget_remaining": max(spend_cap - amount_spent, 0),
            }
        except APIError:
            return {"meta_budget_cap": 0.0, "meta_budget_remaining": 0.0}

    def _parse_row(self, row: dict) -> dict:
        actions = row.get("actions") or []
        action_values = row.get("action_values") or []

        leads     = self._action_value(actions, ["lead", "onsite_conversion.lead_grouped"])
        purchases = self._action_value(actions, ["purchase", "offsite_conversion.fb_pixel_purchase"])
        revenue   = self._action_value(action_values, ["purchase", "offsite_conversion.fb_pixel_purchase"])

        spend = float(row.get("spend") or 0)
        return {
            "meta_spend":       spend,
            "meta_impressions": int(row.get("impressions") or 0),
            "meta_reach":       int(row.get("reach") or 0),
            "meta_frequency":   float(row.get("frequency") or 0),
            "meta_clicks":      int(row.get("clicks") or 0),
            "meta_ctr":         float(row.get("ctr") or 0),
            "meta_cpm":         float(row.get("cpm") or 0),
            "meta_cpc":         float(row.get("cpc") or 0),
            "meta_leads":       int(leads),
            "meta_cpl":         round(spend / leads, 2) if leads else 0.0,
            "meta_purchases":   int(purchases),
            "meta_revenue":     float(revenue),
            "meta_roas":        round(revenue / spend, 2) if spend else 0.0,
            "date":             row.get("date_start", ""),
        }

    def _action_value(self, actions: list, action_types: list) -> float:
        for a in actions:
            if a.get("action_type") in action_types:
                return float(a.get("value") or 0)
        return 0.0

    def _empty_insights(self) -> dict:
        return {
            "meta_spend": 0.0, "meta_impressions": 0, "meta_reach": 0,
            "meta_frequency": 0.0, "meta_clicks": 0, "meta_ctr": 0.0,
            "meta_cpm": 0.0, "meta_cpc": 0.0, "meta_leads": 0,
            "meta_cpl": 0.0, "meta_purchases": 0, "meta_revenue": 0.0,
            "meta_roas": 0.0,
        }
