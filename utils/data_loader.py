from pathlib import Path

import pandas as pd
import streamlit as st


DATA_FILES = {
    "income_statement": "historical_income_statement.csv",
    "balance_sheet": "historical_balance_sheet.csv",
    "cash_flow": "historical_cash_flow.csv",
    "segments": "segment_revenue.csv",
    "kpis": "operating_kpis.csv",
    "budget": "budget_assumptions.csv",
}


@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_financial_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    data = {}
    missing_files = []

    for key, file_name in DATA_FILES.items():
        path = data_dir / file_name
        if path.exists():
            data[key] = load_csv(str(path))
        else:
            missing_files.append(file_name)
            data[key] = pd.DataFrame()

    if missing_files:
        st.warning(
            "Some data files are missing: "
            + ", ".join(missing_files)
            + ". Add them to the data folder to enable every dashboard section."
        )

    return data

