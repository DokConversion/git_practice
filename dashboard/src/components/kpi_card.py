import streamlit as st
from src.components.traffic_light import KPIStatus, STATUS_COLORS, STATUS_EMOJI


def kpi_card(
    label: str,
    value,
    target=None,
    status: KPIStatus = KPIStatus.UNKNOWN,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 2,
    help_text: str = "",
):
    """Render a styled KPI card with optional traffic-light indicator."""
    if isinstance(value, float):
        formatted = f"{prefix}{value:,.{decimals}f}{suffix}"
    elif isinstance(value, int):
        formatted = f"{prefix}{value:,}{suffix}"
    else:
        formatted = f"{prefix}{value}{suffix}"

    color  = STATUS_COLORS[status]
    emoji  = STATUS_EMOJI[status]
    border = f"3px solid {color}"

    if status != KPIStatus.UNKNOWN:
        target_str = f"{prefix}{target:,.{decimals}f}{suffix}" if target is not None else ""
        delta_str  = f"Ziel: {target_str}" if target_str else ""
    else:
        delta_str = ""

    st.markdown(
        f"""
        <div style="
            border-left: {border};
            padding: 12px 16px;
            border-radius: 6px;
            background: #1e1e2e;
            margin-bottom: 8px;
        ">
            <div style="font-size:12px; color:#aaa; margin-bottom:4px;">{emoji} {label}</div>
            <div style="font-size:24px; font-weight:700; color:#fff;">{formatted}</div>
            <div style="font-size:11px; color:#888; margin-top:4px;">{delta_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
        help=help_text or None,
    )
