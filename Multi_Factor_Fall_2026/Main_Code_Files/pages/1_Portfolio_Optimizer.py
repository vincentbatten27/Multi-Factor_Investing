import streamlit as st
import pandas as pd
from app_common import load_data
from RunSim_utils import *
import statsmodels.api as sm

st.set_page_config(page_title="Portfolio Optimizer")

price_monthly_data, new_monthly_data, ff3_monthly, indexgspc1, spy_yoy_tickers1 = load_data()
today = pd.Timestamp.now()# -relativedelta(days=10)  # ensure we have data for the current month if we're early in the month
target_date = today.replace(day=1)
target_date = target_date.normalize()
curr_weights = target_date.date()
weights_opt_d = curr_weights - relativedelta(days=1)

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

        if "Ticker" not in uploaded_df.columns:
            st.error("File must have a 'Ticker' column!")
        else:
            has_value = "Value" in uploaded_df.columns or "Market Value" in uploaded_df.columns
            has_weight = "Weight" in uploaded_df.columns

            if "Market Value" in uploaded_df.columns and "Value" not in uploaded_df.columns:
                uploaded_df = uploaded_df.rename(columns={"Market Value": "Value"})

            uploaded_df["Ticker"] = uploaded_df["Ticker"].str.upper().str.strip()

            if has_value:
                uploaded_df["Value"] = pd.to_numeric(uploaded_df["Value"], errors="coerce")
                uploaded_df = uploaded_df.dropna(subset=["Ticker", "Value"])
            elif has_weight:
                uploaded_df["Weight"] = pd.to_numeric(uploaded_df["Weight"], errors="coerce")
                uploaded_df = uploaded_df.dropna(subset=["Ticker", "Weight"])
            else:
                # no Value / Market Value / Weight column at all — leave it blank,
                # the manual-entry sliders below will fill in st.session_state.opt_holdings
                uploaded_df = uploaded_df.dropna(subset=["Ticker"])

            valid_universe = set(new_monthly_data.columns)
            unknown = sorted(set(uploaded_df["Ticker"]) - valid_universe)

            st.session_state.opt_holdings = uploaded_df.to_dict("records")
            st.session_state.opt_file_loaded = True
            st.session_state.opt_unknown_tickers = unknown
            st.session_state.opt_needs_manual_entry = not (has_value)  # NEW
            st.success(f"✅ Loaded {len(st.session_state.opt_holdings)} holdings")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

if uploaded_file is None:
    st.session_state.opt_file_loaded = False
    st.session_state.opt_holdings = []
    st.session_state.opt_unknown_tickers = []
    st.session_state.opt_needs_manual_entry = False

