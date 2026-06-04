import numpy as np
import pandas as pd
from typing import Optional


FORECAST_METHODS = [
    "Management Growth Assumption",
    "Historical CAGR",
    "Weighted Historical Trend",
    "Segment Driver Forecast",
]


def _historical_growth_rates(actual_income: pd.DataFrame) -> pd.Series:
    revenue = actual_income.sort_values("year")["revenue"].astype(float)
    return revenue.pct_change().dropna()


def historical_cagr(actual_income: pd.DataFrame) -> float:
    sorted_income = actual_income.sort_values("year")
    first = float(sorted_income.iloc[0]["revenue"])
    last = float(sorted_income.iloc[-1]["revenue"])
    periods = max(len(sorted_income) - 1, 1)
    return (last / first) ** (1 / periods) - 1


def weighted_historical_growth(actual_income: pd.DataFrame) -> float:
    growth = _historical_growth_rates(actual_income)
    if growth.empty:
        return 0.0

    weights = np.arange(1, len(growth) + 1, dtype=float)
    return float(np.average(growth, weights=weights))


def _blend_growth(start_growth: float, long_term_growth: float, year_index: int) -> float:
    if year_index <= 1:
        return start_growth

    blend = min(0.25 * (year_index - 1), 0.75)
    return start_growth * (1 - blend) + long_term_growth * blend


def _forecast_revenue_from_growth(
    starting_revenue: float,
    growth_rates: list[float],
    years: int,
) -> list[float]:
    revenue = starting_revenue
    output = []
    for i in range(years):
        growth = growth_rates[min(i, len(growth_rates) - 1)]
        revenue *= 1 + growth
        output.append(revenue)
    return output


def _segment_driver_revenue(
    segment_df: pd.DataFrame,
    latest_year: int,
    years: int,
) -> tuple[list[float], list[float], pd.DataFrame]:
    geography = segment_df[segment_df["category_type"] == "Geography"].sort_values(["segment", "year"]).copy()
    if geography.empty:
        return [], [], pd.DataFrame()

    geography["growth"] = geography.groupby("segment")["revenue"].pct_change()
    long_term_growth = historical_cagr(
        geography.groupby("year", as_index=False)["revenue"].sum().assign(company="Segment Total")
    )
    segment_rows = []
    totals = [0.0 for _ in range(years)]

    for segment, group in geography.groupby("segment"):
        group = group.sort_values("year")
        latest_revenue = float(group.iloc[-1]["revenue"])
        recent_growth = group["growth"].dropna()
        if recent_growth.empty:
            weighted_growth = long_term_growth
        else:
            weights = np.arange(1, len(recent_growth) + 1, dtype=float)
            weighted_growth = float(np.average(recent_growth, weights=weights))

        # Cap segment growth to keep one-year volatility from overpowering a simple FP&A planning case.
        first_year_growth = float(np.clip(weighted_growth, -0.08, 0.08))
        segment_revenue = latest_revenue
        growth_path = []
        for i in range(1, years + 1):
            growth = _blend_growth(first_year_growth, long_term_growth, i)
            growth_path.append(growth)
            segment_revenue *= 1 + growth
            totals[i - 1] += segment_revenue

        segment_rows.append(
            {
                "segment": segment,
                "latest_revenue": latest_revenue,
                "initial_growth": first_year_growth,
                "terminal_growth": growth_path[-1],
            }
        )

    aggregate_growth = []
    prior_revenue = float(geography[geography["year"] == latest_year]["revenue"].sum())
    for total in totals:
        aggregate_growth.append(total / prior_revenue - 1)
        prior_revenue = total

    return totals, aggregate_growth, pd.DataFrame(segment_rows)


def revenue_forecast(
    actual_income: pd.DataFrame,
    segment_df: pd.DataFrame,
    method: str,
    management_growth: float,
    years: int,
) -> tuple[list[float], list[float], pd.DataFrame]:
    latest = actual_income.sort_values("year").iloc[-1]
    starting_revenue = float(latest["revenue"])
    long_term_growth = historical_cagr(actual_income)

    if method == "Historical CAGR":
        growth_rates = [long_term_growth] * years
        return _forecast_revenue_from_growth(starting_revenue, growth_rates, years), growth_rates, pd.DataFrame()

    if method == "Weighted Historical Trend":
        first_year_growth = weighted_historical_growth(actual_income)
        growth_rates = [_blend_growth(first_year_growth, long_term_growth, i) for i in range(1, years + 1)]
        return _forecast_revenue_from_growth(starting_revenue, growth_rates, years), growth_rates, pd.DataFrame()

    if method == "Segment Driver Forecast":
        segment_revenue, growth_rates, segment_detail = _segment_driver_revenue(segment_df, int(latest["year"]), years)
        if segment_revenue:
            return segment_revenue, growth_rates, segment_detail

    growth_rates = [management_growth] * years
    return _forecast_revenue_from_growth(starting_revenue, growth_rates, years), growth_rates, pd.DataFrame()


