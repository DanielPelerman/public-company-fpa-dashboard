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
        .baseline-overlay {
            position: relative;
            height: 0;
            margin: 0 0 0.9rem;
            pointer-events: none;
        }
        .baseline-tick {
            position: absolute;
            left: calc(var(--baseline-left) * 1%);
            top: -29px;
            width: 2px;
            height: 12px;
            background: #0b3b7a;
            border-radius: 999px;
            box-shadow: 0 0 0 2px #ffffff;
            transform: translate(-1px, -50%);
            z-index: 50;
        }
        .baseline-tick::after {
            content: "";
            position: absolute;
            left: 50%;
            top: -22px;
            transform: translateX(-50%);
            background: #172033;
            color: #ffffff;
            border-radius: 4px;
            font-size: 0.68rem;
            line-height: 1;
            padding: 0.25rem 0.35rem;
            opacity: 0;
            transition: opacity 0.12s ease;
            white-space: nowrap;
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
    return f"${value:,.0f}M"


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


def baseline_marker(label: str, min_value: float, max_value: float, baseline_value: float) -> str:
    if max_value == min_value:
        position = 0
    else:
        position = (baseline_value - min_value) / (max_value - min_value) * 100
    position = min(max(position, 0), 100)
    return f"""
        <div class="baseline-overlay" aria-hidden="true">
            <div class="baseline-tick" style="--baseline-left: {position:.2f};"></div>
        </div>
        """


def format_financial_table(df: pd.DataFrame, percent_cols: Optional[list[str]] = None):
    percent_cols = percent_cols or []
    formatters = {}

    def money_fmt(value):
        if pd.isna(value):
            return "n/a"
        return f"(${abs(value):,.0f})" if value < 0 else f"${value:,.0f}"

    for col in df.columns:
        if col in percent_cols:
            formatters[col] = "{:.1%}"
        elif pd.api.types.is_numeric_dtype(df[col]) and col.lower() != "year":
            formatters[col] = money_fmt
    return df.style.format(formatters)


def line_chart(df: pd.DataFrame, x: str, y: Union[str, list[str]], title: str, y_title: str = "$M"):
    fig = px.line(df, x=x, y=y, markers=True, title=title)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=58, b=20),
        legend_title_text="",
        yaxis_title=y_title,
        xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=GRID)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, color: Optional[str], title: str, y_title: str = "$M"):
    fig = px.bar(df, x=x, y=y, color=color, title=title, text_auto=".2s")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=58, b=20),
        legend_title_text="",
        yaxis_title=y_title,
        xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=GRID)
    return fig
