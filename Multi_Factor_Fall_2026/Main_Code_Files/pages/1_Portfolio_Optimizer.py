import streamlit as st
import pandas as pd
from app_common import load_data
from RunSim_utils import *
import statsmodels.api as sm
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio Optimizer")

price_monthly_data, new_monthly_data, ff3_monthly, indexgspc1, spy_yoy_tickers1 = load_data()
# One date rule for the whole page: last month's data is complete by DATA_READY_DAY,
# so the 36-month window ends on the last day of the last complete month.
DATA_READY_DAY = 3
today = pd.Timestamp.now().normalize()
if today.day >= DATA_READY_DAY:
    target_date = today.replace(day=1)
else:
    target_date = (today - pd.DateOffset(months=1)).replace(day=1)
window_end = target_date - pd.Timedelta(days=1)   # e.g. 2026-08-31 -> window Sep 2023 .. Aug 2026



def compute_metrics(series, label, ff3):
    """Performance stats for a growth-of-$1 series of monthly points."""
    returns = series.pct_change().dropna()
    months = len(returns)

    # Monthly RF over exactly the return months (divide by 100 if FF is in percent)
    rf_m = ff3.loc[returns.index[0]:returns.index[-1], "RF"]
    rf_mean = rf_m.mean() if len(rf_m) else 0.0
    rf_m_aligned = rf_m.reindex(returns.index, method="ffill").fillna(rf_mean)
    rf = (1 + rf_mean) ** 12 - 1          # scalar annual RF

    total_return = (series.iloc[-1] / series.iloc[0]) - 1
    ann_return = (1 + total_return) ** (12 / months) - 1
    volatility = returns.std() * np.sqrt(12)
    downside_vol = np.sqrt(((returns - rf_m_aligned).clip(upper=0) ** 2).mean()) * np.sqrt(12)
    sharpe = (ann_return - rf) / volatility if volatility != 0 else np.nan
    sortino = (ann_return - rf) / downside_vol if downside_vol != 0 else np.nan

    return {
        "Metric": label,
        "Total Return": f"{total_return*100:.2f}%",
        "Annualized Return": f"{ann_return*100:.2f}%",
        "Volatility": f"{volatility*100:.2f}%",
        "Downside Vol": f"{downside_vol*100:.2f}%",
        "Sharpe Ratio": f"{sharpe:.3f}",
        "Sortino Ratio": f"{sortino:.3f}",
    }


