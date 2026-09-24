# Streamlit Input Collection - Quick Reference

## What This Does

This app collects exactly the inputs you need:

1. **Total Portfolio Value** (single number)
2. **Constrained Holdings** (DataFrame with Ticker/Value)
3. **Target FF3 Factors** (MKT, SMB, HML)

## How to Run

```bash
streamlit run streamlit_inputs_only.py
```

Browser opens at `http://localhost:8501`

## What You'll See

### Section 1: Portfolio Value
- Number input for total portfolio value
- Default: $1,000,000

### Section 2: Holdings to Keep
- Text input for ticker
- Number input for dollar value
- "Add" button to add to list
- Shows all holdings with delete buttons
- Shows summary: locked value, remaining to allocate
- "Clear All" button to reset

### Section 3: Target FF3 Exposures
- Dropdown with presets OR custom values
- Three inputs: MKT, SMB, HML

### Section 4: Summary
- Shows everything you entered
- Debug expander to see exact data structures

### Optimize Button
- Currently just confirms inputs are collected
- Next step: This is where we'll call your optimization function

## Data Structures Created

When you click "Optimize", these variables are available:

```python
# Simple values
total_value = 1000000.0  # float

target_mkt = 1.0   # float
target_smb = 0.5   # float
target_hml = 0.5   # float

# DataFrame
constrained_holdings = pd.DataFrame([
    {'Ticker': 'AAPL', 'Value': 50000.0},
    {'Ticker': 'TSLA', 'Value': 50000.0}
])
# Columns: ['Ticker', 'Value']
# If no holdings specified, this is an empty DataFrame with same columns
```

## Session State

The app uses `st.session_state.holdings` to store the holdings list persistently.

This prevents the list from resetting every time you interact with the app.

## Next Steps

Once you're happy with the input collection, we'll add:

1. Import your optimization function
2. Call it with these inputs when button is clicked
3. Display the results

## Customization Tips

### Add more input fields
```python
# Example: Add a max position size constraint
max_position = st.slider("Max position size (%)", 1, 100, 40)
```

### Change default values
```python
# Example: Different default portfolio value
total_value = st.number_input("Total Value", value=500000.0)
```

### Add validation
```python
# Example: Check if total constrained value exceeds portfolio
if constrained_holdings['Value'].sum() > total_value:
    st.error("Holdings exceed portfolio value!")
```

### Different input method for holdings
Instead of manual add/remove, you could:

**Option A: CSV Upload**
```python
uploaded_file = st.file_uploader("Upload holdings CSV", type=['csv'])
if uploaded_file:
    constrained_holdings = pd.read_csv(uploaded_file)
```

**Option B: Text area (paste from Excel)**
```python
text_input = st.text_area("Paste holdings (Ticker,Value)")
# Parse the text into DataFrame
```

**Option C: Data editor (Streamlit's Excel-like widget)**
```python
constrained_holdings = st.data_editor(
    pd.DataFrame(columns=['Ticker', 'Value']),
    num_rows="dynamic"
)
```

## Test It

Try entering:
- Total: $1,000,000
- Holdings: AAPL $50,000, TSLA $50,000
- Target: MKT=1.0, SMB=0.5, HML=0.5

Click "Optimize" and check the debug section to see the exact data structures.
