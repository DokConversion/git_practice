import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


_THEME = dict(
    paper_bgcolor="#1e1e2e",
    plot_bgcolor="#1e1e2e",
    font_color="#cdd6f4",
    margin=dict(l=20, r=20, t=40, b=20),
)


def spend_bar_chart(daily: list[dict]) -> go.Figure:
    """Daily Meta spend bar chart."""
    df = pd.DataFrame(daily) if daily else pd.DataFrame(columns=["date", "meta_spend"])
    fig = go.Figure(go.Bar(
        x=df.get("date", []),
        y=df.get("meta_spend", []),
        marker_color="#89b4fa",
        name="Spend (€)",
    ))
    fig.update_layout(title="Täglicher Spend", yaxis_title="€", **_THEME)
    return fig


def leads_cpl_chart(daily: list[dict]) -> go.Figure:
    """Dual-axis: leads (bar) + CPL (line)."""
    df = pd.DataFrame(daily) if daily else pd.DataFrame(columns=["date", "meta_leads", "meta_cpl"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.get("date", []), y=df.get("meta_leads", []),
        name="Leads", marker_color="#a6e3a1", yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df.get("date", []), y=df.get("meta_cpl", []),
        name="CPL (€)", line=dict(color="#f38ba8", width=2), yaxis="y2",
    ))
    fig.update_layout(
        title="Leads & CPL Trend",
        yaxis=dict(title="Leads"),
        yaxis2=dict(title="CPL (€)", overlaying="y", side="right"),
        **_THEME,
    )
    return fig


def budget_pacing_gauge(pacing_ratio: float, monthly_budget: float, spend: float) -> go.Figure:
    """Gauge for budget pacing. pacing_ratio: 1.0 = perfect pace."""
    pct_spent  = round(spend / monthly_budget * 100, 1) if monthly_budget else 0
    color = "#a6e3a1" if 0.85 <= pacing_ratio <= 1.15 else \
            "#f9e2af" if 0.70 <= pacing_ratio <= 1.30 else "#f38ba8"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct_spent,
        delta={"reference": 100 * pacing_ratio, "suffix": "%"},
        title={"text": f"Budget-Pacing<br><sub>{spend:,.0f} € von {monthly_budget:,.0f} € ausgegeben</sub>"},
        gauge={
            "axis": {"range": [0, 120]},
            "bar":  {"color": color},
            "steps": [
                {"range": [0, 75],  "color": "#313244"},
                {"range": [75, 110], "color": "#45475a"},
                {"range": [110, 120], "color": "#585b70"},
            ],
            "threshold": {"line": {"color": "#cba6f7", "width": 3}, "thickness": 0.75, "value": 100},
        },
        number={"suffix": "%"},
    ))
    fig.update_layout(height=280, **_THEME)
    return fig


def sessions_trend_chart(daily: list[dict]) -> go.Figure:
    df = pd.DataFrame(daily) if daily else pd.DataFrame(columns=["date", "sessions", "conversions"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.get("date", []), y=df.get("sessions", []),
        name="Sessions", fill="tozeroy", line=dict(color="#89b4fa"),
    ))
    fig.add_trace(go.Scatter(
        x=df.get("date", []), y=df.get("conversions", []),
        name="Conversions", line=dict(color="#cba6f7", width=2),
    ))
    fig.update_layout(title="Sessions & Conversions", **_THEME)
    return fig


def traffic_sources_chart(sources: list[dict]) -> go.Figure:
    df = pd.DataFrame(sources) if sources else pd.DataFrame(columns=["channel", "sessions"])
    fig = go.Figure(go.Bar(
        x=df.get("channel", []),
        y=df.get("sessions", []),
        marker_color="#89dceb",
        text=df.get("sessions", []),
        textposition="outside",
    ))
    fig.update_layout(title="Traffic-Quellen (Top 5)", yaxis_title="Sessions", **_THEME)
    return fig


def pipeline_funnel(new_leads: int, open_opps: int, won_deals: int) -> go.Figure:
    fig = go.Figure(go.Funnel(
        y=["Neue Leads", "Offene Opportunities", "Gewonnene Deals"],
        x=[new_leads, open_opps, won_deals],
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": ["#89b4fa", "#cba6f7", "#a6e3a1"]},
    ))
    fig.update_layout(title="CRM Pipeline Funnel", **_THEME)
    return fig


def roas_components_chart(spend: float, revenue: float) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=["Meta Spend", "CRM Revenue"],
        y=[spend, revenue],
        marker_color=["#f38ba8", "#a6e3a1"],
        text=[f"€{spend:,.0f}", f"€{revenue:,.0f}"],
        textposition="outside",
    ))
    fig.update_layout(title="ROAS Komponenten", yaxis_title="€", **_THEME)
    return fig
