from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import (
    BAD,
    GOOD,
    apply_theme,
    bar_chart,
    baseline_marker,
    format_financial_table,
    kpi_card,
    line_chart,
    money,
    page_header,
    pct,
)
from utils.commentary import (
    cfo_recommendations,
    executive_summary,
    revenue_driver_commentary,
    variance_commentary,
)
from utils.data_loader import load_financial_data
from utils.finance import (
    add_balance_sheet_metrics,
    add_cash_flow_metrics,
    add_income_statement_metrics,
    calculate_budget_variance,
    common_size_income_statement,
    latest_snapshot,
)
from utils.forecast import build_forecast, run_scenarios


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
NAV_ITEMS = [
    "Executive Dashboard",
    "Historical Financials",
    "Revenue Drivers",
    "Expense & Margins",
    "Budget vs Actual",
    "Forecast Builder",
    "Scenario Analysis",
    "KPI Dashboard",
    "CFO Summary",
]
PLANNING_TABS = {"Forecast Builder", "Scenario Analysis", "CFO Summary"}


st.set_page_config(
    page_title="Public Company FP&A Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()


data = load_financial_data(DATA_DIR)
income_raw = data["income_statement"]
companies = sorted(income_raw["company"].unique()) if not income_raw.empty else ["Nike"]

page_header(
    "Public Company FP&A Dashboard",
    "Operating review, variance analysis, forecasting, scenario planning, and CFO-ready commentary for a public-company finance team.",
)
active_tab = st.pills("Dashboard section", NAV_ITEMS, default=NAV_ITEMS[0], label_visibility="collapsed")

if len(companies) > 1:
    company = st.selectbox("Company", companies, index=0)
else:
    company = companies[0]


income = income_raw[income_raw["company"] == company].copy()
balance = data["balance_sheet"][data["balance_sheet"]["company"] == company].copy()
cash_flow = data["cash_flow"][data["cash_flow"]["company"] == company].copy()
segments = data["segments"][data["segments"]["company"] == company].copy()
kpis = data["kpis"][data["kpis"]["company"] == company].copy()
budget = data["budget"][data["budget"]["company"] == company].copy()

income_metrics = add_income_statement_metrics(income)
cash_flow_metrics = add_cash_flow_metrics(cash_flow, income)
balance_metrics = add_balance_sheet_metrics(balance, income)
snapshot = latest_snapshot(income, cash_flow)
variance_df = calculate_budget_variance(income, budget, cash_flow)

latest_year = int(income_metrics["year"].max())
latest_budget = budget[budget["year"] == latest_year + 1]
defaults = latest_budget.iloc[0].to_dict() if not latest_budget.empty else {
    "revenue_growth": 0.04,
    "gross_margin": 0.43,
    "sga_pct": 0.325,
    "tax_rate": 0.225,
    "capex_pct": 0.018,
    "depreciation_pct": 0.015,
    "working_capital_pct": 0.002,
}

revenue_growth = float(defaults["revenue_growth"])
gross_margin = float(defaults["gross_margin"])
sga_pct = float(defaults["sga_pct"])
tax_rate = float(defaults["tax_rate"])
capex_pct = float(defaults["capex_pct"])
depreciation_pct = float(defaults["depreciation_pct"])
working_capital_pct = float(defaults["working_capital_pct"])


ASSUMPTION_CONTROLS = {
    "assumption_revenue_growth": float(defaults["revenue_growth"] * 100),
    "assumption_gross_margin": float(defaults["gross_margin"] * 100),
    "assumption_sga_pct": float(defaults["sga_pct"] * 100),
    "assumption_tax_rate": float(defaults["tax_rate"] * 100),
    "assumption_capex_pct": float(defaults["capex_pct"] * 100),
    "assumption_depreciation_pct": float(defaults["depreciation_pct"] * 100),
    "assumption_working_capital_pct": float(defaults["working_capital_pct"] * 100),
}


def reset_assumptions() -> None:
    for key, baseline in ASSUMPTION_CONTROLS.items():
        st.session_state[key] = baseline


def assumption_slider(key: str, label: str, min_value: float, max_value: float, baseline: float, step: float) -> float:
    value = st.slider(label, min_value, max_value, value=baseline, step=step, key=key)
    st.markdown(baseline_marker("Baseline", min_value, max_value, baseline), unsafe_allow_html=True)
    return value / 100


if active_tab in PLANNING_TABS:
    with st.container(border=True):
        header_col, button_col = st.columns([4, 1])
        with header_col:
            st.markdown("#### Planning Assumptions")
            st.caption("Small ticks on each slider show the original planning values while you test upside or downside cases.")
        with button_col:
            st.button("Reset assumptions", on_click=reset_assumptions, use_container_width=True)
        row_1 = st.columns(4)
        row_2 = st.columns(3)
        with row_1[0]:
            revenue_growth = assumption_slider("assumption_revenue_growth", "Revenue growth %", -10.0, 15.0, ASSUMPTION_CONTROLS["assumption_revenue_growth"], 0.5)
        with row_1[1]:
            gross_margin = assumption_slider("assumption_gross_margin", "Gross margin %", 35.0, 55.0, ASSUMPTION_CONTROLS["assumption_gross_margin"], 0.5)
        with row_1[2]:
            sga_pct = assumption_slider("assumption_sga_pct", "SG&A % of revenue", 20.0, 45.0, ASSUMPTION_CONTROLS["assumption_sga_pct"], 0.5)
        with row_1[3]:
            tax_rate = assumption_slider("assumption_tax_rate", "Tax rate %", 10.0, 35.0, ASSUMPTION_CONTROLS["assumption_tax_rate"], 0.5)
        with row_2[0]:
            capex_pct = assumption_slider("assumption_capex_pct", "Capex % of revenue", 0.5, 5.0, ASSUMPTION_CONTROLS["assumption_capex_pct"], 0.1)
        with row_2[1]:
            depreciation_pct = assumption_slider(
                "assumption_depreciation_pct",
                "Depreciation % of revenue",
                0.5,
                4.0,
                ASSUMPTION_CONTROLS["assumption_depreciation_pct"],
                0.1,
            )
        with row_2[2]:
            working_capital_pct = assumption_slider(
                "assumption_working_capital_pct",
                "Working capital change % of revenue",
                -3.0,
                4.0,
                ASSUMPTION_CONTROLS["assumption_working_capital_pct"],
                0.1,
            )

forecast = build_forecast(
    income,
    revenue_growth=revenue_growth,
    gross_margin=gross_margin,
    sga_pct=sga_pct,
    tax_rate=tax_rate,
    capex_pct=capex_pct,
    depreciation_pct=depreciation_pct,
    working_capital_pct=working_capital_pct,
)
scenario_data = run_scenarios(
    income,
    {
        "revenue_growth": revenue_growth,
        "gross_margin": gross_margin,
        "sga_pct": sga_pct,
        "tax_rate": tax_rate,
        "capex_pct": capex_pct,
        "depreciation_pct": depreciation_pct,
        "working_capital_pct": working_capital_pct,
    },
)


if active_tab == "Executive Dashboard":
    st.subheader(f"{company} Operating Review")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Revenue", money(snapshot["revenue"]), f"YoY growth {pct(snapshot['revenue_growth'])}"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Gross Margin", pct(snapshot["gross_margin"]), f"Latest fiscal year {snapshot['year']}"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Operating Margin", pct(snapshot["operating_margin"]), "Profitability after SG&A"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Free Cash Flow", money(snapshot["free_cash_flow"]), f"FCF margin {pct(snapshot['fcf_margin'])}"), unsafe_allow_html=True)

    c5, c6, c7 = st.columns(3)
    c5.markdown(kpi_card("Net Income", money(snapshot["net_income"]), f"Net margin {pct(snapshot['net_income'] / snapshot['revenue'])}"), unsafe_allow_html=True)
    c6.markdown(kpi_card("SG&A % Revenue", pct(income_metrics.iloc[-1]["sga_pct"]), "Operating expense intensity"), unsafe_allow_html=True)
    c7.markdown(kpi_card("Capex % Revenue", pct(cash_flow_metrics.iloc[-1]["capex_pct"]), "Reinvestment rate"), unsafe_allow_html=True)

    st.markdown(f'<div class="summary-box">{executive_summary(snapshot)}</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    chart_col1.plotly_chart(line_chart(income_metrics, "year", "revenue", "Revenue Trend"), use_container_width=True)
    chart_col2.plotly_chart(line_chart(income_metrics, "year", "operating_income", "Operating Income Trend"), use_container_width=True)

    margin_view = income_metrics[["year", "gross_margin", "operating_margin", "net_margin"]].melt(
        "year", var_name="Metric", value_name="Margin"
    )
    margin_view["Metric"] = margin_view["Metric"].str.replace("_", " ").str.title()
    cash_view = cash_flow_metrics[["year", "free_cash_flow"]]

    chart_col3, chart_col4 = st.columns(2)
    margin_fig = px.line(margin_view, x="year", y="Margin", color="Metric", markers=True, title="Margin Trend")
    margin_fig.update_layout(template="plotly_white", yaxis_tickformat=".1%", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
    chart_col3.plotly_chart(margin_fig, use_container_width=True)
    chart_col4.plotly_chart(line_chart(cash_view, "year", "free_cash_flow", "Free Cash Flow Trend"), use_container_width=True)


if active_tab == "Historical Financials":
    st.subheader("Historical Financial Statements")
    hist_tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow", "Common Size"])

    income_table = income_metrics[
        [
            "year",
            "revenue",
            "revenue_growth",
            "gross_profit",
            "gross_margin",
            "sga",
            "sga_pct",
            "operating_income",
            "operating_margin",
            "net_income",
            "net_margin",
        ]
    ].rename(columns=str.title)
    with hist_tabs[0]:
        st.dataframe(
            format_financial_table(
                income_table,
                percent_cols=["Revenue_Growth", "Gross_Margin", "Sga_Pct", "Operating_Margin", "Net_Margin"],
            ),
            width='stretch',
            hide_index=True,
        )
        st.plotly_chart(line_chart(income_metrics, "year", ["revenue", "gross_profit", "operating_income", "net_income"], "Income Statement Trend"), use_container_width=True)

    with hist_tabs[1]:
        balance_table = balance_metrics.drop(columns=["company"], errors="ignore")
        st.dataframe(format_financial_table(balance_table), width='stretch', hide_index=True)
        st.plotly_chart(line_chart(balance_metrics, "year", ["cash", "inventory", "total_debt", "shareholders_equity"], "Balance Sheet Trend"), use_container_width=True)

    with hist_tabs[2]:
        cf_table = cash_flow_metrics.drop(columns=["company"], errors="ignore")
        st.dataframe(format_financial_table(cf_table, percent_cols=["fcf_margin", "capex_pct"]), width='stretch', hide_index=True)
        st.plotly_chart(line_chart(cash_flow_metrics, "year", ["cash_from_operations", "capex", "free_cash_flow"], "Cash Flow Trend"), use_container_width=True)

    with hist_tabs[3]:
        common_size = common_size_income_statement(income)
        st.dataframe(common_size.style.format({col: "{:.1%}" for col in common_size.columns if col != "year"}), width='stretch', hide_index=True)
        common_melt = common_size.melt("year", var_name="Line Item", value_name="Percent of Revenue")
        common_melt = common_melt[common_melt["Line Item"] != "Revenue"]
        fig = px.line(common_melt, x="year", y="Percent of Revenue", color="Line Item", markers=True, title="Common-Size Income Statement")
        fig.update_layout(template="plotly_white", yaxis_tickformat=".1%", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
        st.plotly_chart(fig, use_container_width=True)


if active_tab == "Revenue Drivers":
    st.subheader("Revenue Driver Analysis")
    st.markdown(f'<div class="summary-box">{revenue_driver_commentary(segments)}</div>', unsafe_allow_html=True)

    category = st.radio("Revenue view", ["Geography", "Product", "Channel"], horizontal=True)
    segment_view = segments[segments["category_type"] == category].copy()
    latest_segments = segment_view[segment_view["year"] == latest_year].copy()
    latest_segments["mix"] = latest_segments["revenue"] / latest_segments["revenue"].sum()

    seg_col1, seg_col2 = st.columns(2)
    seg_col1.plotly_chart(bar_chart(segment_view, "year", "revenue", "segment", f"{category} Revenue"), use_container_width=True)

    mix_fig = px.pie(latest_segments, values="revenue", names="segment", title=f"{latest_year} {category} Mix", hole=0.48)
    mix_fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=58, b=20), legend_title_text="")
    seg_col2.plotly_chart(mix_fig, use_container_width=True)

    segment_growth = segment_view.sort_values(["segment", "year"]).copy()
    segment_growth["growth"] = segment_growth.groupby("segment")["revenue"].pct_change()
    growth_table = segment_growth[segment_growth["year"] == latest_year][["segment", "revenue", "growth"]].rename(
        columns={"segment": "Segment", "revenue": "Revenue", "growth": "YoY Growth"}
    )
    st.dataframe(growth_table.style.format({"Revenue": "${:,.0f}", "YoY Growth": "{:.1%}"}), width='stretch', hide_index=True)


if active_tab == "Expense & Margins":
    st.subheader("Expense & Margin Analysis")
    expense_df = income_metrics[["year", "cogs", "sga", "gross_margin", "sga_pct", "operating_margin"]].copy()
    latest = expense_df.iloc[-1]
    prior = expense_df.iloc[-2]
    margin_delta = latest["operating_margin"] - prior["operating_margin"]
    status_color = GOOD if margin_delta >= 0 else BAD
    status_text = "expanding" if margin_delta >= 0 else "compressing"
    st.markdown(
        f'<div class="summary-box">Operating margin is <b style="color:{status_color};">{status_text}</b> by {pct(abs(margin_delta))} year over year. SG&A intensity is {pct(latest["sga_pct"])} of revenue.</div>',
        unsafe_allow_html=True,
    )

    exp_col1, exp_col2 = st.columns(2)
    exp_col1.plotly_chart(line_chart(income_metrics, "year", ["cogs", "sga", "operating_income"], "Expenses and Operating Income"), use_container_width=True)
    margin_melt = income_metrics[["year", "gross_margin", "sga_pct", "operating_margin"]].melt("year", var_name="Metric", value_name="Percent")
    margin_melt["Metric"] = margin_melt["Metric"].str.replace("_", " ").str.title()
    fig = px.line(margin_melt, x="year", y="Percent", color="Metric", markers=True, title="Margin and Expense Rates")
    fig.update_layout(template="plotly_white", yaxis_tickformat=".1%", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
    exp_col2.plotly_chart(fig, use_container_width=True)

    expense_table = income_metrics[["year", "revenue", "cogs", "gross_profit", "sga", "operating_income", "gross_margin", "sga_pct", "operating_margin"]]
    st.dataframe(format_financial_table(expense_table, percent_cols=["gross_margin", "sga_pct", "operating_margin"]), width='stretch', hide_index=True)


if active_tab == "Budget vs Actual":
    st.subheader("Budget vs Actual / Variance Analysis")
    st.markdown(f'<div class="summary-box">{variance_commentary(variance_df)}</div>', unsafe_allow_html=True)
    variance_display = variance_df.rename(
        columns={
            "metric": "Metric",
            "actual": "Actual",
            "budget": "Budget",
            "variance": "Variance",
            "variance_pct": "Variance %",
            "status": "Status",
        }
    )
    st.dataframe(
        variance_display.style.format(
            {"Actual": "${:,.0f}", "Budget": "${:,.0f}", "Variance": "${:,.0f}", "Variance %": "{:.1%}"}
        ).map(lambda value: f"color: {GOOD}; font-weight: 700" if value == "Favorable" else f"color: {BAD}; font-weight: 700", subset=["Status"]),
        width='stretch',
        hide_index=True,
    )

    var_fig = px.bar(variance_display, x="Metric", y="Variance", color="Status", title=f"{latest_year} Budget Variance", text_auto=".2s", color_discrete_map={"Favorable": GOOD, "Unfavorable": BAD})
    var_fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=58, b=20), yaxis_title="$M", xaxis_title="")
    st.plotly_chart(var_fig, use_container_width=True)


