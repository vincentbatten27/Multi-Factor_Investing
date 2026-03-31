import streamlit as st
import pandas as pd
from RunSim_utils import *
import os

@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    price_monthly_data = pd.read_csv(os.path.join(base_path, 'monthly_prices.csv'))
    price_monthly_data.columns.name = 'Ticker'
    price_monthly_data['Date'] = pd.to_datetime(price_monthly_data['Date'])
    price_monthly_data = price_monthly_data.set_index('Date')

    new_monthly_data = pd.read_csv(os.path.join(base_path, 'monthly_returns.csv'))
    new_monthly_data.columns.name = 'Ticker'
    new_monthly_data['Date'] = pd.to_datetime(new_monthly_data['Date'])
    new_monthly_data = new_monthly_data.set_index('Date')
    new_monthly_data = new_monthly_data.apply(pd.to_numeric, errors='coerce')

    indexgspc1, spy_yoy_tickers1 = run_sp500_data()

    return price_monthly_data, new_monthly_data, indexgspc1, spy_yoy_tickers1

price_monthly_data, new_monthly_data, indexgspc1, spy_yoy_tickers1 = load_data()

st.title("Multi-Factor Investing")
st.caption(
    "Optimize portfolio weights to achieve target three Fama-French exposures from S&P 500 equity universe.<br>"
    "[ℹ️ Documentation](https://github.com/vincentbatten27/Multi-Factor_Investing/blob/main/README.md)",
    unsafe_allow_html=True
)

# =============================================================================
# INPUT 1: Total Portfolio Value
# =============================================================================
st.header("Total Portfolio Value")

total_value = st.number_input(
    "Total Portfolio Value ($)",
    min_value=1000.0,
    value=1000000.0,
    step=10000.0,
    format="%.2f",
)

st.divider()

# =============================================================================
# INPUT 2: Holdings to Keep (Optional)
# =============================================================================
st.header("Holdings to Keep (Optional)")
st.caption(
    "If you have specific positions you want to keep, enter them here. Otherwise leave blank. *Must be S&P 500 tickers*"
)

if "holdings" not in st.session_state:
    st.session_state.holdings = []

if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

col1, col2, col3= st.columns([2, 2, 1])

with col1:
    new_ticker = st.text_input(
        "Ticker",
        placeholder="e.g., AAPL",
        key=f"new_ticker_{st.session_state.input_counter}",
    )
with col2:
    new_value = st.number_input(
        "Value ($)",
        min_value=0.0,
        value=None,
        placeholder="e.g., 10000",
        step=1000.0,
        format="%.2f",
        key=f"new_value_{st.session_state.input_counter}",
    )
with col3:
    st.write("")
    st.write("")
    if st.button("➕ Add"):
        if new_ticker and new_value and new_value > 0:
            st.session_state.holdings.append(
                {"Ticker": new_ticker.upper().strip(), "Value": new_value}
            )
            st.session_state.input_counter += 1
            st.rerun()

if st.session_state.holdings:
    holdings_df = pd.DataFrame(st.session_state.holdings)
    st.write("**Current Holdings:**")
    for idx, row in holdings_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"**{row['Ticker']}**")
        col2.write(f"${row['Value']:,.2f}")
        if col3.button("🗑️", key=f"del_{idx}"):
            st.session_state.holdings.pop(idx)
            st.rerun()
    total_constrained = holdings_df["Value"].sum()
    remaining = total_value - total_constrained
    col1, col2, col3 = st.columns(3)
    col1.metric("Locked Value", f"${total_constrained:,.2f}")
    col2.metric("Remaining to Allocate", f"${remaining:,.2f}")
    col3.metric("Locked %", f"{(total_constrained/total_value*100):.1f}%")
    if st.button("🗑️ Clear All Holdings"):
        st.session_state.holdings = []
        st.rerun()
else:
    st.info("No holdings specified. Will allocate entire portfolio.")

st.divider()


