"""Overview page: all clients at a glance with traffic-light KPI cards."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import streamlit as st
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db import client_repo, target_repo
from src.db.cache_repo import invalidate_client
from src.apis.aggregator import build_client_kpis
from src.components.traffic_light import compute_status, worst_status, STATUS_EMOJI, STATUS_COLORS, KPIStatus
from src.components.date_selector import date_range_selector


def render():
    st.title("Übersicht – alle Kunden")

    date_from, date_to = date_range_selector("ov")

    col_refresh, col_month = st.columns([1, 2])
    with col_refresh:
        force = st.button("Alles aktualisieren", type="primary")

    today  = date.today()
    month  = f"{today.year}-{today.month:02d}"

    clients = client_repo.list_clients(active_only=True)
    if not clients:
        st.info("Noch keine aktiven Kunden. Bitte unter **Einstellungen** anlegen.")
        return

    # Load all clients in parallel
    with st.spinner("Daten werden geladen…"):
        results = _load_all(clients, date_from, date_to, month, force_refresh=force)

    # ── Client cards grid ─────────────────────────────────────────────────────
    cols = st.columns(min(len(clients), 3))
    for i, client in enumerate(clients):
        kpis    = results.get(client["id"], {})
        targets = target_repo.get_targets(client["id"], month)
        with cols[i % 3]:
            _client_card(client, kpis, targets)

    # ── Summary table ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Vergleichstabelle")
    _summary_table(clients, results, month)


def _load_all(clients, date_from, date_to, month, force_refresh=False) -> dict:
    def load_one(client):
        targets = target_repo.get_targets(client["id"], month)
        monthly_budget = targets.get("meta_spend_budget", {}).get("value", 0.0)
        cache_key = f"kpis_{client['id']}_{date_from}_{date_to}"
        if not force_refresh and cache_key in st.session_state:
            return client["id"], st.session_state[cache_key]
        if force_refresh:
            invalidate_client(client["id"])
        kpis = build_client_kpis(client["id"], date_from, date_to,
                                  force_refresh=force_refresh, monthly_budget=monthly_budget)
        st.session_state[cache_key] = kpis
        return client["id"], kpis

    results = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(load_one, c): c for c in clients}
        for future in as_completed(futures):
            try:
                cid, kpis = future.result()
                results[cid] = kpis
            except Exception as exc:
                cid = futures[future]["id"]
                results[cid] = {"_error": str(exc)}
    return results


def _client_card(client: dict, kpis: dict, targets: dict):
    if "_error" in kpis:
        st.error(f"**{client['name']}**: {kpis['_error']}")
        return

    kpi_statuses = _compute_statuses(kpis, targets)
    overall      = worst_status(list(kpi_statuses.values()))
    color        = STATUS_COLORS[overall]
    emoji        = STATUS_EMOJI[overall]

    st.markdown(
        f"""
        <div style="border:2px solid {color}; border-radius:8px; padding:14px; margin-bottom:12px;">
            <div style="font-size:16px; font-weight:700; margin-bottom:10px;">{emoji} {client['name']}</div>
        """,
        unsafe_allow_html=True,
    )

    rows = [
        ("Spend",    kpis.get("meta_spend", 0),  "meta_spend_budget", "€", 0),
        ("Leads",    kpis.get("meta_leads", 0),   "meta_leads",        "",  0),
        ("CPL",      kpis.get("meta_cpl", 0),     "meta_cpl",          "€", 2),
        ("Revenue",  kpis.get("crm_revenue", 0),  "crm_revenue",       "€", 0),
        ("ROAS",     kpis.get("combined_roas", 0), "combined_roas",    "x", 2),
    ]
    for label, val, tgt_key, suffix, dec in rows:
        tgt    = targets.get(tgt_key, {}).get("value")
        dire   = targets.get(tgt_key, {}).get("direction", "maximize")
        status = kpi_statuses.get(tgt_key, KPIStatus.UNKNOWN)
        s_emoji = STATUS_EMOJI[status]
        if isinstance(val, float):
            val_str = f"{val:,.{dec}f}{suffix}"
        else:
            val_str = f"{val:,}{suffix}"
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:2px 0;'>"
            f"<span style='color:#aaa;font-size:13px;'>{label}</span>"
            f"<span style='font-size:13px;'>{val_str} {s_emoji}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if st.button("Details →", key=f"detail_{client['id']}"):
        st.session_state["active_client_id"] = client["id"]
        st.session_state["nav_page"] = "Client Detail"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _compute_statuses(kpis: dict, targets: dict) -> dict[str, KPIStatus]:
    mappings = {
        "meta_leads":       ("meta_leads",       "maximize"),
        "meta_cpl":         ("meta_cpl",         "minimize"),
        "meta_roas":        ("meta_roas",        "maximize"),
        "combined_roas":    ("combined_roas",    "maximize"),
        "combined_cac":     ("combined_cac",     "minimize"),
        "crm_revenue":      ("crm_revenue",      "maximize"),
        "crm_won_deals":    ("crm_won_deals",    "maximize"),
        "meta_spend_budget":("meta_spend",       "pace"),
    }
    statuses = {}
    for tgt_key, (kpi_key, default_dir) in mappings.items():
        tgt_entry = targets.get(tgt_key)
        tgt_val   = tgt_entry.get("value") if tgt_entry else None
        direction = tgt_entry.get("direction", default_dir) if tgt_entry else default_dir
        actual    = kpis.get(kpi_key, 0.0)
        statuses[tgt_key] = compute_status(actual, tgt_val, direction)
    return statuses


def _summary_table(clients, results, month):
    rows = []
    for c in clients:
        kpis    = results.get(c["id"], {})
        targets = target_repo.get_targets(c["id"], month)
        overall = worst_status(list(_compute_statuses(kpis, targets).values()))
        rows.append({
            "Kunde":    c["name"],
            "Status":   STATUS_EMOJI[overall],
            "Spend €":  kpis.get("meta_spend", 0),
            "Leads":    kpis.get("meta_leads", 0),
            "CPL €":    kpis.get("meta_cpl", 0),
            "Revenue €":kpis.get("crm_revenue", 0),
            "ROAS":     kpis.get("combined_roas", 0),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