if active_tab == "Forecast Builder":
    st.subheader("Forecast Builder")
    forecast_table = forecast[
        [
            "year",
            "revenue",
            "gross_profit",
            "sga",
            "operating_income",
            "net_income",
            "capex",
            "free_cash_flow",
            "gross_margin",
            "operating_margin",
            "net_margin",
            "fcf_margin",
        ]
    ]
    st.dataframe(
        format_financial_table(forecast_table, percent_cols=["gross_margin", "operating_margin", "net_margin", "fcf_margin"]),
        width='stretch',
        hide_index=True,
    )

    actual_forecast = pd.concat(
        [
            income_metrics[["year", "revenue", "operating_income", "net_income"]].assign(type="Actual"),
            forecast[["year", "revenue", "operating_income", "net_income"]].assign(type="Forecast"),
        ],
        ignore_index=True,
    )
    fc_col1, fc_col2 = st.columns(2)
    fig = px.line(actual_forecast, x="year", y="revenue", color="type", markers=True, title="Actuals vs Forecast Revenue")
    fig.update_layout(template="plotly_white", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20), yaxis_title="$M", xaxis_title="")
    fc_col1.plotly_chart(fig, use_container_width=True)

    fcf_actual_forecast = pd.concat(
        [
            cash_flow_metrics[["year", "free_cash_flow"]].assign(type="Actual"),
            forecast[["year", "free_cash_flow"]].assign(type="Forecast"),
        ],
        ignore_index=True,
    )
    fig2 = px.line(fcf_actual_forecast, x="year", y="free_cash_flow", color="type", markers=True, title="Actuals vs Forecast Free Cash Flow")
    fig2.update_layout(template="plotly_white", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20), yaxis_title="$M", xaxis_title="")
    fc_col2.plotly_chart(fig2, use_container_width=True)