# =============================================================================
# INPUT 3: Target FF3 Factors
# =============================================================================
def get_betas():
    OBJECTIVES = ["max_return", "sharpe", "sortino", "volatility", "downside_vol"]
    betas = {}

    today = pd.Timestamp.now()
    target_date = today.replace(day=1)
    target_date = target_date.normalize()
    curr_weights = target_date.date()
    weights_opt_d = curr_weights - relativedelta(days=1)

    for obj in OBJECTIVES:
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path,f"Front_End_Strategies/{obj}/rebal_explored_{obj}_active_{weights_opt_d.strftime('%Y-%m-%d')}.csv")
        df = pd.read_csv(path)
        curr_df = df.sort_values(by="reward")
        betaA = curr_df.iloc[-1][0]
        betaB = curr_df.iloc[-1][1]
        betaC = curr_df.iloc[-1][2]
        betas[obj] = [betaA, betaB, betaC]

    return betas


st.header("Target FF3 Exposures")
betas = get_betas()

preset = st.selectbox(
    "Choose a preset or enter custom values",
    [
        "Custom",
        f"Max Return ({betas['max_return'][0]}, {betas['max_return'][1]}, {betas['max_return'][2]})",
        f"Minimum Volatility ({betas['volatility'][0]}, {betas['volatility'][1]}, {betas['volatility'][2]})",
        f"Max Sharpe ({betas['sharpe'][0]}, {betas['sharpe'][1]}, {betas['sharpe'][2]})",
        f"Max Sortino ({betas['sortino'][0]}, {betas['sortino'][1]}, {betas['sortino'][2]})",
        f"Minimum Downside Volatility ({betas['downside_vol'][0]}, {betas['downside_vol'][1]}, {betas['downside_vol'][2]})",
    ],
)


PRESET_TO_OBJ = {
    "Max Return": "max_return",
    "Minimum Volatility": "volatility",
    "Max Sharpe": "sharpe",
    "Max Sortino": "sortino",
    "Minimum Downside Volatility": "downside_vol",
}
if preset == "Custom":
    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input("MKT (Market)",min_value = 0.5, max_value = 1.5, value=1.0, step=0.1, format="%.2f",
            help="Market exposure (typically around 1.0)")
    with col2:
        target_smb = st.number_input("SMB (Size)", min_value = -1.0, max_value = 1.0, value = 0.0, step=0.1, format="%.2f",
            help="Small minus Big (positive = small cap tilt)")
    with col3:
        target_hml = st.number_input("HML (Value)", min_value = -1.0, max_value = 1.0,  value=0.0, step=0.1, format="%.2f",
            help="High minus Low (positive = value tilt)")
    obj_key = None
else:
    obj_key = next((v for k, v in PRESET_TO_OBJ.items() if k in preset), None)
    target_mkt, target_smb, target_hml = betas[obj_key]
    col1, col2, col3 = st.columns(3)
    col1.metric("MKT (Market)", f"{target_mkt:.2f}")
    col2.metric("SMB (Size)", f"{target_smb:.2f}")
    col3.metric("HML (Value)", f"{target_hml:.2f}")

st.divider()

# =============================================================================
# OPTIMIZATION FUNCTION
# =============================================================================

