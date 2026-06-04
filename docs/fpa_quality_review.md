# FP&A Quality Review

This review documents the finance and usability changes made to make the Nike FP&A Dashboard more credible for an operating review, forecast discussion, and entry-level FP&A portfolio presentation.

## Issues Found

- EBITDA and EBITDA margin were missing, even though they are standard operating profitability metrics in FP&A reviews.
- Revenue forecasting used a single fixed growth rate, which made every forecast path overly linear and disconnected from historical performance.
- Segment revenue was analyzed historically but was not available as a forecast driver.
- Some charts could display large dollar values with generic abbreviated labels, which can make millions look like raw thousands.
- Budget variance logic was mathematically correct, but the table did not explain why revenue/profit items and expense items have opposite favorability rules.
- Legacy slider baseline styling remained in the component code after planning assumptions were converted to input boxes.

## Changes Made

- Added EBITDA as Operating Income plus Depreciation, and added EBITDA Margin as EBITDA divided by Revenue.
- Added EBITDA to the Executive Dashboard, Historical Financials, Expense & Margin Analysis, Budget vs Actual, Forecast Builder, Scenario Analysis, and KPI Dashboard.
- Added four revenue forecast methodologies:
  - Management Growth Assumption
  - Historical CAGR
  - Weighted Historical Trend
  - Segment Driver Forecast
- Added methodology commentary in Forecast Builder so users can see what is driving the forecast.
- Added a Segment Driver Detail expander when the segment-driven method is selected.
- Improved chart unit formatting so dollar charts display in billions of dollars ($B), while detailed tables remain in millions of dollars ($M).
- Added variance favorability logic to the Budget vs Actual table.
- Kept the planning panel as numeric inputs instead of sliders so it feels more like an FP&A model.
- Removed obsolete slider baseline CSS and helper code.

## Finance Rationale

- EBITDA is a standard proxy for pre-D&A operating profitability and helps bridge gross margin, operating margin, and cash flow.
- Revenue forecasts should be explainable. Providing multiple simple methodologies gives the analyst a way to compare management assumptions against historical evidence without overbuilding the model.
- A weighted historical trend gives more influence to recent performance while still blending toward a longer-term trend.
- A segment driver forecast is more realistic for a company like Nike because geography-level trends can differ materially and should aggregate to total revenue.
- Variance equals Actual minus Budget. Positive variance is favorable for revenue, profit, EBITDA, net income, and free cash flow. Negative variance is favorable for SG&A because it is an expense.
- Free cash flow remains calculated as Operating Cash Flow minus Capex in historical reporting, and as Net Income plus Depreciation minus Working Capital Change minus Capex in forecast periods.

## User Experience Rationale

- Finance users expect planning assumptions to look editable and controlled, not playful. Numeric inputs support that mental model.
- Chart axes now use $B for readability while table captions clearly identify $M detail.
- Methodology commentary reduces ambiguity and makes the dashboard easier to discuss in an interview.
- The app stays focused on operating performance, budgeting, forecasting, variance analysis, and management recommendations rather than valuation or stock recommendations.

## Code Optimizations

- Centralized EBITDA and margin calculations in `utils/finance.py`.
- Centralized forecast methodology logic in `utils/forecast.py`.
- Improved shared chart helpers in `components/ui.py` to apply consistent dollar scaling.
- Removed unused slider baseline styles and helper code from the UI component layer.
