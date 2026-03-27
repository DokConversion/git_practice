"""Client detail page: tabbed deep-dive per client."""
from datetime import date

import streamlit as st

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db import client_repo, target_repo
from src.db.cache_repo import invalidate_client
from src.apis.aggregator import build_client_kpis, build_timeseries
from src.components.traffic_light import compute_status, STATUS_EMOJI, KPIStatus
from src.components.kpi_card import kpi_card
from src.components.date_selector import date_range_selector
from src.components import charts


def render(client_id: int | None = None):
    clients = client_repo.list_clients()
    if not clients:
        st.info("Bitte zuerst unter **Einstellungen** einen Kunden anlegen.")
        return

    # Client selector in sidebar
    names   = [c["name"] for c in clients]
    default = next((i for i, c in enumerate(clients) if c["id"] == client_id), 0)
    idx     = st.sidebar.selectbox("Kunde", range(len(names)),
                                   format_func=lambda i: names[i],
                                   index=default, key="detail_client_sel")
    client  = clients[idx]

    date_from, date_to = date_range_selector("cd")

    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.title(f"{client['name']}")
    with col_btn:
        force = st.button("Aktualisieren", key="detail_refresh")
        if force:
            invalidate_client(client["id"])

    today      = date.today()
    month      = f"{today.year}-{today.month:02d}"
    targets    = target_repo.get_targets(client["id"], month)
    monthly_budget = targets.get("meta_spend_budget", {}).get("value", 0.0)

    cache_key = f"kpis_{client['id']}_{date_from}_{date_to}"
    if force or cache_key not in st.session_state:
        with st.spinner("Daten werden geladen…"):
            kpis = build_client_kpis(client["id"], date_from, date_to,
                                      force_refresh=force, monthly_budget=monthly_budget)
            st.session_state[cache_key] = kpis
    else:
        kpis = st.session_state[cache_key]

    ts_key = f"ts_{client['id']}_{date_from}_{date_to}"
    if force or ts_key not in st.session_state:
        ts = build_timeseries(client["id"], date_from, date_to)
        st.session_state[ts_key] = ts
    else:
        ts = st.session_state[ts_key]

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_meta, tab_ga4, tab_crm, tab_combined, tab_targets = st.tabs([
        "Meta Ads", "GA4 Website", "CRM Revenue", "Combined", "Zielwerte",
    ])

    with tab_meta:
        _tab_meta(kpis, targets, ts.get("meta", []), monthly_budget)

    with tab_ga4:
        _tab_ga4(kpis, ts.get("ga4", []))

    with tab_crm:
        _tab_crm(kpis, targets)

    with tab_combined:
        _tab_combined(kpis, targets)

    with tab_targets:
        _tab_targets(client["id"], month, targets)


# ── Tab renderers ──────────────────────────────────────────────────────────────

def _tab_meta(kpis, targets, daily, monthly_budget):
    st.subheader("Meta Ads KPIs")
    cols = st.columns(5)
    _card_in(cols[0], "Spend (€)",    kpis, "meta_spend",  targets, "meta_spend_budget", prefix="€", dec=0)
    _card_in(cols[1], "Leads",        kpis, "meta_leads",  targets, "meta_leads",        dec=0)
    _card_in(cols[2], "CPL (€)",      kpis, "meta_cpl",    targets, "meta_cpl",          prefix="€")
    _card_in(cols[3], "CTR (%)",      kpis, "meta_ctr",    targets, None,                suffix="%")
    _card_in(cols[4], "Meta ROAS",    kpis, "meta_roas",   targets, "meta_roas",         suffix="x")

    cols2 = st.columns(4)
    _card_in(cols2[0], "Impressions",  kpis, "meta_impressions", targets, None, dec=0)
    _card_in(cols2[1], "Reach",        kpis, "meta_reach",       targets, None, dec=0)
    _card_in(cols2[2], "CPM (€)",      kpis, "meta_cpm",         targets, None, prefix="€")
    _card_in(cols2[3], "CPC (€)",      kpis, "meta_cpc",         targets, None, prefix="€")

    st.divider()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.plotly_chart(charts.spend_bar_chart(daily), use_container_width=True)
    with col_b:
        spend = kpis.get("meta_spend", 0.0)
        pacing = kpis.get("budget_pacing_pct", 0.0)
        if monthly_budget:
            st.plotly_chart(charts.budget_pacing_gauge(pacing, monthly_budget, spend), use_container_width=True)
        else:
            st.info("Budget-Pacing: Bitte monatliches Budget in Zielwerten hinterlegen.")

    st.plotly_chart(charts.leads_cpl_chart(daily), use_container_width=True)