if st.session_state.opt_holdings:
    holdings_df = pd.DataFrame(st.session_state.opt_holdings)

    if st.session_state.get("opt_needs_manual_entry"):
        st.write("**No Value or Weight column found — enter a total portfolio value:**")
        total_value = st.number_input(
            "Total Portfolio Value ($)",
            min_value=0.0, value=100000.0, step=1000.0,
            key="opt_manual_total_value",
        )
        n = len(holdings_df)
        holdings_df["Value"] = total_value / n  # equal-weight split across all holdings
        st.session_state.opt_holdings = holdings_df.to_dict("records")

    st.write("**Current Portfolio:**")
    st.dataframe(holdings_df, hide_index=True, width="stretch")

    if "Value" in holdings_df.columns:
        total_value = holdings_df["Value"].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
        col2.metric("Number of Holdings", len(holdings_df))
        col3.metric("Unrecognized Tickers", len(st.session_state.opt_unknown_tickers))
    else:
        total_weight = holdings_df["Weight"].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Weight", f"{total_weight:.1%}")
        col2.metric("Number of Holdings", len(holdings_df))
        col3.metric("Unrecognized Tickers", len(st.session_state.opt_unknown_tickers))

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

    df_extrap = optimal_weights_appended(opt_portfolio_weights, price_monthly_data, target_date)
    portf_ff3 = portoflio_ff3(df_extrap, new_monthly_data, ff3_monthly)
    
    if isinstance(portf_ff3, str):
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


    st.divider()
    st.header('Rebalance to new FF3 Exposures')

    if "holdings" not in st.session_state:
        st.session_state.holdings = []
    if "input_counter" not in st.session_state:
        st.session_state.input_counter = 0

    # Defaults — only the selected branch below will override these
    max_tickers = None
    turnover_cap = None
    edited_holdings_df = None

    rebalance_constraints = st.radio(
        "Rebalance Constraints",
        ["Keep All Tickers Alike", "Set Turnover Threshold", "Manual Entry"],
        horizontal=True,
    )

    if rebalance_constraints == "Keep All Tickers Alike":
        st.session_state.opt_holdings['Weight'] = .001
        st.session_state.holdings = st.session_state.opt_holdings
        max_tickers = st.session_state.opt_holdings.index.tolist()

    elif rebalance_constraints == "Set Turnover Threshold":
        turnover_pct = st.slider(
            "Max Turnover (% of portfolio that can change)",
            min_value=0, max_value=95, value=10, step=5,
        )
        turnover_cap = turnover_pct / 100

    elif rebalance_constraints == "Manual Entry":
        st.write("**Adjust Current Portfolio:**")

        holdings_df["Min Weight"] = holdings_df["Weight"]  # default: current weight as the floor

        edited_holdings_df = st.data_editor(
            holdings_df,
            hide_index=True,
            width="stretch",
            column_config={
                "Min Weight": st.column_config.NumberColumn(
                    "Min Weight",
                    help="Minimum weight this ticker must keep after rebalancing",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.001,
                    format="%.3f",
                ),
                # lock everything else so only Min Weight is editable
                **{col: st.column_config.Column(disabled=True) for col in holdings_df.columns if col != "Min Weight"}
            },
            key="manual_min_weight_editor",
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input(
            "MKT (Market)",
            min_value=0.5, max_value=1.5, value=1.0, step=0.1,
            format="%.2f", help="Market exposure (typically around 1.0)",
        )
    with col2:
        target_smb = st.number_input(
            "SMB (Size)",
            min_value=-1.0, max_value=1.0, value=0.0, step=0.1,
            format="%.2f", help="Small minus Big (positive = small cap tilt)",
        )
    with col3:
        target_hml = st.number_input(
            "HML (Value)",
            min_value=-1.0, max_value=1.0, value=0.0, step=0.1,
            format="%.2f", help="High minus Low (positive = value tilt)",
        )

    # =============================================================================
    # OPTIMIZE BUTTON
    # =============================================================================
    if st.button("Retrieve Weights", type="primary", width="stretch"):
        with st.spinner("Running optimization... This may take a moment."):
            constrained_holdings = (
                pd.DataFrame(st.session_state.holdings)
                if st.session_state.holdings
                else None
            )
            try:
                results_df, target_date = optimize_portfolio(
                    total_value=total_value,
                    constrained_holdings=constrained_holdings,
                    target_mkt=target_mkt,
                    target_smb=target_smb,
                    target_hml=target_hml,
                    max_tickers=max_tickers,
                    turnover_cap=turnover_cap,
                )

                st.success(
                    f"Optimization Complete — using data as of **{target_date.strftime('%B %Y')}**. Results Below:"
                )

            except Exception as e:
                st.error(f"Optimization failed: {e}")
                st.exception(e)


def optimize_portfolio(
    total_value, constrained_holdings, target_mkt, target_smb, target_hml, max_tickers, turnover_cap
):
    today = pd.Timestamp.now()
    if today.day >= 10:
        target_date = today.replace(day=1)
    else:
        target_date = (today - pd.DateOffset(months=1)).replace(day=1)
    target_date = target_date.normalize()
    curr_weights = target_date.date()
    end = curr_weights - relativedelta(days=1)
    start = curr_weights - relativedelta(months=36)

    opt_portf_weights = front_end_plug(
        target_mkt,
        target_smb,
        target_hml,
        start,
        end,
        total_value,
        50,
        constrained_holdings,
        price_monthly_data,
        new_monthly_data,
        indexgspc1,
        spy_yoy_tickers1,
        max_tickers,
        turnover_cap
    )

    results_df = opt_portf_weights.rename(columns={"New Weights": "Weight"})
    return results_df, target_date
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
