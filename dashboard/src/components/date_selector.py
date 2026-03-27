import streamlit as st
from datetime import date, timedelta
from calendar import monthrange


def date_range_selector(key_prefix: str = "dr") -> tuple[date, date]:
    """
    Renders a date-range selector in the Streamlit sidebar.
    Returns (date_from, date_to).
    """
    presets = [
        "Heute",
        "Gestern",
        "Letzte 7 Tage",
        "Letzte 30 Tage",
        "Dieser Monat",
        "Individuell",
    ]
    choice = st.sidebar.selectbox("Zeitraum", presets, key=f"{key_prefix}_preset")

    today = date.today()

    if choice == "Heute":
        return today, today
    elif choice == "Gestern":
        y = today - timedelta(days=1)
        return y, y
    elif choice == "Letzte 7 Tage":
        return today - timedelta(days=6), today
    elif choice == "Letzte 30 Tage":
        return today - timedelta(days=29), today
    elif choice == "Dieser Monat":
        return date(today.year, today.month, 1), today
    else:  # Individuell
        col1, col2 = st.sidebar.columns(2)
        with col1:
            d_from = st.date_input("Von", value=today - timedelta(days=29), key=f"{key_prefix}_from")
        with col2:
            d_to = st.date_input("Bis", value=today, key=f"{key_prefix}_to")
        return d_from, d_to
