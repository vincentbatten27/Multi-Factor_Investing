import streamlit as st
import pandas as pd
from app_common import load_data
from RunSim_utils import *
import statsmodels.api as sm

st.set_page_config(page_title="Portfolio Optimizer")

price_monthly_data, new_monthly_data, ff3_monthly, indexgspc1, spy_yoy_tickers1 = load_data()

st.title("Portfolio Optimizer")
st.caption(
    "Analyze an existing portfolio's Fama-French factor exposures against a target, "
    "and see whether getting there means reweighting your current holdings or adding/dropping positions.<br>"
    "[ℹ️ Documentation](https://github.com/vincentbatten27/Multi-Factor_Investing/blob/main/README.md)",
    unsafe_allow_html=True,
)

st.divider()

# =============================================================================
# INPUT: Upload Current Portfolio
# =============================================================================
st.header("Upload Your Portfolio")
st.caption(
    "Upload your current holdings as a CSV or Excel file. *Must be S&P 500 tickers*"
)

if "opt_holdings" not in st.session_state:
    st.session_state.opt_holdings = []
if "opt_file_loaded" not in st.session_state:
    st.session_state.opt_file_loaded = False
if "opt_unknown_tickers" not in st.session_state:
    st.session_state.opt_unknown_tickers = []

sample_csv = "Ticker,Value\nAAPL,50000\nMSFT,30000\nTSLA,20000"
st.download_button(
    "📥 Download Sample Template (CSV)",
    data=sample_csv,
    file_name="portfolio_template.csv",
    mime="text/csv",
)

uploaded_file = st.file_uploader(
    "Upload Portfolio (CSV or Excel)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None and not st.session_state.opt_file_loaded:
    try:
        if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
            uploaded_df = pd.read_excel(uploaded_file)
        else:
            uploaded_df = pd.read_csv(uploaded_file)

        if "Ticker" not in uploaded_df.columns or (
            "Value" not in uploaded_df.columns and "Market Value" not in uploaded_df.columns
        ):
            st.error("File must have a 'Ticker' column and a 'Value' or 'Market Value' column!")
        else:
            if "Value" not in uploaded_df.columns:
                uploaded_df = uploaded_df.rename(columns={"Market Value": "Value"})

            uploaded_df["Ticker"] = uploaded_df["Ticker"].str.upper().str.strip()
            uploaded_df["Value"] = pd.to_numeric(uploaded_df["Value"], errors="coerce")
            uploaded_df = uploaded_df.dropna()


            valid_universe = set(new_monthly_data.columns)
            unknown = sorted(set(uploaded_df["Ticker"]) - valid_universe)

            st.session_state.opt_holdings = uploaded_df.to_dict("records")
            st.session_state.opt_file_loaded = True
            st.session_state.opt_unknown_tickers = unknown
            st.success(f"✅ Loaded {len(st.session_state.opt_holdings)} holdings")
            st.rerun()
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

if uploaded_file is None:
    st.session_state.opt_file_loaded = False

if st.session_state.opt_holdings:
    holdings_df = pd.DataFrame(st.session_state.opt_holdings)
    st.write("**Current Portfolio:**")
    st.dataframe(holdings_df, hide_index=True, width="stretch")

    total_value = holdings_df["Value"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
    col2.metric("Number of Holdings", len(holdings_df))
    col3.metric("Unrecognized Tickers", len(st.session_state.opt_unknown_tickers))

    if st.session_state.opt_unknown_tickers:
        st.warning(
            "These tickers aren't in the current data universe and will be "
            f"ignored: {', '.join(st.session_state.opt_unknown_tickers)}"
        )

    if st.button("🗑️ Clear Portfolio"):
        st.session_state.opt_holdings = []
        st.session_state.opt_file_loaded = False
        st.session_state.opt_unknown_tickers = []
        st.rerun()
else:
    st.info("No portfolio uploaded yet. Will populate once you upload a file above.")

st.divider()

# =============================================================================
# PLACEHOLDER: Factor Exposure & Recommendations
# =============================================================================
st.header("Factor Exposure & Rebalancing Recommendations")
st.info(
   'Find out your portfolio\'s Fama-French factor exposures and get recommendations for rebalancing. '
)

if st.session_state.opt_holdings:
    holdings_df = pd.DataFrame(st.session_state.opt_holdings)

    # drop tickers not in the data universe before running the regression
    clean_df = holdings_df[
        ~holdings_df["Ticker"].isin(st.session_state.opt_unknown_tickers)
    ].copy()

    if "Weight" not in clean_df.columns:
        clean_df["Weight"] = clean_df["Value"] / clean_df["Value"].sum()

    opt_portfolio_weights = clean_df.set_index("Ticker")[["Weight"]]
    opt_portfolio_weights.rename(columns={"Weight": "New Weight"}, inplace=True)

    df_extrap = optimal_weights_appended(opt_portfolio_weights, price_monthly_data)
    portf_ff3 = portoflio_ff3(df_extrap, new_monthly_data, ff3_monthly)
    
    if isinstance(port_ff3, str):
        st.warning(portf_ff3)
    else:
        mkt_beta = portf_ff3["Mkt-RF"]
        smb_beta = portf_ff3["SMB"]
        hml_beta = portf_ff3["HML"]
        mkt_se = portf_ff3["Mkt-RF_SE"]
        smb_se = portf_ff3["SMB_SE"]
        hml_se = portf_ff3["HML_SE"]
        ff3_r2 = portf_ff3["R_squared"]

        st.subheader("Portfolio FF3 Betas")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mkt-RF", f"{mkt_beta:.3f}", help=f"± {mkt_se:.3f} SE")
        col2.metric("SMB", f"{smb_beta:.3f}", help=f"± {smb_se:.3f} SE")
        col3.metric("HML", f"{hml_beta:.3f}", help=f"± {hml_se:.3f} SE")
        col4.metric("R²", f"{ff3_r2:.3f}", help="Share of monthly portfolio return variance explained by the 3 factors")
else:
    st.info("Upload a CSV of your holdings to see your portfolio's factor exposures.")

footer = """
<style>
.footer {
    position: relative;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: transparent;
    color: #31333F;
    text-align: center;
    padding: 20px 10px;
    font-size: 14px;
    border-top: 1px solid #e6e6e6;
    margin-top: 50px;
}
.footer a:hover {
    text-decoration: underline;
}
</style>

<div class="footer">
    <p>Developed by <b>Vincent Batten</b> & <b>Nate Songstad</b> |
    ✉ Email <a href="mailto:vincentbatten27@gmail.com?subject=Beta Optimization App Inquiry">vincentbatten27@gmail.com</a> <br>
    <i>Original Logic by</i> <b>Johanan Pranesh</b><br>
    Sponsored by: <b>Jordan Weintraub</b></p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)