def final_visuala(ddfs, expected_betas=None, obj=None):
    import plotly.graph_objects as go

    concatenated_df = pd.concat(ddfs, axis=1)
    averaged_df_A = concatenated_df.filter(like="SP_500").mean(axis=1)
    averaged_df_B = concatenated_df.filter(like="Optimized Portfolio").mean(axis=1)
    averaged_df = pd.DataFrame(
        {"SP_500": averaged_df_A, "Optimized Portfolio": averaged_df_B}
    )

    fig = go.Figure()

    # Individual portfolio runs (faint blue lines)
    for i, df in enumerate(ddfs):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Optimized Portfolio"],
                mode="lines",
                line=dict(color="rgba(0, 100, 255, 0.15)", width=1),
                showlegend=(i == 0),
                name="Individual Runs",
                hovertemplate="%{x|%b %Y}<br>Value: $%{y:.3f}<extra></extra>",
            )
        )

    # SP500
    fig.add_trace(
        go.Scatter(
            x=averaged_df.index,
            y=averaged_df["SP_500"],
            mode="lines+markers",
            name="S&P 500",
            line=dict(color="black", width=2, dash="dash"),
            marker=dict(color="black", size=5, symbol="circle"),
            hovertemplate="%{x|%b %Y}<br>S&P 500: $%{y:.3f}<extra></extra>",
        )
    )

    # Optimized Portfolio (average)
    beta_hover = ''
    if expected_betas:
        beta_lines = [
            f"Month {i+1}: β_mkt={b[0]}, β_smb={b[1]}, β_hml={b[2]}"
            for i, b in enumerate(expected_betas)
        ]
        beta_hover = "<br>" + "<br>".join(beta_lines)

    fig.add_trace(
        go.Scatter(
            x=averaged_df.index,
            y=averaged_df["Optimized Portfolio"],
            mode="lines+markers",
            name="Optimized Portfolio",
            line=dict(color="royalblue", width=2.5),
            marker=dict(color="royalblue", size=5, symbol="circle"),
            customdata=(
                expected_betas
                if expected_betas
                else [[None, None, None]] * len(averaged_df)
            ),
            hovertemplate="%{x|%b %Y}<br>Portfolio: $%{y:.3f}<br>"
            "β<sub>Mkt</sub>=%{customdata[0]}, "
            "β<sub>SMB</sub>=%{customdata[1]}, "
            "β<sub>HML</sub>=%{customdata[2]}"
            "<extra></extra>",
        )
    )

    # Month indicators
    for date in averaged_df.index:
        fig.add_vline(
            x=date, line=dict(color="rgba(150, 150, 150, 0.2)", width=1, dash="dot")
        )
    obj_label = obj_key.replace("_", " ").title() if obj_key else "Custom"
    fig.update_layout(
        title=dict(
            text=f"Optimized Portfolio vs S&P 500 — {obj_label}<br><sup>Growth of $1 invested</sup>",
            font=dict(size=18),
        ),
        xaxis=dict(title="Date", tickformat="%b %Y", tickangle=-45, showgrid=False),
        yaxis=dict(
            title="Value ($)",
            tickprefix="$",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.3)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=500,
    )

    st.plotly_chart(fig, width="stretch")

    # =========================================================================
    # Performance Metrics
    # =========================================================================
    def compute_metrics(series, label):
        start = str(series.index[0])
        end   = str(series.index[-1])
        ff3_monthly = famafrenchreturns()
        rf = ff3_monthly[start:end]['RF']
        rf = rf.mean()
        # Convert cumulative values to period returns
        returns = series.pct_change().dropna()
        n = len(returns)
        months = n

        total_return = (series.iloc[-1] / series.iloc[0]) - 1
        ann_return = (1 + total_return) ** (12 / months) - 1
        volatility = returns.std() * np.sqrt(12)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(12)
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

    metrics = pd.DataFrame(
        [
            compute_metrics(averaged_df["Optimized Portfolio"], "Optimized Portfolio"),
            compute_metrics(averaged_df["SP_500"], "S&P 500"),
        ]
    ).set_index("Metric")
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

    return averaged_df

def optimize_portfolio(
    total_value, constrained_holdings, target_mkt, target_smb, target_hml
):
    today = pd.Timestamp.now()
    if today.day >= 2:
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
    )

    results_df = opt_portf_weights.rename(columns={"New Weights": "Weight"})
    return results_df, target_date


# =============================================================================
# SUMMARY OF INPUTS
# =============================================================================
st.header("Summary of Inputs")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Portfolio")
    st.write(f"**Total Value:** ${total_value:,.2f}")
    if st.session_state.holdings:
        st.write(f"**Constrained Holdings:** {len(st.session_state.holdings)}")
        constrained_df = pd.DataFrame(st.session_state.holdings)
        st.dataframe(constrained_df, hide_index=True, width="stretch")
    else:
        st.write("**No constrained holdings**")
