import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db.schema import get_connection

# KPI keys that can have targets, with their default direction
KPI_DEFINITIONS = {
    "meta_spend_budget": ("Monatliches Meta Budget (€)", "pace"),
    "meta_cpl":          ("CPL – Cost per Lead (€)", "minimize"),
    "meta_roas":         ("Meta ROAS", "maximize"),
    "meta_leads":        ("Meta Leads (Anzahl)", "maximize"),
    "combined_roas":     ("Gesamt-ROAS (Revenue/Spend)", "maximize"),
    "combined_cac":      ("CAC – Customer Acquisition Cost (€)", "minimize"),
    "crm_revenue":       ("Umsatz / Revenue (€)", "maximize"),
    "crm_won_deals":     ("Gewonnene Deals (Anzahl)", "maximize"),
    "ga4_sessions":      ("GA4 Sessions", "maximize"),
    "ga4_conversion_rate": ("GA4 Conversion Rate (%)", "maximize"),
}


def get_targets(client_id: int, month: str) -> dict[str, dict]:
    """Return {kpi_key: {target_value, target_direction}} for a given month."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT kpi_key, target_value, target_direction FROM kpi_targets WHERE client_id=? AND month=?",
            (client_id, month),
        ).fetchall()
        return {r["kpi_key"]: {"value": r["target_value"], "direction": r["target_direction"]} for r in rows}
    finally:
        conn.close()


def set_target(client_id: int, month: str, kpi_key: str, value: float, direction: str):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO kpi_targets (client_id, month, kpi_key, target_value, target_direction)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(client_id, month, kpi_key)
               DO UPDATE SET target_value=excluded.target_value, target_direction=excluded.target_direction""",
            (client_id, month, kpi_key, value, direction),
        )
        conn.commit()
    finally:
        conn.close()


def delete_target(client_id: int, month: str, kpi_key: str):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM kpi_targets WHERE client_id=? AND month=? AND kpi_key=?",
            (client_id, month, kpi_key),
        )
        conn.commit()
    finally:
        conn.close()


def get_target_history(client_id: int, kpi_key: str, months: int = 6) -> list[dict]:
    """Return last N months of target + (future: actual) for a KPI."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT month, target_value, target_direction FROM kpi_targets
               WHERE client_id=? AND kpi_key=?
               ORDER BY month DESC LIMIT ?""",
            (client_id, kpi_key, months),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
