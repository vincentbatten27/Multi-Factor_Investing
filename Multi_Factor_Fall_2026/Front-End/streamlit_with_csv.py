import streamlit as st
import pandas as pd
import io

st.title("FF3 Portfolio Optimizer")
st.caption("Step 1: Collect inputs")

# =============================================================================
# INPUT 1: Total Portfolio Value
# =============================================================================
st.header("1️⃣ Portfolio Value")

total_value = st.number_input(
    "Total Portfolio Value ($)",
    min_value=1000.0,
    value=1000000.0,
    step=10000.0,
    format="%.2f"
)

st.divider()

# =============================================================================
# INPUT 2: Holdings to Keep (Optional) - WITH CSV UPLOAD
# =============================================================================
st.header("2️⃣ Holdings to Keep (Optional)")

# Choose input method
input_method = st.radio(
    "How would you like to enter holdings?",
    ["No holdings to keep", "Manual entry", "Upload CSV"],
    horizontal=True
)

constrained_holdings = pd.DataFrame(columns=['Ticker', 'Value'])

if input_method == "Manual entry":
    # Initialize session state
    if 'holdings' not in st.session_state:
        st.session_state.holdings = []
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        new_ticker = st.text_input("Ticker", key="new_ticker", placeholder="e.g., AAPL")
    with col2:
        new_value = st.number_input("Value ($)", key="new_value", min_value=0.0, step=1000.0, format="%.2f")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add"):
            if new_ticker and new_value > 0:
                st.session_state.holdings.append({
                    'Ticker': new_ticker.upper().strip(),
                    'Value': new_value
                })
                st.rerun()
    
    # Display holdings
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
        
        constrained_holdings = holdings_df
        
        if st.button("🗑️ Clear All Holdings"):
            st.session_state.holdings = []
            st.rerun()
    else:
        st.info("No holdings added yet.")

elif input_method == "Upload CSV":
    st.caption("Upload a CSV file with columns: Ticker, Value")
    
    # Sample CSV download
    sample_csv = """Ticker,Value
AAPL,50000
TSLA,50000
MSFT,30000"""
    
    st.download_button(
        "📥 Download Sample CSV Template",
        data=sample_csv,
        file_name="holdings_template.csv",
        mime="text/csv"
    )
    
    uploaded_file = st.file_uploader("Upload Holdings CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            constrained_holdings = pd.read_csv(uploaded_file)
            
            # Validate columns
            if 'Ticker' not in constrained_holdings.columns or 'Value' not in constrained_holdings.columns:
                st.error("CSV must have 'Ticker' and 'Value' columns!")
                constrained_holdings = pd.DataFrame(columns=['Ticker', 'Value'])
            else:
                # Clean up data
                constrained_holdings['Ticker'] = constrained_holdings['Ticker'].str.upper().str.strip()
                constrained_holdings['Value'] = pd.to_numeric(constrained_holdings['Value'], errors='coerce')
                constrained_holdings = constrained_holdings.dropna()
                
                st.success(f"✅ Loaded {len(constrained_holdings)} holdings")
                st.dataframe(constrained_holdings, hide_index=True, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            constrained_holdings = pd.DataFrame(columns=['Ticker', 'Value'])

# Show summary if holdings exist
if len(constrained_holdings) > 0:
    total_constrained = constrained_holdings['Value'].sum()
    remaining = total_value - total_constrained
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Locked Value", f"${total_constrained:,.2f}")
    col2.metric("Remaining to Allocate", f"${remaining:,.2f}")
    col3.metric("Locked %", f"{(total_constrained/total_value*100):.1f}%")
    
    if remaining < 0:
        st.error("⚠️ Holdings exceed total portfolio value!")

st.divider()

# =============================================================================
# INPUT 3: Target FF3 Factors
# =============================================================================
st.header("3️⃣ Target FF3 Exposures")

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

if preset == "Custom":
    col1, col2, col3 = st.columns(3)
    with col1:
        target_mkt = st.number_input("MKT (Market)", value=1.0, step=0.1, format="%.2f")
    with col2:
        target_smb = st.number_input("SMB (Size)", value=0.0, step=0.1, format="%.2f")
    with col3:
        target_hml = st.number_input("HML (Value)", value=0.0, step=0.1, format="%.2f")
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
    col1.metric("MKT", f"{target_mkt:.2f}")
    col2.metric("SMB", f"{target_smb:.2f}")
    col3.metric("HML", f"{target_hml:.2f}")

st.divider()

# =============================================================================
# OPTIMIZE BUTTON
# =============================================================================
st.header("🎯 Ready to Optimize")

col1, col2 = st.columns(2)

with col1:
    st.write("**Portfolio:**")
    st.write(f"Total: ${total_value:,.2f}")
    st.write(f"Holdings: {len(constrained_holdings)}")

with col2:
    st.write("**Target Exposures:**")
    st.write(f"MKT={target_mkt:.2f}, SMB={target_smb:.2f}, HML={target_hml:.2f}")

if st.button("▶️ Run Optimization", type="primary", use_container_width=True):
    st.success("✅ Inputs collected!")
    
    st.write("**Ready to pass to optimization function:**")
    st.code(f"""
total_value = {total_value}
constrained_holdings = pd.DataFrame with {len(constrained_holdings)} rows
target_mkt = {target_mkt}
target_smb = {target_smb}
target_hml = {target_hml}
    """)
    
    st.info("👉 Next: Add your optimization function call here")
