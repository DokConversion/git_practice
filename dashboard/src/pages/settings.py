"""Settings page: manage clients, API credentials, monthly targets."""
import streamlit as st
from datetime import date

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db import client_repo, target_repo
from src.db.cache_repo import invalidate_client


def render():
    st.title("Einstellungen")

    tab_clients, tab_creds, tab_targets = st.tabs(["Kunden", "API-Zugangsdaten", "Zielwerte"])

    with tab_clients:
        _clients_tab()

    with tab_creds:
        _credentials_tab()

    with tab_targets:
        _targets_tab()


# ── Clients ────────────────────────────────────────────────────────────────────

def _clients_tab():
    st.subheader("Kunden verwalten")

    clients = client_repo.list_clients(active_only=False)
    if clients:
        for c in clients:
            with st.expander(f"{'✅' if c['is_active'] else '⏸️'} {c['name']}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    new_name = st.text_input("Name", value=c["name"], key=f"cname_{c['id']}")
                with col2:
                    is_active = st.checkbox("Aktiv", value=bool(c["is_active"]), key=f"cactive_{c['id']}")
                with col3:
                    st.write("")
                    if st.button("Speichern", key=f"csave_{c['id']}"):
                        client_repo.update_client(c["id"], new_name, is_active)
                        st.success("Gespeichert")
                        st.rerun()
                if st.button("Löschen", key=f"cdel_{c['id']}", type="secondary"):
                    client_repo.delete_client(c["id"])
                    st.warning(f"Kunde '{c['name']}' gelöscht.")
                    st.rerun()
    else:
        st.info("Noch keine Kunden angelegt.")

    st.divider()
    st.subheader("Neuen Kunden anlegen")
    new_name = st.text_input("Kundenname", key="new_client_name")
    if st.button("Anlegen", type="primary"):
        if new_name.strip():
            client_repo.create_client(new_name.strip())
            st.success(f"Kunde '{new_name}' angelegt.")
            st.rerun()
        else:
            st.error("Bitte einen Namen eingeben.")


# ── Credentials ────────────────────────────────────────────────────────────────

def _credentials_tab():
    st.subheader("API-Zugangsdaten")

    clients = client_repo.list_clients()
    if not clients:
        st.info("Bitte zuerst einen Kunden anlegen.")
        return

    client = _pick_client(clients, key="cred_client")
    if not client:
        return

    service = st.selectbox("Service", ["meta", "ga4", "close_crm"], key="cred_service",
                           format_func=lambda s: {"meta": "Meta Ads", "ga4": "Google Analytics 4",
                                                   "close_crm": "Close CRM"}[s])

    existing = client_repo.get_credentials(client["id"], service)
    fields   = _credential_fields(service)

    st.markdown(f"**{service.upper()} Credentials** für _{client['name']}_")
    values = {}
    for key, label, help_text, is_secret in fields:
        default = existing.get(key, "")
        if is_secret and default:
            default = "••••••••"
        values[key] = st.text_input(label, value=default if not is_secret else "",
                                    type="password" if is_secret else "default",
                                    help=help_text, key=f"cred_{service}_{key}")

    if st.button("Credentials speichern", type="primary"):
        for key, _, _, is_secret in fields:
            val = values[key].strip()
            if val and val != "••••••••":
                client_repo.save_credential(client["id"], service, key, val)
        invalidate_client(client["id"])
        st.success("Credentials gespeichert und Cache geleert.")


def _credential_fields(service: str) -> list[tuple]:
    """Returns list of (key, label, help, is_secret)."""
    if service == "meta":
        return [
            ("ad_account_id", "Ad Account ID", "Format: act_123456789", False),
            ("access_token",  "Access Token",  "System User Token mit ads_read", True),
            ("app_id",        "App ID",        "Meta App ID (optional)", False),
            ("app_secret",    "App Secret",    "Meta App Secret (optional)", True),
        ]
    elif service == "ga4":
        return [
            ("property_id",         "Property ID",         "Format: properties/123456789", False),
            ("service_account_json", "Service Account JSON", "Vollständiges JSON des Service Accounts", True),
        ]
    else:  # close_crm
        return [
            ("api_key",     "API Key",     "Close CRM API Key", True),
            ("pipeline_id", "Pipeline ID", "Pipeline ID zum Filtern (optional)", False),
        ]


# ── Targets ───────────────────────────────────────────────────────────────────

def _targets_tab():
    st.subheader("Monatliche Zielwerte")

    clients = client_repo.list_clients()
    if not clients:
        st.info("Bitte zuerst einen Kunden anlegen.")
        return

    client = _pick_client(clients, key="target_client")
    if not client:
        return

    today = date.today()
    month_str = st.text_input("Monat (YYYY-MM)", value=f"{today.year}-{today.month:02d}", key="target_month")

    existing = target_repo.get_targets(client["id"], month_str)
    st.write("")

    updated = {}
    for kpi_key, (label, default_direction) in target_repo.KPI_DEFINITIONS.items():
        current = existing.get(kpi_key, {})
        col1, col2 = st.columns([3, 1])
        with col1:
            val = st.number_input(
                label, value=float(current.get("value") or 0.0),
                min_value=0.0, step=1.0, format="%.2f",
                key=f"target_{kpi_key}",
            )
        with col2:
            direction = st.selectbox(
                "Richtung", ["minimize", "maximize", "pace"],
                index=["minimize", "maximize", "pace"].index(current.get("direction", default_direction)),
                key=f"dir_{kpi_key}",
                label_visibility="collapsed",
            )
        updated[kpi_key] = (val, direction)

    if st.button("Zielwerte speichern", type="primary"):
        for kpi_key, (val, direction) in updated.items():
            if val > 0:
                target_repo.set_target(client["id"], month_str, kpi_key, val, direction)
            else:
                target_repo.delete_target(client["id"], month_str, kpi_key)
        st.success(f"Zielwerte für {month_str} gespeichert.")


# ── Helper ────────────────────────────────────────────────────────────────────

def _pick_client(clients: list[dict], key: str) -> dict | None:
    names = [c["name"] for c in clients]
    idx   = st.selectbox("Kunde", range(len(names)), format_func=lambda i: names[i], key=key)
    return clients[idx] if clients else None
