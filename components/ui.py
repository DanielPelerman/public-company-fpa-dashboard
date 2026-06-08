import pandas as pd
import plotly.express as px
import streamlit as st
from typing import Optional, Union


ACCENT = "#1f6feb"
GOOD = "#12805c"
BAD = "#c2410c"
GRID = "#dbe4f0"


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --accent: #1f6feb;
            --ink: #172033;
            --muted: #64748b;
            --line: #dbe4f0;
            --panel: #ffffff;
            --soft: #f7f9fc;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1380px;
        }
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 42%);
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }
        .hero {
            border: 1px solid var(--line);
            background: #ffffff;
            padding: 1.2rem 1.35rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        }
        .hero p {
            color: var(--muted);
            margin: 0.25rem 0 0;
            font-size: 1rem;
        }
        .kpi-card {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 8px;
            padding: 1rem;
            min-height: 112px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
        }
        .kpi-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 700;
        }
        .kpi-value {
            color: var(--ink);
            font-size: 1.7rem;
            font-weight: 760;
            line-height: 1.2;
            margin-top: 0.4rem;
        }
        .kpi-delta {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 0.28rem;
        }
        .summary-box {
            border-left: 4px solid var(--accent);
            background: #eef6ff;
            color: #17324d;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.4rem 0 1rem;
        }
        .status-good {
            color: #12805c;
            font-weight: 700;
        }
        .status-bad {
            color: #c2410c;
            font-weight: 700;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.5rem 0.8rem;
        }
        .stTabs [aria-selected="true"] {
            color: var(--accent);
            border-color: var(--accent);
        }
        div.stNumberInput {
            border: 1px solid #d7e2ef;
            background: #fbfdff;
            border-radius: 8px;
            padding: 0.72rem 0.78rem 0.58rem;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.035);
        }
        div.stNumberInput:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.12);
        }
        div.stNumberInput label {
            color: var(--ink);
            font-weight: 650;
        }
        div.stNumberInput [data-baseweb="input"] {
            border: 1px solid #cbd7e6;
            background: #ffffff;
            border-radius: 7px;
            overflow: hidden;
            min-height: 2.35rem;
            margin-top: 0.35rem;
        }
        div.stNumberInput input {
            color: var(--ink);
            font-weight: 720;
            font-size: 1rem;
            padding-left: 0.72rem;
        }
        div.stNumberInput button {
            border-left: 1px solid #dbe4f0;
            background: #f3f7fc;
            color: var(--ink);
            min-width: 2.15rem;
        }
        div.stNumberInput button:hover {
            background: #e8f1ff;
            color: var(--accent);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(value: float) -> str:
    if pd.isna(value):
        return "n/a"

    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1000:
        return f"{sign}${value / 1000:,.1f}B"
    return f"{sign}${value:,.0f}M"


def pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.1%}"


def number(value: float) -> str:
    return f"{value:,.1f}"


def kpi_card(label: str, value: str, delta: str = "") -> str:
    return f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """


def format_financial_table(df: pd.DataFrame, percent_cols: Optional[list[str]] = None):
    percent_cols = percent_cols or []
    formatters = {}

    def money_fmt(value):
        if pd.isna(value):
            return "n/a"
        return f"(${abs(value):,.0f})" if value < 0 else f"${value:,.0f}"

    def number_fmt(value):
        if pd.isna(value):
            return "n/a"
        return f"{value:,.1f}" if abs(value) < 100 else f"{value:,.0f}"

    for col in df.columns:
        if col in percent_cols:
            formatters[col] = "{:.1%}"
        elif pd.api.types.is_numeric_dtype(df[col]) and ("($M)" in col or "($K)" in col):
            formatters[col] = money_fmt
        elif pd.api.types.is_numeric_dtype(df[col]) and col.lower() != "year":
            formatters[col] = number_fmt
    return df.style.format(formatters)


def line_chart(df: pd.DataFrame, x: str, y: Union[str, list[str]], title: str, y_title: str = "Dollars ($M)"):
    chart_df = df.copy()
    y_columns = [y] if isinstance(y, str) else y
    chart_y_title = y_title
    if y_title == "Dollars ($M)":
        for col in y_columns:
            chart_df[col] = chart_df[col] / 1000
        chart_y_title = "Dollars ($B)"

    fig = px.line(chart_df, x=x, y=y, markers=True, title=title)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=58, b=20),
        legend_title_text="",
        yaxis_title=chart_y_title,
        xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=GRID, tickprefix="$" if chart_y_title == "Dollars ($B)" else None, tickformat=",.1f" if chart_y_title == "Dollars ($B)" else None)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, color: Optional[str], title: str, y_title: str = "Dollars ($M)"):
    chart_df = df.copy()
    chart_y_title = y_title
    text_value = None
    if y_title == "Dollars ($M)":
        chart_df[y] = chart_df[y] / 1000
        chart_df["_display_value"] = chart_df[y].map(lambda value: f"${value:,.1f}B")
        chart_y_title = "Dollars ($B)"
        text_value = "_display_value"

    fig = px.bar(data_frame=chart_df, x=x, y=y, color=color, title=title, text=text_value)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=58, b=20),
        legend_title_text="",
        yaxis_title=chart_y_title,
        xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=GRID, tickprefix="$" if chart_y_title == "Dollars ($B)" else None, tickformat=",.1f" if chart_y_title == "Dollars ($B)" else None)
    fig.update_traces(textposition="inside", insidetextanchor="middle", hovertemplate="%{x}<br>%{y:$,.1f}B<extra></extra>" if chart_y_title == "Dollars ($B)" else None)
    return fig