with col2:
    st.subheader("Target FF3 Exposures")
    st.write(f"**MKT:** {target_mkt:.2f}")
    st.write(f"**SMB:** {target_smb:.2f}")
    st.write(f"**HML:** {target_hml:.2f}")

st.divider()

with st.expander("Debug: See actual data structures"):
    st.write("**This is what will be passed to your optimization function:**")
    st.code(
        f"""
total_value = {total_value}
constrained_holdings = pd.DataFrame({st.session_state.holdings})
# Shape: {pd.DataFrame(st.session_state.holdings).shape if st.session_state.holdings else (0, 0)}
target_mkt = {target_mkt}
target_smb = {target_smb}
target_hml = {target_hml}
    """,
        language="python",
    )
    if st.session_state.holdings:
        st.write("**Holdings DataFrame:**")
        st.dataframe(pd.DataFrame(st.session_state.holdings))

st.divider()

# =============================================================================
# SIMULATION OPTIONS - before the button
# =============================================================================
st.subheader("Simulation Options")

col1, col2 = st.columns([3,1])

with col1:
    use_constrained_sim = st.toggle(
        "Include constrained holdings in Monte Carlo simulation",
        value=True,
        disabled=(len(st.session_state.holdings) == 0) or (preset != "Custom"),
        help="If off, simulation runs without locked positions \nSelecting Optimized Beta will automatically override and exclude any Custom Constrained Holdings",
    )
    max_runs = 25 if preset == "Custom" else 2
    out_years = st.number_input(
        "Testing Years",
        min_value=1,
        max_value=max_runs,
        value=1,
        step=1,
        help="Number of years to see results for",
    )

with col2:
    num_runs = st.number_input(
        "Monte Carlo Runs",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
        help="Number of Monte Carlo simulation runs"
    )

