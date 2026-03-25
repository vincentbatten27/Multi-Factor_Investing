import streamlit as st
import pandas as pd

st.title("FF3 Portfolio Optimizer")
st.caption("Step 1: Collect inputs")

# =============================================================================
# INPUT 1: Total Portfolio Value
# =============================================================================
st.header("Total Portfolio Value")

total_value = st.number_input(
    "Total Portfolio Value ($)",
    min_value=1000.0,
    value=1000000.0,
    step=10000.0,
    format="%.2f"
)

st.divider()

# =============================================================================
# INPUT 2: Holdings to Keep (Optional)
# =============================================================================
st.header("Holdings to Keep (Optional)")
st.caption("If you have specific positions you want to keep, enter them here. Otherwise leave blank. *Must be S&P 500 tickers")

# Option A: Manual entry with add/remove buttons
if 'holdings' not in st.session_state:
    st.session_state.holdings = []

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    new_ticker = st.text_input("Ticker", key="new_ticker", placeholder="e.g., AAPL")
with col2:
    new_value = st.number_input("Value ($)", key="new_value", min_value=0.0, step=1000.0, format="%.2f")
with col3:
    st.write("")  # Spacer
    st.write("")  # Spacer
    if st.button("➕ Add"):
        if new_ticker and new_value > 0:
            st.session_state.holdings.append({
                'Ticker': new_ticker.upper().strip(),
                'Value': new_value
            })
            st.rerun()

# Display current holdings
if st.session_state.holdings:
    holdings_df = pd.DataFrame(st.session_state.holdings)
    
    st.write("**Current Holdings:**")
    
    # Show holdings with delete button for each
    for idx, row in holdings_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"**{row['Ticker']}**")
        col2.write(f"${row['Value']:,.2f}")
        if col3.button("🗑️", key=f"del_{idx}"):
            st.session_state.holdings.pop(idx)
            st.rerun()
    
    # Summary
    total_constrained = holdings_df['Value'].sum()
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

# Preset selector
preset = st.selectbox(
    "Choose a preset or enter custom values",
    [
        "Custom",
        "Market Neutral (1, 0, 0)",
        "Small Value (1, 0.5, 0.5)",
        "Large Growth (1, -0.5, -0.5)",
        "Aggressive Growth (1.2, -0.3, -0.3)"
    ]
)

# Set values based on preset
if preset == "Custom":
    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input(
            "MKT (Market)",
            value=1.0,
            step=0.1,
            format="%.2f",
            help="Market exposure (typically around 1.0)"
        )
    with col2:
        target_smb = st.number_input(
            "SMB (Size)",
            value=0.0,
            step=0.1,
            format="%.2f",
            help="Small minus Big (positive = small cap tilt)"
        )
    with col3:
        target_hml = st.number_input(
            "HML (Value)",
            value=0.0,
            step=0.1,
            format="%.2f",
            help="High minus Low (positive = value tilt)"
        )
elif preset == "Market Neutral (1, 0, 0)":
    target_mkt, target_smb, target_hml = 1.0, 0.0, 0.0
elif preset == "Small Value (1, 0.5, 0.5)":
    target_mkt, target_smb, target_hml = 1.0, 0.5, 0.5
elif preset == "Large Growth (1, -0.5, -0.5)":
    target_mkt, target_smb, target_hml = 1.0, -0.5, -0.5
else:  # Aggressive Growth
    target_mkt, target_smb, target_hml = 1.2, -0.3, -0.3

# Display selected values (even for presets)
if preset != "Custom":
    col1, col2, col3 = st.columns(3)
    col1.metric("MKT (Market)", f"{target_mkt:.2f}")
    col2.metric("SMB (Size)", f"{target_smb:.2f}")
    col3.metric("HML (Value)", f"{target_hml:.2f}")

st.divider()

# =============================================================================
# OUTPUT: Show what we collected
from RunSim_utils import *
def optimize_portfolio(total_value, constrained_holdings, target_mkt, target_smb, target_hml):
    start = pd.to_datetime('2022-01-01')#set to begginging of current month and - 3 years
    end= pd.to_datetime('2024-12-31')# set to EOM, or ~3 years + of start 
    
    opt_portf_weights = front_end_plug(target_mkt, target_smb, target_hml,start,end,total_value, 50,constrained_holdings)
    results_df = opt_portf_weights.rename(columns={'New Weights': 'Weights' })
    return results_df
# =============================================================================
st.header("Summary of Inputs")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Portfolio")
    st.write(f"**Total Value:** ${total_value:,.2f}")
    
    if st.session_state.holdings:
        st.write(f"**Constrained Holdings:** {len(st.session_state.holdings)}")
        constrained_df = pd.DataFrame(st.session_state.holdings)
        st.dataframe(constrained_df, hide_index=True, use_container_width=True)
    else:
        st.write("**No constrained holdings**")

with col2:
    st.subheader("Target FF3 Exposures")
    st.write(f"**MKT:** {target_mkt:.2f}")
    st.write(f"**SMB:** {target_smb:.2f}")
    st.write(f"**HML:** {target_hml:.2f}")

st.divider()

# =============================================================================
# DEBUG: Show the actual data structures
# =============================================================================
with st.expander("Debug: See actual data structures"):
    st.write("**This is what will be passed to your optimization function:**")
    
    st.code(f"""
# Variables available:
total_value = {total_value}

constrained_holdings = pd.DataFrame({st.session_state.holdings})
# Shape: {pd.DataFrame(st.session_state.holdings).shape if st.session_state.holdings else (0, 0)}

target_mkt = {target_mkt}
target_smb = {target_smb}
target_hml = {target_hml}
    """, language="python")
    
    if st.session_state.holdings:
        st.write("**Holdings DataFrame:**")
        st.dataframe(pd.DataFrame(st.session_state.holdings))

# =============================================================================
# PLACEHOLDER: Next step button
# =============================================================================
st.divider()

if st.button("Retreive Weights", type="primary", use_container_width=True):
    st.success("Inputs collected! Ready to call optimization function.")
    
    # Create the holdings dataframe
    constrained_holdings = pd.DataFrame(st.session_state.holdings) if st.session_state.holdings else pd.DataFrame(columns=['Ticker', 'Value'])
    
    st.write("**Data ready to pass to your function:**")
    st.write(f"- `total_value`: {total_value}")
    st.write(f"- `constrained_holdings`: DataFrame with {len(constrained_holdings)} rows")
    st.write(f"- `target_mkt`: {target_mkt}")
    st.write(f"- `target_smb`: {target_smb}")
    st.write(f"- `target_hml`: {target_hml}")
    
    st.info("Next step: We'll call your optimization function here with these inputs")
