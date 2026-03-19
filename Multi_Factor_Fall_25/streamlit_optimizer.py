import streamlit as st
import pandas as pd
from RunSim_utils import *

st.title("Multi-Factor Investing")
st.caption(
    "Optimize portfolio weights to achieve target three fama-french exposures from S&P 500 equity universe."
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

col1, col2, col3 = st.columns([2, 2, 1])

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
st.header("Target FF3 Exposures")

preset = st.selectbox(
    "Choose a preset or enter custom values",
    [
        "Custom",
        "Market Neutral (1, 0, 0)",
        "Small Value (1, 0.5, 0.5)",
        "Large Growth (1, -0.5, -0.5)",
        "Aggressive Growth (1.2, -0.3, -0.3)",
    ],
)

if preset == "Custom":
    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input(
            "MKT (Market)",
            value=1.0,
            step=0.1,
            format="%.2f",
            help="Market exposure (typically around 1.0)",
        )
    with col2:
        target_smb = st.number_input(
            "SMB (Size)",
            value=0.0,
            step=0.1,
            format="%.2f",
            help="Small minus Big (positive = small cap tilt)",
        )
    with col3:
        target_hml = st.number_input(
            "HML (Value)",
            value=0.0,
            step=0.1,
            format="%.2f",
            help="High minus Low (positive = value tilt)",
        )
elif preset == "Market Neutral (1, 0, 0)":
    target_mkt, target_smb, target_hml = 1.0, 0.0, 0.0
elif preset == "Small Value (1, 0.5, 0.5)":
    target_mkt, target_smb, target_hml = 1.0, 0.5, 0.5
elif preset == "Large Growth (1, -0.5, -0.5)":
    target_mkt, target_smb, target_hml = 1.0, -0.5, -0.5
else:
    target_mkt, target_smb, target_hml = 1.2, -0.3, -0.3

if preset != "Custom":
    col1, col2, col3 = st.columns(3)
    col1.metric("MKT (Market)", f"{target_mkt:.2f}")
    col2.metric("SMB (Size)", f"{target_smb:.2f}")
    col3.metric("HML (Value)", f"{target_hml:.2f}")

st.divider()


# =============================================================================
# OPTIMIZATION FUNCTION
# =============================================================================
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
# OPTIMIZE BUTTON
# =============================================================================
if st.button("Retrieve Weights", type="primary", width="stretch"):
    with st.spinner("Running optimization... This may take a moment."):
        if st.session_state.holdings:
            constrained_holdings = pd.DataFrame(st.session_state.holdings)
        else:
            constrained_holdings = None

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

            use_constrained = st.toggle(
                "Include constrained holdings in simulation",
                value=True,
                disabled=(constrained_holdings is None),
                help="If off, simulation runs without locked positions",
            )

            sim_constrained = constrained_holdings if use_constrained else None

            with st.spinner("Running Monte Carlo simulation..."):
                today = pd.Timestamp.now()
                curr_weights = target_date.date()
                end_sim = curr_weights - relativedelta(days=1)

                oos1_list, oos1_avg, oos1_y = monte_carlo_simulation(
                    1,
                    target_mkt,
                    target_smb,
                    target_hml,
                    end_sim,
                    3,
                    1,
                    total_value,
                    "m",
                    sim_constrained
                )

                avg_drm = final_visuala(oos1_list)

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
