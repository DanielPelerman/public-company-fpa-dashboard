import numpy as np
import pandas as pd


def add_income_statement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.sort_values("year").copy()
    out["revenue_growth"] = out["revenue"].pct_change()
    out["gross_margin"] = out["gross_profit"] / out["revenue"]
    out["sga_pct"] = out["sga"] / out["revenue"]
    out["operating_margin"] = out["operating_income"] / out["revenue"]
    out["net_margin"] = out["net_income"] / out["revenue"]
    return out


def add_cash_flow_metrics(df: pd.DataFrame, income_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.sort_values("year").copy()
    revenue = income_df[["year", "revenue"]] if not income_df.empty else pd.DataFrame()
    if not revenue.empty:
        out = out.merge(revenue, on="year", how="left")
        out["fcf_margin"] = out["free_cash_flow"] / out["revenue"]
        out["capex_pct"] = out["capex"] / out["revenue"]
    return out


def add_balance_sheet_metrics(df: pd.DataFrame, income_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.sort_values("year").copy()
    if not income_df.empty:
        revenue = income_df[["year", "revenue"]]
        out = out.merge(revenue, on="year", how="left")
        out["revenue_per_employee"] = out["revenue"] / out["employee_count"] * 1000
    return out


def common_size_income_statement(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "year": row["year"],
                "Revenue": 1.0,
                "COGS": row["cogs"] / row["revenue"],
                "Gross Profit": row["gross_profit"] / row["revenue"],
                "SG&A": row["sga"] / row["revenue"],
                "Operating Income": row["operating_income"] / row["revenue"],
                "Net Income": row["net_income"] / row["revenue"],
            }
        )
    return pd.DataFrame(rows)


def calculate_budget_variance(actual_df: pd.DataFrame, budget_df: pd.DataFrame, cash_flow_df: pd.DataFrame) -> pd.DataFrame:
    if actual_df.empty or budget_df.empty:
        return pd.DataFrame()

    latest_year = int(actual_df["year"].max())
    actual = actual_df.loc[actual_df["year"] == latest_year].iloc[0]
    budget = budget_df.loc[budget_df["year"] == latest_year]
    if budget.empty:
        budget = budget_df.iloc[[0]]
    budget = budget.iloc[0]

    revenue_budget = actual_df.loc[actual_df["year"] == latest_year - 1, "revenue"].iloc[0] * (1 + budget["revenue_growth"])
    gross_profit_budget = revenue_budget * budget["gross_margin"]
    sga_budget = revenue_budget * budget["sga_pct"]
    operating_income_budget = gross_profit_budget - sga_budget
    tax_budget = max(operating_income_budget - actual.get("interest_expense", 0), 0) * budget["tax_rate"]
    net_income_budget = operating_income_budget - actual.get("interest_expense", 0) - tax_budget
    fcf_budget = (
        net_income_budget
        + revenue_budget * budget["depreciation_pct"]
        - revenue_budget * budget["working_capital_pct"]
        - revenue_budget * budget["capex_pct"]
    )

    actual_fcf = cash_flow_df.loc[cash_flow_df["year"] == latest_year, "free_cash_flow"].iloc[0]

    metrics = [
        ("Revenue", actual["revenue"], revenue_budget, "higher"),
        ("Gross Profit", actual["gross_profit"], gross_profit_budget, "higher"),
        ("SG&A", actual["sga"], sga_budget, "lower"),
        ("Operating Income", actual["operating_income"], operating_income_budget, "higher"),
        ("Net Income", actual["net_income"], net_income_budget, "higher"),
        ("Free Cash Flow", actual_fcf, fcf_budget, "higher"),
    ]

    rows = []
    for metric, actual_value, budget_value, favorable_direction in metrics:
        variance = actual_value - budget_value
        variance_pct = variance / budget_value if budget_value else np.nan
        favorable = variance >= 0 if favorable_direction == "higher" else variance <= 0
        rows.append(
            {
                "metric": metric,
                "actual": actual_value,
                "budget": budget_value,
                "variance": variance,
                "variance_pct": variance_pct,
                "status": "Favorable" if favorable else "Unfavorable",
            }
        )

    return pd.DataFrame(rows)


def latest_snapshot(income_df: pd.DataFrame, cash_flow_df: pd.DataFrame) -> dict:
    if income_df.empty:
        return {}

    income = add_income_statement_metrics(income_df)
    cash_flow = add_cash_flow_metrics(cash_flow_df, income_df)
    latest_year = int(income["year"].max())
    row = income.loc[income["year"] == latest_year].iloc[0]
    fcf = cash_flow.loc[cash_flow["year"] == latest_year, "free_cash_flow"].iloc[0]
    fcf_margin = fcf / row["revenue"]

    return {
        "year": latest_year,
        "revenue": row["revenue"],
        "revenue_growth": row["revenue_growth"],
        "gross_margin": row["gross_margin"],
        "operating_margin": row["operating_margin"],
        "net_income": row["net_income"],
        "free_cash_flow": fcf,
        "fcf_margin": fcf_margin,
    }