if active_tab == "Scenario Analysis":
    st.subheader("Scenario Analysis")
    scenario_final = scenario_data[scenario_data["year"] == scenario_data["year"].max()].copy()
    scenario_table = scenario_final[
        ["scenario", "revenue", "operating_income", "net_income", "free_cash_flow", "operating_margin", "net_margin", "fcf_margin"]
    ].rename(columns={"scenario": "Scenario"})
    st.dataframe(
        format_financial_table(scenario_table, percent_cols=["operating_margin", "net_margin", "fcf_margin"]),
        width='stretch',
        hide_index=True,
    )

    sc_col1, sc_col2 = st.columns(2)
    scenario_metric = scenario_data.melt(
        id_vars=["scenario", "year"],
        value_vars=["revenue", "operating_income", "net_income", "free_cash_flow"],
        var_name="Metric",
        value_name="Value",
    )
    scenario_metric["Metric"] = scenario_metric["Metric"].str.replace("_", " ").str.title()
    fig = px.line(scenario_metric, x="year", y="Value", color="scenario", facet_col="Metric", facet_col_wrap=2, markers=True, title="Scenario Outcomes")
    fig.update_layout(template="plotly_white", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
    sc_col1.plotly_chart(fig, use_container_width=True)

    margin_scenarios = scenario_data.melt(
        id_vars=["scenario", "year"],
        value_vars=["operating_margin", "fcf_margin"],
        var_name="Metric",
        value_name="Margin",
    )
    margin_scenarios["Metric"] = margin_scenarios["Metric"].str.replace("_", " ").str.title()
    fig2 = px.line(margin_scenarios, x="year", y="Margin", color="scenario", line_dash="Metric", markers=True, title="Scenario Margins")
    fig2.update_layout(template="plotly_white", yaxis_tickformat=".1%", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
    sc_col2.plotly_chart(fig2, use_container_width=True)


if active_tab == "KPI Dashboard":
    st.subheader("FP&A KPI Dashboard")
    kpi_metrics = income_metrics.merge(cash_flow_metrics[["year", "free_cash_flow", "fcf_margin", "capex_pct"]], on="year")
    kpi_metrics = kpi_metrics.merge(kpis.drop(columns=["company"], errors="ignore"), on="year", how="left")
    latest_kpis = kpi_metrics.iloc[-1]
    kp1, kp2, kp3, kp4 = st.columns(4)
    kp1.markdown(kpi_card("Revenue Growth", pct(latest_kpis["revenue_growth"]), "Top-line trajectory"), unsafe_allow_html=True)
    kp2.markdown(kpi_card("Gross Margin", pct(latest_kpis["gross_margin"]), "Product economics"), unsafe_allow_html=True)
    kp3.markdown(kpi_card("Operating Margin", pct(latest_kpis["operating_margin"]), "Operating leverage"), unsafe_allow_html=True)
    kp4.markdown(kpi_card("FCF Margin", pct(latest_kpis["fcf_margin"]), "Cash conversion"), unsafe_allow_html=True)

    kp5, kp6, kp7, kp8 = st.columns(4)
    kp5.markdown(kpi_card("SG&A % Revenue", pct(latest_kpis["sga_pct"]), "Expense discipline"), unsafe_allow_html=True)
    kp6.markdown(kpi_card("Capex % Revenue", pct(latest_kpis["capex_pct"]), "Reinvestment"), unsafe_allow_html=True)
    kp7.markdown(kpi_card("Inventory Turnover", f"{latest_kpis['inventory_turnover']:.2f}x", "Working capital"), unsafe_allow_html=True)
    kp8.markdown(kpi_card("Revenue / Employee", f"${latest_kpis['revenue_per_employee']:.0f}K", "Productivity"), unsafe_allow_html=True)

    kpi_melt = kpi_metrics[
        ["year", "revenue_growth", "gross_margin", "operating_margin", "net_margin", "fcf_margin", "sga_pct", "capex_pct"]
    ].melt("year", var_name="KPI", value_name="Value")
    kpi_melt["KPI"] = kpi_melt["KPI"].str.replace("_", " ").str.title()
    fig = px.line(kpi_melt, x="year", y="Value", color="KPI", markers=True, title="KPI Trend")
    fig.update_layout(template="plotly_white", yaxis_tickformat=".1%", legend_title_text="", margin=dict(l=20, r=20, t=58, b=20))
    st.plotly_chart(fig, use_container_width=True)


if active_tab == "CFO Summary":
    st.subheader("CFO Summary / Management Recommendations")
    summary = cfo_recommendations(forecast, variance_df)
    cols = st.columns(2)
    sections = list(summary.items())
    for idx, (heading, bullets) in enumerate(sections):
        with cols[idx % 2]:
            st.markdown(f"#### {heading}")
            for item in bullets:
                st.markdown(f"- {item}")

    st.markdown("#### Management View")
    st.markdown(
        f'<div class="summary-box">The base planning case shows {pct(revenue_growth)} revenue growth, {pct(gross_margin)} gross margin, and {pct(sga_pct)} SG&A intensity. The finance team should track whether volume recovery, gross margin, and expense productivity are converting into sustainable free cash flow.</div>',
        unsafe_allow_html=True,
    )
