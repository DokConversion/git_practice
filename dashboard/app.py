"""
Performance Marketing KPI Dashboard
Run: streamlit run dashboard/app.py
"""
import sys
import os

# Ensure imports resolve from dashboard/ root
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── One-time initialisation (cached per process) ───────────────────────────────
@st.cache_resource
def _init():
    from src.db.schema import run_migrations
    from src.db.cache_repo import purge_expired
    run_migrations()
    purge_expired()

_init()

# ── Navigation ─────────────────────────────────────────────────────────────────
from src.pages import overview, client_detail, settings, export

PAGES = {
    "Übersicht":     overview,
    "Client Detail": client_detail,
    "Einstellungen": settings,
    "Export":        export,
}

st.sidebar.title("📊 Performance Dashboard")
st.sidebar.divider()

nav_default = list(PAGES.keys()).index(
    st.session_state.get("nav_page", "Übersicht")
)
page_name = st.sidebar.radio("Navigation", list(PAGES.keys()), index=nav_default)
st.session_state["nav_page"] = page_name

st.sidebar.divider()
st.sidebar.caption("Powered by Meta Ads · GA4 · Close CRM")

# ── Render selected page ───────────────────────────────────────────────────────
module = PAGES[page_name]

if page_name == "Client Detail":
    client_id = st.session_state.get("active_client_id")
    module.render(client_id)
else:
    module.render()