st.caption("Each year of testing takes approximately 30–45 seconds to run.")
st.divider()

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
        sim_constrained = constrained_holdings if use_constrained_sim else None

        try:
            results_df, target_date = optimize_portfolio(
                total_value=total_value,
                constrained_holdings=constrained_holdings,
                target_mkt=target_mkt,
                target_smb=target_smb,
                target_hml=target_hml,
            )

            st.success(
                f"Optimization Complete — using data as of **{target_date.strftime('%B %Y')}**. Results Below:"
            )
            st.info("Scroll down to view Historical Monte Carlo Simulation and performance metrics.")
            with st.expander("Debug: Data returned from optimizer"):
                st.write(f"**Shape:** {results_df.shape}")
                st.write(f"**Columns:** {results_df.columns.tolist()}")
                st.write(f"**First few rows:**")
                st.dataframe(results_df.head(10))

            st.divider()

            st.header("Recommended Portfolio Weights")

            display_df = results_df.copy()
            if "Weight" in display_df.columns and "Weight %" not in display_df.columns:
                if display_df["Weight"].max() <= 1.0:
                    display_df["Weight %"] = (display_df["Weight"] * 100).round(2)
                else:
                    display_df["Weight %"] = display_df["Weight"].round(2)

            if "Value" not in display_df.columns and "Weight" in display_df.columns:
                if display_df["Weight"].max() <= 1.0:
                    display_df["Value"] = (display_df["Weight"] * total_value).round(2)
                else:
                    display_df["Value"] = (
                        display_df["Weight"] / 100 * total_value
                    ).round(2)

            if "Value" in display_df.columns:
                display_df["Value $"] = display_df["Value"].apply(
                    lambda x: f"${x:,.2f}"
                )

            display_cols = []
            ticker_col = None
            for possible_name in ["Ticker", "Symbol", "Stock", "ticker", "symbol"]:
                if possible_name in display_df.columns:
                    ticker_col = possible_name
                    break
            if ticker_col:
                display_cols.append(ticker_col)
            if "Weight %" in display_df.columns:
                display_cols.append("Weight %")
            if "Value $" in display_df.columns:
                display_cols.append("Value $")
            elif "Value" in display_df.columns:
                display_cols.append("Value")
            for col in display_df.columns:
                if col not in display_cols and col not in ["Weight", "Value"]:
                    display_cols.append(col)

            st.dataframe(
                display_df[display_cols], hide_index=False, width="stretch", height=500
            )

            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Positions", len(results_df))
            if "Weight %" in display_df.columns:
                col2.metric("Largest Position", f"{display_df['Weight %'].max():.4f}%")
            if "Value" in display_df.columns:
                total_allocated = display_df["Value"].sum()
                col3.metric("Total Allocated", f"${total_allocated:,.2f}")

            st.divider()
            csv = results_df.to_csv(index=True)
            st.download_button(
                "Download Portfolio Weights (CSV)",
                data=csv,
                file_name="ff3_portfolio_weights.csv",
                mime="text/csv",
                width="stretch",
            )

            # =================================================================
            # MONTE CARLO SIMULATION
            # =================================================================
            st.divider()
            st.header("Historical Monte Carlo Simulation")

            with st.spinner("Running Monte Carlo simulation..."):
                curr_weights = target_date.date()
                end_sim = curr_weights - relativedelta(days=1)
                if preset == "Custom":
                    key = 'm'
                    obj_key = None
                else: 
                    key = 'drm'
                    obj_key = next((v for k, v in PRESET_TO_OBJ.items() if k in preset), None)

                # rebalace_opt_weights is opt_portf_weights for each period
                oos1_list, oos1_avg, oos1_y, expected_betas, rebalance_opt_weights = (
                    monte_carlo_simulation(
                        num_runs,
                        target_mkt,
                        target_smb,
                        target_hml,
                        end_sim,
                        3,
                        out_years,
                        total_value,
                        key,
                        sim_constrained,
                        price_monthly_data,
                        new_monthly_data,
                        indexgspc1,
                        spy_yoy_tickers1,
                        obj_key,
                    )
                )

                avg_drm = final_visuala(oos1_list, expected_betas,obj_key)
                # weights_port = rebalanced_optimal_weights_m(
                #     oos1_list[0], rebalance_opt_weights, price_monthly_data
                # )
                st.caption(
                "⚠️ **Note:** Risk-adjusted metrics over short periods (e.g., 1 year) may not be reflective of long-run expected performance — "
                "a single favorable or unfavorable market regime can significantly skew Sharpe and Sortino. <br>"
                "Return streams do not account for short-term capital gains taxes or dividend reinvestment.",
                unsafe_allow_html=True
    )

        except Exception as e:
            st.error("Optimization failed!")
            st.error(f"**Error:** {str(e)}")
            with st.expander("🐛 Full error traceback"):
                import traceback

                st.code(traceback.format_exc())
            st.info(
                """
            **Troubleshooting:**
            - Make sure RunSim_utils.py is in the same folder
            - Verify that all required data files are accessible
            - Check that constrained tickers are valid S&P 500 symbols
            - Try without constrained holdings first to isolate the issue
            """
            )
footer = """
<style>
.footer {
    position: relative;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: transparent; /* Changed to transparent to blend with Streamlit themes */
    color: #31333F;
    text-align: center;
    padding: 20px 10px; /* Added vertical padding for breathing room */
    font-size: 14px;
    border-top: 1px solid #e6e6e6;
    margin-top: 50px; /* Pushes it away from your last chart/table */
}
.footer a:hover {
    text-decoration: underline;
}
</style>

<div class="footer">
    <p>Developed by <b>Vincent Batten</b> | 
    ✉ Email <a href="mailto:vincentbatten27@gmail.com?subject=Beta Optimization App Inquiry">vincentbatten27@gmail.com</a> | 
    <i>Original Logic by</i> <b>Johanan Pranesh</b><br>
    Created alongside <b>Nate Songstad & Kshitij Bhandari</b><br>
    Sponsored by: <b>Jordan Weintraub</b></p>
</div>
"""

# Place this line at the very end of your script
st.markdown(footer, unsafe_allow_html=True)
