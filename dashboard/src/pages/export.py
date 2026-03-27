"""Export page: CSV and PDF downloads."""
from datetime import date

import streamlit as st

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db import client_repo, target_repo
from src.apis.aggregator import build_client_kpis
from src.components.date_selector import date_range_selector
from src.components.export_engine import export_csv, export_pdf


def render():
    st.title("Export")

    clients = client_repo.list_clients()
    if not clients:
        st.info("Keine Kunden vorhanden.")
        return

    names  = [c["name"] for c in clients]
    idx    = st.selectbox("Kunde", range(len(names)), format_func=lambda i: names[i], key="exp_client")
    client = clients[idx]

    date_from, date_to = date_range_selector("exp")

    today  = date.today()
    month  = f"{today.year}-{today.month:02d}"
    targets = target_repo.get_targets(client["id"], month)
    monthly_budget = targets.get("meta_spend_budget", {}).get("value", 0.0)

    if st.button("Daten laden", type="primary"):
        with st.spinner("Laden…"):
            kpis = build_client_kpis(client["id"], date_from, date_to, monthly_budget=monthly_budget)
        st.session_state["exp_kpis"]    = kpis
        st.session_state["exp_targets"] = targets
        st.success("Daten geladen.")

    kpis    = st.session_state.get("exp_kpis")
    tgt_map = st.session_state.get("exp_targets", {})

    if kpis:
        col_csv, col_pdf = st.columns(2)
        with col_csv:
            csv_bytes = export_csv(kpis, client["name"], date_from, date_to)
            st.download_button(
                "CSV herunterladen",
                data=csv_bytes,
                file_name=f"{client['name'].replace(' ','_')}_{date_from}_{date_to}.csv",
                mime="text/csv",
            )
        with col_pdf:
            try:
                pdf_bytes = export_pdf(kpis, tgt_map, client["name"], date_from, date_to)
                st.download_button(
                    "PDF herunterladen",
                    data=pdf_bytes,
                    file_name=f"{client['name'].replace(' ','_')}_{date_from}_{date_to}.pdf",
                    mime="application/pdf",
                )
            except RuntimeError as e:
                st.warning(str(e))
