# Nike FP&A Dashboard

A professional Streamlit web app that simulates an FP&A operating review and forecasting process for a public company. The first version uses illustrative Nike-style sample data so the dashboard can run immediately.

## What The App Does

- Reviews historical income statement, balance sheet, and cash flow performance
- Tracks revenue growth, gross margin, EBITDA margin, operating margin, free cash flow, and operating KPIs
- Analyzes revenue by geography, product category, and channel
- Compares budget vs actual results with variance labels
- Builds a 1-10 year forecast from editable planning assumptions and selectable revenue forecast methodologies
- Runs Bear, Base, Bull, and Custom scenarios
- Generates rule-based CFO-style management commentary

## Why It Is Relevant To FP&A

The app mirrors the work an FP&A team performs during monthly business reviews, annual planning, and forecast refreshes. It emphasizes internal operating performance rather than stock valuation or buy/sell recommendations.

It demonstrates:

- Financial statement analysis
- Margin and expense analysis
- Budget vs actual variance analysis
- Forecast modeling
- Scenario planning
- KPI tracking
- Executive communication and management recommendations
- Dashboard design for finance stakeholders
- Explainable forecast methodology selection

## Project Structure

```text
fp&a_project/
├── app.py
├── components/
│   └── ui.py
├── data/
│   ├── budget_assumptions.csv
│   ├── historical_balance_sheet.csv
│   ├── historical_cash_flow.csv
│   ├── historical_income_statement.csv
│   ├── operating_kpis.csv
│   └── segment_revenue.csv
├── utils/
│   ├── commentary.py
│   ├── data_loader.py
│   ├── finance.py
│   └── forecast.py
├── docs/
│   └── fpa_quality_review.md
├── requirements.txt
└── README.md
```

## How To Run Locally

From the project folder:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Replacing Sample Data With Real Public-Company Data

Replace the CSV files in `data/` with exported data from 10-Ks, company filings, investor relations tables, Yahoo Finance, or another trusted source. Keep the column names consistent with the starter CSVs, or update the helper functions in `utils/finance.py` and `utils/forecast.py`.

To add another company later:

1. Add rows for the new company to each CSV file.
2. Use the same `company` name across all files.
3. Refresh the Streamlit app.
4. Select the new company in the sidebar.

## Notes

The included Nike-style dataset is illustrative and designed for portfolio demonstration. It should not be treated as audited financial data or investment research.

See `docs/fpa_quality_review.md` for the FP&A calculation review, forecast methodology rationale, and major quality improvements.
