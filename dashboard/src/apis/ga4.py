"""
Google Analytics 4 Data API client.

Required credentials:
    property_id          e.g. "properties/123456789"
    service_account_json Full JSON string of service account key
"""
import json
from datetime import date
from src.apis.base import APIClient, APIError


class GA4Client(APIClient):

    def fetch(self, date_from: date, date_to: date) -> dict:
        client = self._build_client()
        summary = self._get_summary(client, date_from, date_to)
        sources = self._get_top_sources(client, date_from, date_to)
        return {**summary, "ga4_top_sources": sources}

    def fetch_timeseries(self, date_from: date, date_to: date) -> list[dict]:
        client = self._build_client()
        return self._get_daily(client, date_from, date_to)

    # ── Private ───────────────────────────────────────────────────────────────

    def _build_client(self):
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            sa_json = self.credentials.get("service_account_json", "{}")
            sa_info = json.loads(sa_json)
            creds   = service_account.Credentials.from_service_account_info(
                sa_info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            return BetaAnalyticsDataClient(credentials=creds)
        except Exception as exc:
            raise APIError(f"GA4 client build failed: {exc}")

    def _run_report(self, client, date_from: date, date_to: date, metrics: list, dimensions: list = None):
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Metric, Dimension
        )
        property_id = self.credentials["property_id"]
        req = RunReportRequest(
            property=property_id,
            date_ranges=[DateRange(start_date=str(date_from), end_date=str(date_to))],
            metrics=[Metric(name=m) for m in metrics],
            dimensions=[Dimension(name=d) for d in (dimensions or [])],
        )
        return client.run_report(req)

    def _get_summary(self, client, date_from: date, date_to: date) -> dict:
        try:
            resp = self._run_report(client, date_from, date_to, [
                "sessions", "totalUsers", "newUsers",
                "engagementRate", "averageSessionDuration",
                "conversions", "sessionConversionRate",
            ])
            if not resp.rows:
                return self._empty_summary()
            r = resp.rows[0]
            vals = [v.value for v in r.metric_values]
            return {
                "ga4_sessions":             int(vals[0] or 0),
                "ga4_users":                int(vals[1] or 0),
                "ga4_new_users":            int(vals[2] or 0),
                "ga4_engagement_rate":      round(float(vals[3] or 0) * 100, 1),
                "ga4_avg_session_duration": round(float(vals[4] or 0), 1),
                "ga4_conversions":          int(vals[5] or 0),
                "ga4_conversion_rate":      round(float(vals[6] or 0) * 100, 2),
            }
        except Exception as exc:
            raise APIError(f"GA4 summary failed: {exc}")

    def _get_top_sources(self, client, date_from: date, date_to: date, top_n: int = 5) -> list[dict]:
        try:
            resp = self._run_report(
                client, date_from, date_to,
                metrics=["sessions", "conversions"],
                dimensions=["sessionDefaultChannelGroup"],
            )
            rows = []
            for r in resp.rows:
                rows.append({
                    "channel":     r.dimension_values[0].value,
                    "sessions":    int(r.metric_values[0].value or 0),
                    "conversions": int(r.metric_values[1].value or 0),
                })
            rows.sort(key=lambda x: x["sessions"], reverse=True)
            return rows[:top_n]
        except Exception:
            return []

    def _get_daily(self, client, date_from: date, date_to: date) -> list[dict]:
        try:
            resp = self._run_report(
                client, date_from, date_to,
                metrics=["sessions", "conversions"],
                dimensions=["date"],
            )
            rows = []
            for r in resp.rows:
                raw = r.dimension_values[0].value  # YYYYMMDD
                rows.append({
                    "date":        f"{raw[:4]}-{raw[4:6]}-{raw[6:]}",
                    "sessions":    int(r.metric_values[0].value or 0),
                    "conversions": int(r.metric_values[1].value or 0),
                })
            rows.sort(key=lambda x: x["date"])
            return rows
        except Exception:
            return []

    def _empty_summary(self) -> dict:
        return {
            "ga4_sessions": 0, "ga4_users": 0, "ga4_new_users": 0,
            "ga4_engagement_rate": 0.0, "ga4_avg_session_duration": 0.0,
            "ga4_conversions": 0, "ga4_conversion_rate": 0.0,
        }