def _tab_ga4(kpis, daily_ga4):
    st.subheader("Google Analytics 4")
    cols = st.columns(4)
    with cols[0]: kpi_card("Sessions",         kpis.get("ga4_sessions", 0),          decimals=0)
    with cols[1]: kpi_card("Users",             kpis.get("ga4_users", 0),             decimals=0)
    with cols[2]: kpi_card("Engagement Rate",   kpis.get("ga4_engagement_rate", 0),   suffix="%")
    with cols[3]: kpi_card("Ø Session Dauer (s)", kpis.get("ga4_avg_session_duration", 0))

    cols2 = st.columns(2)
    with cols2[0]: kpi_card("Conversions",      kpis.get("ga4_conversions", 0),       decimals=0)
    with cols2[1]: kpi_card("Conv.-Rate",        kpis.get("ga4_conversion_rate", 0),  suffix="%")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(charts.sessions_trend_chart(daily_ga4), use_container_width=True)
    with col_b:
        sources = kpis.get("ga4_top_sources", [])
        if sources:
            st.plotly_chart(charts.traffic_sources_chart(sources), use_container_width=True)
        else:
            st.info("Keine Traffic-Quellen verfügbar.")


def _tab_crm(kpis, targets):
    st.subheader("Close CRM")
    cols = st.columns(4)
    _card_in(cols[0], "Neue Leads",     kpis, "crm_new_leads",     targets, "meta_leads",  dec=0)
    _card_in(cols[1], "Gewon. Deals",   kpis, "crm_won_deals",     targets, "crm_won_deals", dec=0)
    _card_in(cols[2], "Revenue (€)",    kpis, "crm_revenue",       targets, "crm_revenue",  prefix="€", dec=0)
    _card_in(cols[3], "Pipeline (€)",   kpis, "crm_pipeline_value",targets, None,           prefix="€", dec=0)

    cols2 = st.columns(2)
    with cols2[0]: kpi_card("Lead→Close Rate", kpis.get("crm_lead_to_close_rate", 0), suffix="%")
    with cols2[1]: kpi_card("Ø Deal-Wert (€)", kpis.get("crm_avg_deal_value", 0),     prefix="€")

    st.divider()
    st.plotly_chart(charts.pipeline_funnel(
        kpis.get("crm_new_leads", 0),
        kpis.get("crm_open_opportunities", 0),
        kpis.get("crm_won_deals", 0),
    ), use_container_width=True)


def _tab_combined(kpis, targets):
    st.subheader("Combined Metrics")
    cols = st.columns(3)
    _card_in(cols[0], "Gesamt-ROAS",   kpis, "combined_roas", targets, "combined_roas", suffix="x")
    _card_in(cols[1], "CAC (€)",       kpis, "combined_cac",  targets, "combined_cac",  prefix="€")
    with cols[2]:
        pacing = kpis.get("budget_pacing_pct", 0.0)
        status_str = "🟢 On Pace" if 0.85 <= pacing <= 1.15 else \
                     "🟡 Leicht ab" if 0.70 <= pacing <= 1.30 else "🔴 Kritisch"
        kpi_card("Budget-Pacing", pacing, suffix="x", help_text=f"1.0 = perfektes Tempo. {status_str}")

    st.divider()
    st.plotly_chart(charts.roas_components_chart(
        kpis.get("meta_spend", 0),
        kpis.get("crm_revenue", 0),
    ), use_container_width=True)


def _tab_targets(client_id, month, targets):
    st.subheader(f"Zielwerte – {month}")
    st.info("Zum Bearbeiten: Einstellungen → Zielwerte")

    rows = []
    for kpi_key, (label, _) in target_repo.KPI_DEFINITIONS.items():
        tgt = targets.get(kpi_key, {})
        rows.append({
            "KPI":     label,
            "Ziel":    tgt.get("value", "–"),
            "Richtung": tgt.get("direction", "–"),
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Helper ────────────────────────────────────────────────────────────────────

def _card_in(col, label, kpis, kpi_key, targets, tgt_key, prefix="", suffix="", dec=2):
    with col:
        actual = kpis.get(kpi_key, 0.0)
        tgt_entry = targets.get(tgt_key) if tgt_key else None
        tgt_val   = tgt_entry.get("value")   if tgt_entry else None
        direction = tgt_entry.get("direction", "maximize") if tgt_entry else "maximize"
        status    = compute_status(actual, tgt_val, direction) if tgt_val else KPIStatus.UNKNOWN
        kpi_card(label, actual, target=tgt_val, status=status, prefix=prefix, suffix=suffix, decimals=dec)
