import pandas as pd


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
) -> pd.DataFrame:
    latest = actual_income.sort_values("year").iloc[-1]
    rows = []
    revenue = float(latest["revenue"])

    for i in range(1, years + 1):
        year = int(latest["year"] + i)
        revenue *= 1 + revenue_growth
        gross_profit = revenue * gross_margin
        sga = revenue * sga_pct
        operating_income = gross_profit - sga
        interest_expense = float(latest.get("interest_expense", 0))
        pretax_income = operating_income - interest_expense
        tax_expense = max(pretax_income, 0) * tax_rate
        net_income = pretax_income - tax_expense
        depreciation = revenue * depreciation_pct
        working_capital_change = revenue * working_capital_pct
        capex = revenue * capex_pct
        free_cash_flow = net_income + depreciation - working_capital_change - capex

        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "gross_profit": gross_profit,
                "sga": sga,
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
                "operating_margin": operating_income / revenue,
                "net_margin": net_income / revenue,
                "fcf_margin": free_cash_flow / revenue,
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
