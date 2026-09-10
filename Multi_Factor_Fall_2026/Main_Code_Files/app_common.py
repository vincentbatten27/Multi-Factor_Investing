"""
Shared, cached data loading for the multipage app.

Both the main page (streamlit_optimizer.py) and everything in pages/ should
import load_data() from here instead of defining it locally. Two separate
local definitions of an @st.cache_data function (even if identical) get
cached separately by Streamlit and will each trigger their own CSV read /
run_sp500_data() call the first time that page is visited — defeating the
point of caching across pages. Defining it once here means both pages share
one cache entry.

Also note: we resolve file paths off RunSim_utils.SCRIPT_DIR (the directory
RunSim_utils.py lives in), not this file's own location. That way it doesn't
matter whether load_data() is called from the repo root or from inside
pages/ — it always finds monthly_prices.csv / monthly_returns.csv next to
RunSim_utils.py.
"""
import streamlit as st
import pandas as pd
from RunSim_utils import run_sp500_data, SCRIPT_DIR


@st.cache_data
def load_data():
    price_monthly_data = pd.read_csv(SCRIPT_DIR / "monthly_prices.csv")
    price_monthly_data.columns.name = "Ticker"
    price_monthly_data["Date"] = pd.to_datetime(price_monthly_data["Date"])
    price_monthly_data = price_monthly_data.set_index("Date")

    new_monthly_data = pd.read_csv(SCRIPT_DIR / "monthly_returns.csv")
    new_monthly_data.columns.name = "Ticker"
    new_monthly_data["Date"] = pd.to_datetime(new_monthly_data["Date"])
    new_monthly_data = new_monthly_data.set_index("Date")
    new_monthly_data = new_monthly_data.apply(pd.to_numeric, errors="coerce")

    indexgspc1, spy_yoy_tickers1 = run_sp500_data()

    return price_monthly_data, new_monthly_data, indexgspc1, spy_yoy_tickers1