def forecast_method_summary(method: str, management_growth: float, growth_rates: list[float]) -> str:
    if not growth_rates:
        return "Forecast revenue is driven by the selected planning method."

    first_growth = growth_rates[0]
    final_growth = growth_rates[-1]
    if method == "Management Growth Assumption":
        return f"Revenue grows at the management case assumption of {management_growth:.1%} per year."
    if method == "Historical CAGR":
        return f"Revenue grows at the historical compound annual growth rate of {first_growth:.1%}."
    if method == "Weighted Historical Trend":
        return (
            f"Revenue starts at a recent-year weighted growth rate of {first_growth:.1%} "
            f"and blends toward the longer-term trend by the final forecast year ({final_growth:.1%})."
        )
    if method == "Segment Driver Forecast":
        return (
            f"Each geography is forecast separately using its weighted recent trend, with growth capped for planning realism. "
            f"The aggregate revenue growth path moves from {first_growth:.1%} to {final_growth:.1%}."
        )
    return "Forecast revenue is driven by the selected planning method."


def build_forecast(
    actual_income: pd.DataFrame,
    revenue_growth: float,
    gross_margin: float,
    sga_pct: float,
    tax_rate: float,
    capex_pct: float,
    depreciation_pct: float,
    working_capital_pct: float,
    years: int = 3,
    method: str = "Management Growth Assumption",
    segment_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    latest = actual_income.sort_values("year").iloc[-1]
    rows = []
    segment_df = pd.DataFrame() if segment_df is None else segment_df
    revenue_values, growth_rates, _ = revenue_forecast(actual_income, segment_df, method, revenue_growth, years)

    for i in range(1, years + 1):
        year = int(latest["year"] + i)
        revenue = revenue_values[i - 1]
        current_revenue_growth = growth_rates[i - 1]
        gross_profit = revenue * gross_margin
        sga = revenue * sga_pct
        operating_income = gross_profit - sga
        depreciation = revenue * depreciation_pct
        ebitda = operating_income + depreciation
        interest_expense = float(latest.get("interest_expense", 0))
        pretax_income = operating_income - interest_expense
        tax_expense = max(pretax_income, 0) * tax_rate
        net_income = pretax_income - tax_expense
        working_capital_change = revenue * working_capital_pct
        capex = revenue * capex_pct
        free_cash_flow = net_income + depreciation - working_capital_change - capex

        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "revenue_growth": current_revenue_growth,
                "gross_profit": gross_profit,
                "sga": sga,
                "ebitda": ebitda,
                "operating_income": operating_income,
                "pretax_income": pretax_income,
                "tax_expense": tax_expense,
                "net_income": net_income,
                "depreciation": depreciation,
                "working_capital_change": working_capital_change,
                "capex": capex,
                "free_cash_flow": free_cash_flow,
                "gross_margin": gross_margin,
                "sga_pct": sga_pct,
                "ebitda_margin": ebitda / revenue,
                "operating_margin": operating_income / revenue,
                "net_margin": net_income / revenue,
                "fcf_margin": free_cash_flow / revenue,
                "forecast_method": method,
            }
        )

    return pd.DataFrame(rows)


def scenario_assumptions(custom: dict) -> dict[str, dict]:
    return {
        "Bear": {
            "revenue_growth": -0.02,
            "gross_margin": 0.405,
            "sga_pct": 0.350,
            "tax_rate": 0.235,
            "capex_pct": 0.019,
            "depreciation_pct": 0.015,
            "working_capital_pct": 0.006,
        },
        "Base": {
            "revenue_growth": 0.04,
            "gross_margin": 0.430,
            "sga_pct": 0.325,
            "tax_rate": 0.225,
            "capex_pct": 0.018,
            "depreciation_pct": 0.015,
            "working_capital_pct": 0.002,
        },
        "Bull": {
            "revenue_growth": 0.075,
            "gross_margin": 0.448,
            "sga_pct": 0.310,
            "tax_rate": 0.220,
            "capex_pct": 0.017,
            "depreciation_pct": 0.014,
            "working_capital_pct": 0.000,
        },
        "Custom": custom,
    }


def run_scenarios(actual_income: pd.DataFrame, custom: dict, years: int = 3) -> pd.DataFrame:
    outputs = []
    for scenario, assumptions in scenario_assumptions(custom).items():
        forecast = build_forecast(actual_income, **assumptions, years=years)
        forecast["scenario"] = scenario
        outputs.append(forecast)
    return pd.concat(outputs, ignore_index=True)