def oos_compare_chart(perf_df):
    """Growth of $1: optimized weights vs current weights, each line toggleable."""
    c1, c2 = st.columns(2)
    show_new = c1.checkbox("Optimized Portfolio", value=True, key="oos_show_new")
    show_old = c2.checkbox("Current Portfolio", value=True, key="oos_show_old")

    fig = go.Figure()
    if show_old:
        fig.add_trace(go.Scatter(
            x=perf_df.index, y=perf_df["Old Portfolio"],
            mode="lines+markers", name="Current Portfolio",
            line=dict(color="black", width=2, dash="dash"),
            marker=dict(color="black", size=5, symbol="circle"),
            hovertemplate="%{x|%b %Y}<br>Current: $%{y:.3f}<extra></extra>",
        ))
    if show_new:
        fig.add_trace(go.Scatter(
            x=perf_df.index, y=perf_df["Optimized Portfolio"],
            mode="lines+markers", name="Optimized Portfolio",
            line=dict(color="royalblue", width=2.5),
            marker=dict(color="royalblue", size=5, symbol="circle"),
            hovertemplate="%{x|%b %Y}<br>Optimized: $%{y:.3f}<extra></extra>",
        ))
    if not (show_new or show_old):
        st.info("Select at least one portfolio to plot.")
        return

    for date in perf_df.index:
        fig.add_vline(x=date, line=dict(color="rgba(150, 150, 150, 0.2)", width=1, dash="dot"))

    fig.update_layout(
        title=dict(
            text="Optimized vs Current Portfolio<br><sup>Growth of $1 invested</sup>",
            font=dict(size=18),
        ),
        xaxis=dict(title="Date", tickformat="%b %Y", tickangle=-45, showgrid=False),
        yaxis=dict(title="Value ($)", tickprefix="$", showgrid=True,
                   gridcolor="rgba(200,200,200,0.3)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
    )
    st.plotly_chart(fig, width="stretch")

    # Metrics for whichever portfolios are toggled on
    rows = []
    if show_new:
        rows.append(compute_metrics(perf_df["Optimized Portfolio"], "Optimized Portfolio", ff3_monthly))
    if show_old:
        rows.append(compute_metrics(perf_df["Old Portfolio"], "Current Portfolio", ff3_monthly))
    metrics = pd.DataFrame(rows).set_index("Metric")
    st.dataframe(
        metrics.style.apply(
            lambda col: [
                "color: royalblue" if idx == "Optimized Portfolio" else "color: black"
                for idx in metrics.index
            ],
            axis=0,
        ),
        width="stretch",
    )


st.title("Portfolio Optimizer")
st.caption(
    "Analyze an existing portfolio's Fama-French factor exposures against a target, "
    "and see whether getting there means reweighting your current holdings or adding/dropping positions.<br>"
    "[ℹ️ Documentation](https://github.com/vincentbatten27/Multi-Factor_Investing/blob/main/README.md)",
    unsafe_allow_html=True,
)

st.divider()

# =============================================================================
# INPUT: Total Portfolio Value
# =============================================================================
st.header("Total Portfolio Value")

total_value = st.number_input(
    "Total Portfolio Value ($)",
    min_value=1000.0,
    value=1000000.0,
    step=10000.0,
    format="%.2f",
    key="opt_total_value",
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

            recent = new_monthly_data.loc[new_monthly_data.index.max() - pd.DateOffset(months=36):]
            valid_universe = set(recent.columns[recent.notna().any()])  # column exists AND has recent data
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
    st.session_state.opt_results = None

if st.session_state.opt_holdings:
    holdings_df = pd.DataFrame(st.session_state.opt_holdings)

    if st.session_state.get("opt_needs_manual_entry"):
        st.caption("No Value or Weight column found — splitting the Total Portfolio Value above equally across holdings.")
        n = len(holdings_df)
        holdings_df["Value"] = total_value * holdings_df['Weight'] # equal-weight split across all holdings
        st.session_state.opt_holdings = holdings_df.to_dict("records")

    st.write("**Current Portfolio:**")
    st.dataframe(holdings_df, hide_index=True, width="stretch")

    if "Value" in holdings_df.columns:
        holdings_value = holdings_df["Value"].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Uploaded Holdings Value", f"${holdings_value:,.2f}")
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

curr_ff3 = None
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

    df_extrap = optimal_weights_appended(opt_portfolio_weights, price_monthly_data, window_end)
    portf_ff3 = portoflio_ff3(df_extrap, new_monthly_data, ff3_monthly)
    
    if isinstance(portf_ff3, str):
        st.warning(portf_ff3)
    else:
        curr_ff3 = portf_ff3
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

# =============================================================================
# PLACEHOLDER: Graphing and Rebalancing
# =============================================================================
def optimize_portfolio(
    total_value, constrained_holdings, target_mkt, target_smb, target_hml, max_tickers, turnover_cap
):
    # uses the page-level target_date so the optimizer and the FF3 checks share one window
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




st.header('Rebalance to new FF3 Exposures')

if not st.session_state.opt_holdings:
    st.info("Upload a CSV of your holdings first to rebalance.")
else:
    holdings_df = pd.DataFrame(st.session_state.opt_holdings)
    if "Weight" not in holdings_df.columns:   # Value-only uploads
        holdings_df["Weight"] = holdings_df["Value"] / holdings_df["Value"].sum()

    # separate key from the Constructor page, which also uses st.session_state.holdings
    st.session_state.opt_constrained = []
    if "input_counter" not in st.session_state:
        st.session_state.input_counter = 0

    max_tickers = None
    turnover_cap = None
    edited_holdings_df = None

    rebalance_constraints = st.radio(
        "Rebalance Constraints",
        ["Keep All Tickers Alike", "Set Turnover Threshold", "Manual Entry"],
        horizontal=True,
    )

    if rebalance_constraints == "Keep All Tickers Alike":
        holdings_df["Min Weight"] = .001
        st.session_state.opt_constrained = holdings_df.to_dict("records")
        max_tickers = holdings_df["Ticker"].tolist()

    elif rebalance_constraints == "Set Turnover Threshold":
        turnover_pct = st.slider(
            "Max Turnover (% of portfolio that can change)",
            min_value=5, max_value=100, value=10, step=5,
        )
        turnover_cap = turnover_pct / 100
        constrained_df = holdings_df.copy()
        constrained_df["Min Weight"] = constrained_df["Weight"] * (1 - turnover_cap)
        st.session_state.opt_constrained = constrained_df.to_dict("records")
        
    elif rebalance_constraints == "Manual Entry":
        st.write("**Adjust Current Portfolio:**")

        holdings_df["Min Weight"] = holdings_df["Weight"]

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
                **{col: st.column_config.Column(disabled=True) for col in holdings_df.columns if col != "Min Weight"}
            },
            key="manual_min_weight_editor",
        )
        st.session_state.opt_constrained = edited_holdings_df.to_dict("records")

    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input(
            "MKT (Market)", min_value=0.5, max_value=1.5, value=1.0, step=0.1,
            format="%.2f", help="Market exposure (typically around 1.0)",
        )
    with col2:
        target_smb = st.number_input(
            "SMB (Size)", min_value=-1.0, max_value=1.0, value=0.0, step=0.1,
            format="%.2f", help="Small minus Big (positive = small cap tilt)",
        )
    with col3:
        target_hml = st.number_input(
            "HML (Value)", min_value=-1.0, max_value=1.0, value=0.0, step=0.1,
            format="%.2f", help="High minus Low (positive = value tilt)",
        )

    # =============================================================================
    # OPTIMIZE BUTTON
    # =============================================================================
    if st.button("Retrieve Weights", type="primary", width="stretch"):
        with st.spinner("Running optimization... This may take a moment."):
            constrained_holdings = (
                pd.DataFrame(st.session_state.opt_constrained)
                if st.session_state.opt_constrained
                else None
            )
            try:
                results_df, opt_date = optimize_portfolio(
                    total_value=total_value,
                    constrained_holdings=constrained_holdings,
                    target_mkt=target_mkt,
                    target_smb=target_smb,
                    target_hml=target_hml,
                    max_tickers=max_tickers,
                    turnover_cap=turnover_cap,
                )
                # FF3 of the new portfolio — same method/window as the current portfolio's betas above
                new_w = results_df[["Weight"]].rename(columns={"Weight": "New Weight"})
                new_extrap = optimal_weights_appended(new_w, price_monthly_data, window_end)
                new_ff3 = portoflio_ff3(new_extrap, new_monthly_data, ff3_monthly)

                st.session_state.opt_results = {
                    "weights": results_df,
                    "date": opt_date,
                    "ff3": new_ff3,
                    "targets": {"Mkt-RF": target_mkt, "SMB": target_smb, "HML": target_hml},
                    "total_value": total_value,
                }
                st.success(
                    f"Optimization Complete — using data as of **{opt_date.strftime('%B %Y')}**. Results Below:"
                )
            except Exception as e:
                st.session_state.opt_results = None
                st.error(f"Optimization failed: {e}")
                st.exception(e)

    # =============================================================================
    # RESULTS (kept in session state so they survive reruns, e.g. the download button)
    # =============================================================================
    res = st.session_state.get("opt_results")
    if res is not None:
        results_df = res["weights"]
        res_value = res["total_value"]

        # ---- New portfolio FF3 betas vs target (and current) ----
        st.divider()
        st.header("New Portfolio FF3 Betas")
        new_ff3 = res["ff3"]
        if isinstance(new_ff3, str):
            st.warning(new_ff3)
        else:
            col1, col2, col3, col4 = st.columns(4)
            for col, f in zip([col1, col2, col3], ["Mkt-RF", "SMB", "HML"]):
                curr_txt = f" | Current: {curr_ff3[f]:.3f}" if curr_ff3 is not None else ""
                col.metric(
                    f,
                    f"{new_ff3[f]:.3f}",
                    delta=f"{new_ff3[f] - res['targets'][f]:+.3f} vs target",
                    delta_color="off",
                    help=f"Target: {res['targets'][f]:.2f}{curr_txt} | ± {new_ff3[f + '_SE']:.3f} SE",
                )
            col4.metric("R²", f"{new_ff3['R_squared']:.3f}", help="Share of monthly portfolio return variance explained by the 3 factors")

        # ---- Recommended weights: current vs new ----
        st.divider()
        st.header("Recommended Portfolio Weights")

        curr_df = holdings_df[~holdings_df["Ticker"].isin(st.session_state.opt_unknown_tickers)]
        curr_w = curr_df.set_index("Ticker")["Weight"]

        display_df = pd.DataFrame({"New Weight": results_df["Weight"]}).join(
            curr_w.rename("Current Weight"), how="outer"
        ).fillna(0.0)
        display_df["Change"] = display_df["New Weight"] - display_df["Current Weight"]
        display_df["Status"] = "Reweighted"
        display_df.loc[display_df["Current Weight"] == 0, "Status"] = "Added"
        display_df.loc[display_df["New Weight"] == 0, "Status"] = "Dropped"
        display_df["Value $"] = (display_df["New Weight"] * res_value).apply(lambda x: f"${x:,.2f}")
        for c in ["New Weight", "Current Weight", "Change"]:
            display_df[c + " %"] = (display_df[c] * 100).round(2)
        display_df = display_df.sort_values("New Weight", ascending=False)
        display_df.index.name = "Ticker"

        st.dataframe(
            display_df[["Status", "Current Weight %", "New Weight %", "Change %", "Value $"]],
            hide_index=False, width="stretch", height=500,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Positions", int((display_df["New Weight"] > 0).sum()))
        col2.metric("Added", int((display_df["Status"] == "Added").sum()))
        col3.metric("Dropped", int((display_df["Status"] == "Dropped").sum()))
        col4.metric("Turnover", f"{display_df['Change'].abs().sum() / 2:.1%}",
                    help="One-way turnover: sum of |change in weight| / 2")

        csv = display_df[["Status", "Current Weight", "New Weight", "Change"]].assign(
            Value=display_df["New Weight"] * res_value
        ).to_csv(index=True)
        st.download_button(
            "Download Rebalanced Weights (CSV)",
            data=csv,
            file_name="ff3_rebalanced_weights.csv",
            mime="text/csv",
            width="stretch",
        )
        # =================================================================
        # MONTE CARLO SIMULATION
        # =================================================================
        st.divider()
        st.header("Historical Monte Carlo Simulation")
        st.subheader("Simulation Options")

        col1 = st.columns([1, 1])
        out_years = st.number_input(
                "Testing Years",
                min_value=1,
                max_value=25,
                value=1,
                step=1,
                help="Number of years to see results for",
            )
        with st.spinner("Running Monte Carlo simulation..."):
            # out_of_sampless reads new_monthly_data as a RunSim_utils global
            import RunSim_utils
            RunSim_utils.new_monthly_data = new_monthly_data
            opt_w = display_df.loc[display_df["New Weight"] != 0, ["New Weight"]].rename(columns={"New Weight": "Weight"})
            old_w = display_df.loc[display_df["Current Weight"] != 0, ["Current Weight"]].rename(columns={"Current Weight": "Weight"})
            oos1_list = out_of_sampless(target_date - relativedelta(years=out_years), target_date, opt_w, old_w)
        oos_compare_chart(oos1_list)
    

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
