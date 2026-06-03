import pandas as pd


def executive_summary(snapshot: dict) -> str:
    if not snapshot:
        return "Add financial data to generate the executive summary."

    growth = snapshot["revenue_growth"]
    margin = snapshot["operating_margin"]
    fcf_margin = snapshot["fcf_margin"]

    if growth >= 0.04 and margin >= 0.12:
        tone = "Revenue growth and operating leverage remain healthy."
    elif growth < 0:
        tone = "Revenue declined year over year, creating pressure on earnings and cash generation."
    else:
        tone = "Revenue performance is stable, with management focus shifting toward margin discipline."

    cash_comment = (
        "Free cash flow conversion remains solid."
        if fcf_margin >= 0.08
        else "Free cash flow conversion is below target and should be monitored."
    )
    return f"{tone} Operating margin finished at {margin:.1%}, while {cash_comment}"


def variance_commentary(variance_df: pd.DataFrame) -> str:
    if variance_df.empty:
        return "Budget variance commentary will appear when budget and actual data are available."

    unfavorable = variance_df[variance_df["status"] == "Unfavorable"]
    if unfavorable.empty:
        return "Actual performance was favorable to budget across the reviewed metrics, indicating disciplined execution against the operating plan."

    items = ", ".join(unfavorable["metric"].tolist())
    return (
        f"Unfavorable variance was concentrated in {items}. "
        "Management should isolate volume, price, mix, and cost drivers before resetting the forward forecast."
    )


def revenue_driver_commentary(segment_df: pd.DataFrame) -> str:
    if segment_df.empty:
        return "Add segment data to generate revenue driver commentary."

    latest_year = segment_df["year"].max()
    geography = segment_df[(segment_df["year"] == latest_year) & (segment_df["category_type"] == "Geography")]
    top_segment = geography.sort_values("revenue", ascending=False).iloc[0]
    return (
        f"In {latest_year}, {top_segment['segment']} remained the largest geography. "
        "Growth should be evaluated by region and channel to separate demand trends from mix shifts."
    )


def cfo_recommendations(forecast_df: pd.DataFrame, variance_df: pd.DataFrame) -> dict[str, list[str]]:
    if forecast_df.empty:
        return {
            "What happened": ["Forecast data is not available."],
            "Why it happened": ["Add assumptions to generate the summary."],
            "Key risks": ["Data coverage is incomplete."],
            "Recommended management actions": ["Load complete financial data and refresh the operating review."],
        }

    first = forecast_df.iloc[0]
    last = forecast_df.iloc[-1]
    revenue_cagr = (last["revenue"] / first["revenue"]) ** (1 / max(len(forecast_df) - 1, 1)) - 1

    what_happened = [
        f"The current forecast projects revenue reaching ${last['revenue']:,.0f}M by {int(last['year'])}.",
        f"Operating margin is expected to move from {first['operating_margin']:.1%} to {last['operating_margin']:.1%}.",
    ]

    why = []
    if last["gross_margin"] < first["gross_margin"]:
        why.append("Gross margin pressure is limiting operating leverage.")
    else:
        why.append("Gross margin stability supports earnings recovery.")
    if last["sga_pct"] > first["sga_pct"]:
        why.append("SG&A is growing faster than planned revenue scale.")
    else:
        why.append("SG&A discipline improves operating income flow-through.")

    risks = []
    if revenue_cagr < 0.03:
        risks.append("Demand risk: revenue growth is below a typical mid-single-digit planning target.")
    if last["fcf_margin"] < 0.07:
        risks.append("Cash conversion risk: free cash flow margin is below the target zone.")
    if not variance_df.empty and (variance_df["status"] == "Unfavorable").any():
        risks.append("Execution risk: current-year unfavorable variances may carry into the next planning cycle.")
    if not risks:
        risks.append("Primary risk is sustaining execution as growth normalizes.")

    actions = []
    if last["sga_pct"] > first["sga_pct"]:
        actions.append("Review discretionary SG&A and set owners for productivity targets.")
    if last["gross_margin"] < first["gross_margin"]:
        actions.append("Prioritize mix, markdown, freight, and sourcing initiatives to stabilize gross margin.")
    if revenue_cagr < 0.03:
        actions.append("Refresh demand assumptions by region and channel before locking the annual plan.")
    if last["fcf_margin"] < 0.07:
        actions.append("Tighten working capital governance and review capex phasing.")
    if not actions:
        actions.append("Maintain operating cadence and track revenue, margin, and cash conversion monthly.")

    return {
        "What happened": what_happened,
        "Why it happened": why,
        "Key risks": risks,
        "Recommended management actions": actions,
    }

