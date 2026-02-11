import streamlit as st
import pandas as pd
from RunSim_utils import *

st.title("Multi-Factor Investing")
st.caption("Optimize portfolio weights to achieve target three fama-french exposures")

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
st.caption("If you have specific positions you want to keep, enter them here. Otherwise leave blank. *Must be S&P 500 tickers*")

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
# OPTIMIZATION FUNCTION
# =============================================================================
def optimize_portfolio(total_value, constrained_holdings, target_mkt, target_smb, target_hml):
    """
    Optimize portfolio to achieve target FF3 exposures.
    """
    start = pd.to_datetime('2022-01-01')  # Set to beginning of current month - 3 years
    end = pd.to_datetime('2024-12-31')    # Set to EOM, or ~3 years + of start 
    
    # Call the optimization function from RunSim_utils
    opt_portf_weights = front_end_plug(
        target_mkt, 
        target_smb, 
        target_hml,
        start,
        end,
        total_value, 
        50,  # max_positions
        constrained_holdings
    )
    
    # Rename columns for display
    results_df = opt_portf_weights.rename(columns={'New Weights': 'Weight'})
    
    return results_df

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
# OPTIMIZE BUTTON - THE MAIN ACTION
# =============================================================================
st.divider()

if st.button("Retrieve Weights", type="primary", use_container_width=True):
    
    with st.spinner("Running optimization... This may take a moment."):
        
        # Prepare constrained_holdings
        if st.session_state.holdings:
            constrained_holdings = pd.DataFrame(st.session_state.holdings)
        else:
            constrained_holdings = None  # Pass None if no holdings
        
        try:
            # ===================================================================
            # CALL YOUR OPTIMIZATION FUNCTION
            # ===================================================================
            results_df = optimize_portfolio(
                total_value=total_value,
                constrained_holdings=constrained_holdings,
                target_mkt=target_mkt,
                target_smb=target_smb,
                target_hml=target_hml
            )
            # ===================================================================
            
            st.success("Optimization Complete!")
            
            # Show debug info about what was returned
            with st.expander("Debug: Data returned from optimizer"):
                st.write(f"**Shape:** {results_df.shape}")
                st.write(f"**Columns:** {results_df.columns.tolist()}")
                st.write(f"**First few rows:**")
                st.dataframe(results_df.head(10))
            
            st.divider()
            
            # =============================================================================
            # DISPLAY RESULTS
            # =============================================================================
            st.header("Recommended Portfolio Weights")
            
            # Prepare display dataframe
            display_df = results_df.copy()
            
            # Handle different possible column names and formats
            # Add Weight % column if it doesn't exist
            if 'Weight' in display_df.columns and 'Weight %' not in display_df.columns:
                # Check if weights are in decimal format (0.15) or percentage (15.0)
                if display_df['Weight'].max() <= 1.0:
                    # Decimal format - convert to percentage
                    display_df['Weight %'] = (display_df['Weight'] * 100).round(2)
                else:
                    # Already percentage
                    display_df['Weight %'] = display_df['Weight'].round(2)
            
            # Add Value column if it doesn't exist
            if 'Value' not in display_df.columns and 'Weight' in display_df.columns:
                if display_df['Weight'].max() <= 1.0:
                    display_df['Value'] = (display_df['Weight'] * total_value).round(2)
                else:
                    display_df['Value'] = (display_df['Weight'] / 100 * total_value).round(2)
            
            # Format Value as currency string for display
            if 'Value' in display_df.columns:
                display_df['Value $'] = display_df['Value'].apply(lambda x: f"${x:,.2f}")
            
            # Select columns to display
            display_cols = []
            
            # Add ticker column (whatever it's called)
            ticker_col = None
            for possible_name in ['Ticker', 'Symbol', 'Stock', 'ticker', 'symbol']:
                if possible_name in display_df.columns:
                    ticker_col = possible_name
                    display_cols.append(possible_name)
                    display_cols = [possible_name] + [c for c in display_cols if c != possible_name]
                    break
            
            # Add weight percentage
            if 'Weight %' in display_df.columns:
                display_cols.append('Weight %')
            
            # Add value
            if 'Value $' in display_df.columns:
                display_cols.append('Value $')
            elif 'Value' in display_df.columns:
                display_cols.append('Value')
            
            # Add any other important columns
            for col in display_df.columns:
                if col not in display_cols and col not in ['Weight', 'Value']:
                    display_cols.append(col)
            
            # Display the results table
            if ticker_col:
                display_cols = [ticker_col] + [c for c in display_cols if c != ticker_col]
            st.dataframe(
                display_df[display_cols],
                hide_index=False,
                use_container_width=True,
                height=500
            )
            
            # Summary metrics
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Total Positions", len(results_df))
            
            if 'Weight %' in display_df.columns:
                col2.metric("Largest Position", f"{display_df['Weight %'].max():.2f}%")
            
            if 'Value' in display_df.columns:
                total_allocated = display_df['Value'].sum()
                col3.metric("Total Allocated", f"${total_allocated:,.2f}")
            
            # Download button
            st.divider()
            csv = results_df.to_csv(index=True)
            st.download_button(
                "Download Portfolio Weights (CSV)",
                data=csv,
                file_name="ff3_portfolio_weights.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        except Exception as e:
            st.error("Optimization failed!")
            st.error(f"**Error:** {str(e)}")
            
            with st.expander("🐛 Full error traceback"):
                import traceback
                st.code(traceback.format_exc())
            
            st.info("""
            **Troubleshooting:**
            - Make sure RunSim_utils.py is in the same folder
            - Verify that all required data files are accessible
            - Check that constrained tickers are valid S&P 500 symbols
            - Try without constrained holdings first to isolate the issue
            """)
