"""
Close CRM REST API client.
Docs: https://developer.close.com/

Required credentials:
    api_key      Close API key (HTTP Basic Auth username, password empty)
    pipeline_id  Close pipeline ID to filter opportunities
"""
from datetime import date
from src.apis.base import APIClient, APIError


class CloseCRMClient(APIClient):
    BASE_URL = "https://api.close.com/api/v1"

    def _auth(self) -> tuple:
        return (self.credentials["api_key"], "")

    def fetch(self, date_from: date, date_to: date) -> dict:
        leads       = self._get_new_leads(date_from, date_to)
        pipeline    = self._get_pipeline()
        won         = self._get_won_deals(date_from, date_to)
        rate        = won["crm_won_deals"] / leads["crm_new_leads"] if leads["crm_new_leads"] else 0.0
        return {
            **leads,
            **pipeline,
            **won,
            "crm_lead_to_close_rate": round(rate * 100, 1),
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _paginate(self, endpoint: str, params: dict) -> list[dict]:
        results = []
        params = {**params, "_limit": 100, "_skip": 0}
        while True:
            resp = self._request("GET", f"{self.BASE_URL}{endpoint}", params=params, auth=self._auth())
            data = resp.json()
            results.extend(data.get("data", []))
            if not data.get("has_more"):
                break
            params["_skip"] += 100
        return results

    def _get_new_leads(self, date_from: date, date_to: date) -> dict:
        try:
            params = {
                "query": f'date_created >= "{date_from}" date_created <= "{date_to}"',
                "_fields": "id",
            }
            items = self._paginate("/lead/", params)
            return {"crm_new_leads": len(items)}
        except APIError:
            return {"crm_new_leads": 0}

    def _get_pipeline(self) -> dict:
        try:
            pipeline_id = self.credentials.get("pipeline_id", "")
            params = {"status_type": "active", "_fields": "value,value_period,value_currency"}
            if pipeline_id:
                params["pipeline_id"] = pipeline_id
            items = self._paginate("/opportunity/", params)
            total_value = sum(float(i.get("value") or 0) / 100 for i in items)
            return {
                "crm_open_opportunities": len(items),
                "crm_pipeline_value":     round(total_value, 2),
            }
        except APIError:
            return {"crm_open_opportunities": 0, "crm_pipeline_value": 0.0}

    def _get_won_deals(self, date_from: date, date_to: date) -> dict:
        try:
            pipeline_id = self.credentials.get("pipeline_id", "")
            params = {
                "status_type": "won",
                "date_won__gte": str(date_from),
                "date_won__lte": str(date_to),
                "_fields": "value,value_period",
            }
            if pipeline_id:
                params["pipeline_id"] = pipeline_id
            items = self._paginate("/opportunity/", params)
            total_revenue = sum(float(i.get("value") or 0) / 100 for i in items)
            count = len(items)
            return {
                "crm_won_deals":    count,
                "crm_revenue":      round(total_revenue, 2),
                "crm_avg_deal_value": round(total_revenue / count, 2) if count else 0.0,
            }
        except APIError:
            return {"crm_won_deals": 0, "crm_revenue": 0.0, "crm_avg_deal_value": 0.0}
