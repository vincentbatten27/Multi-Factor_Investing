#!/usr/bin/env python
# coding: utf-8

# # run all neccessary functionalities

# In[91]:
# To ignore all warnings
import warnings
import getFamaFrenchFactors as gff
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
import numpy as np, numpy.random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime as dt
import calendar
from sklearn.linear_model import LinearRegression
import plotly.express as px
from IPython.display import Markdown as md
import random as rand
from matplotlib import gridspec
import yfinance as yf
from datetime import datetime
from pandas.tseries.offsets import DateOffset
from statsmodels.formula.api import ols
import statsmodels.api as sm
import random
import pulp
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import requests
from pulp import LpProblem, LpMaximize, LpVariable, LpMinimize, LpBinary, lpSum
from pulp import *
from dateutil.relativedelta import relativedelta
import time
import requests
from openpyxl import load_workbook
import os
from pathlib import Path
from io import StringIO
from alpha_vantage.timeseries import TimeSeries
SCRIPT_DIR = Path(__file__).parent




def extract_stock_data(df, tdickers, start, end):
    # df.index = pd.to_datetime(df.index)
    # df.index=df.index.to_period('M').to_timestamp('D')
    # Filter the DataFrame for the date rane
    df_filtered = df.loc[start:end]

    # Select the tickers from the DataFrame
    df_selected = df_filtered[tdickers]
    #df_selected=df_selected.loc[:, df_selected.isna().sum() <= 0].dropna()
    # df_selected.interpolate(method='linear',inplace=True)
    df_selected.index = pd.to_datetime(df_selected.index)
    df_selected = df_selected.tz_localize(None)
    columns = sorted([col for col in df_selected.columns if col != 'Date'])
    df_selected=df_selected[columns]
    for col in df_selected.columns:
        try:
            df_selected[col] = df_selected[col].astype(float)
        except ValueError:
            print()
            #print(f"Column '{col}' could not be converted to float.")
    df_selected.index=df_selected.index.to_period('M').to_timestamp('D')
    df_selected.replace('C', np.nan, inplace=True)
    for col in df_selected.columns:
            try:
                df_selected[col] = df_selected[col].astype(float)
            except ValueError:
                print()
               # print(f"Column '{col}' could not be converted to float.")
    df_selected.interpolate(method='linear',inplace=True)
    df_selected = df_selected.fillna(method='ffill')
    df_selected = df_selected.fillna(method='bfill')
    return df_selected


# In[92]:


def extract_spy_data(df, start, end):
    df.index = pd.to_datetime(df.index)
    df.index=df.index.to_period('M').to_timestamp('D')
    df_filtered = df.loc[start:end]
    return df_filtered


# In[93]:

def get_spy2(start, end, t1, rebal_freq, c_portf):
    ### Get tickers + setup
    global tickers, spy

    new_seed = np.random.randint(0, 1_000_000_000, dtype=int)
    np.random.seed(new_seed)
    random.seed(int(new_seed))

    new_monthly_data1 = new_monthly_data.copy()
    new_monthly_data1.index = pd.to_datetime(new_monthly_data1.index)
    if rebal_freq == "m" or rebal_freq == "drm":
        spy_year2 = pd.to_datetime(t1).year
        spy_year1 = min(
            (pd.to_datetime(t1) - relativedelta(months=1)).year, 2026
        )  # Universe selection year (currently max 2025)
    elif rebal_freq == "y" or rebal_freq == "dry":
        spy_year2 = pd.to_datetime(t1).year
        spy_year1 = min(
            (pd.datetime(t1) - relativedelta(years=1)).year, 2026
        )  # Universe selection year (currently max 2025)
    # ensure sp500 membership
    # print(f'{spy_year1}:{spy_year2}')
    universe_year = spy_yoy_tickers.loc[str(spy_year1) : str(spy_year2)]
    if len(universe_year) > 0:
        candidate_universe = set(universe_year.iloc[0].dropna())
    else:
        candidate_universe = set()

    candidate_universe = list(candidate_universe.intersection(new_monthly_data.columns))
    # ensure tickers are not NA in regression period (typically 3 years)
    end_reg = str(pd.to_datetime(t1) + relativedelta(months=1))
    ret_regression_window = new_monthly_data.loc[start:end_reg, candidate_universe]
    valid_tickers_ret = ret_regression_window.columns[
        ~ret_regression_window.isna().any(axis=0)
    ].tolist()
    prc_regression_window = price_monthly_data.loc[start:end_reg, candidate_universe]
    valid_tickers_prc = prc_regression_window.columns[
        ~prc_regression_window.isna().any(axis=0)
    ].tolist()
    valid_tickers = list(set(valid_tickers_ret) & set(valid_tickers_prc))    
    tickers =  noise_adjustmnet(valid_tickers,new_seed, c_portf)
    ### Import the monthly data
    global monthly_data
    global base_w
    monthly_data = extract_stock_data(new_monthly_data, tickers, start=start, end=end)

    # Assign equal weight as base weights
    base_w = {k: 1 / len(monthly_data.columns) for k in monthly_data.columns}
    base_w = pd.DataFrame.from_dict(base_w, orient="index", columns=["Weight"])

    spy = extract_spy_data(indexgspc, start, end)
    if monthly_data.index.equals(spy.index) == True:
        for i, j in monthly_data.iterrows():
            monthly_data.loc[i, "SP_500"] = spy.loc[i, "SP_500"]

    # Adjusting tickers list
    tickers = list(monthly_data.columns[:-1])

# In[94]:


def download_with_retry(tickers, start, end, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return extract_stock_data(new_monthly_data,tickers, start=start, end=end)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"Failed to download data after {retries} attempts.")


# In[95]:


def famafrenchreturns():
    global ff3_monthly
    # Fama French Monthly Returns Data using getFamaFrenchFactors module
    ff3_monthly = gff.famaFrench3Factor(frequency='m')
    ff3_monthly.rename(columns={"date_ff_factors": 'Date'}, inplace=True)
    ff3_monthly.set_index('Date', inplace=True)
    ff3_monthly.index = ff3_monthly.index.to_period('M').to_timestamp('D')
    # Keeping Only the Dates in the monthly_data
    ff3_monthly = ff3_monthly.reindex(new_monthly_data.index).dropna()
    # Keeping Only the Dates in the monthly_data
    est_df = estimate_ff3_from_holdings(new_monthly_data, ff3_monthly.index[-1], ff3_monthly)
    ff3_monthly = pd.concat([ff3_monthly,est_df])
    return ff3_monthly

def estimate_ff3_from_holdings(new_monthly_data, last_known_date, ff3_source):
    # Filter for dates after the last known date
    returns_subset = new_monthly_data[new_monthly_data.index > last_known_date].copy()
    
    if returns_subset.empty:
        return None
    
    results = []
    
    # Get the last available RF rate as a fallback
    last_rf = ff3_source['RF'].iloc[-1]
    
    for date, row in returns_subset.iterrows():
        r = row.dropna()
        if r.empty:
            continue
            
        # --- [NEW] Get the RF Rate ---
        # Try to find the exact date in your ff3_monthly data
        if date in ff3_source.index:
            rf = ff3_source.loc[date, 'RF']
        else:
            rf = last_rf # Use latest known rate if predicting for future dates
        
        n = len(r)
        tickers = r.index.tolist()
        hist = new_monthly_data[tickers].loc[:date].iloc[:-1]
        
        if hist.empty:
            continue

        cum_ret = hist.add(1).prod() - 1
        size_rank = cum_ret.rank(ascending=True) 

        if len(hist) >= 12:
            prior_12m = hist.iloc[-12:].add(1).prod() - 1
        else:
            prior_12m = cum_ret 
            
        value_rank = prior_12m.rank(ascending=True) 
        
        small = r[size_rank <= n/3].mean()
        big   = r[size_rank >= 2*n/3].mean()
        smb   = small - big
        
        high  = r[value_rank <= n/3].mean()
        low   = r[value_rank >= 2*n/3].mean()
        hml   = high - low

        # --- [ADJUSTED] Mkt-RF Calculation ---
        # Excess market return = Average stock return - Risk Free Rate
        mkt_rf = r.mean() - rf 
        
        results.append({
            'Date':   date,
            'Mkt-RF': mkt_rf,
            'SMB':    smb,
            'HML':    hml,
            'RF':     rf   # Adding the RF to the output for completeness
        })
    
    if not results:
        return None
        
    est = pd.DataFrame(results).set_index('Date')
    return est
# In[96]:


def to__cal_stock_betas():
    global stock_betas
    stock_betas = pd.DataFrame()
    # Iterate over the tickers list
    for col in monthly_data.columns:
        # Set the dependent variable (Return of stock i)
        y = monthly_data[col]
        # Set the independent variables (Fama French 3 Factors)
        X = ff3_monthly[['Mkt-RF','SMB','HML']]
        # Fit the multiple linear regression model
        model = LinearRegression()
        model.fit(X, y)
        # Store the results in the DataFrame
        stock_betas[col] = [model.intercept_] + list(model.coef_)
    stock_betas = stock_betas.T
    stock_betas.columns = ['Intercept','Mkt-RF','SMB','HML']


# In[97]:


def to_cal_stock_price(startt,endd):
    global stock_price
    global s_price
    global s_keys
    global s_values
    #Stock Prices on the Day of Optimization(Rebalancing)
    stock_price = extract_stock_data(price_monthly_data,tickers,start=startt,end=endd)
    stock_price = stock_price[-1:]
    stock_price.index = pd.to_datetime(stock_price.index).tz_localize(None)
    s_price = {}
    s_keys = list(tickers)
    s_values =  list(stock_price.iloc[0])
    for key,value in zip(s_keys,s_values):
        s_price[key] = value


# In[98]:


def Transaction_Costs(initialize=False):
    # if initialize:
    #     print("first draw:", np.random.random())

    global t_cost
    t_cost = {}
    global keys
    keys = list(tickers)
    values = list(random.uniform(.01, .02) for i in range(len(tickers)))
    for key, value in zip(keys, values):
        t_cost[key] = value


# In[99]:


# not working on back tests now?
def extract_weights(c_portf):   
    c_portf.index = c_portf['Ticker']
    if B % 100000 == 0:
        c_portf['Weight'] = c_portf['Value']/B    
        return c_portf[['Weight']].astype(float)
    asof = pd.to_datetime(end).to_period('M').to_timestamp()
    tickers1 = c_portf.index.tolist()
    c_portf_ret = new_monthly_data[tickers1].loc[asof].astype(float) + 1

    # Ensure alignment by setting the index explicitly

    c_portf_ret.index = c_portf.index

    # Update values with returns
    c_portf['Value'] = c_portf['Value'].astype(float) * c_portf_ret

    # Calculate weights
    raw_weights = c_portf['Value'] / B
    total_w = raw_weights.sum()

    if total_w > 1.0:
        c_portf['Weight'] = raw_weights / total_w
    else:
        c_portf['Weight'] = raw_weights
    constrained_weights = c_portf[['Weight']].astype(float)

    if constrained_weights['Weight'].sum() > 1 + 1e-9:  # Added tolerance
        raise ValueError(f"Invalid weight(s) > 1: sum = {constrained_weights['Weight'].sum()}")

    return constrained_weights


# In[100]:

def noise_adjustmnet(tickers, seed,c_portf):

    rng = np.random.default_rng(seed)
    n_keep = round(len(tickers) * (23/25))
    array_t = rng.choice(tickers, size= n_keep, replace=False)
    if c_portf is not None:
        must_hold = list(c_portf["Ticker"])
        tickers = list(set(list(array_t) + must_hold ))
    else:
        tickers = list(array_t)
    # print(f'Check : {len(tickers)}')
    
    return tickers


def optimization(c_portf):#new
    

    global index, wei, aux, err, binary
    if c_portf is not None : # if we arent sending None, then this runs
        constrained_weigths = extract_weights(c_portf)

    # --- Local, cached index sets ---
    T = list(monthly_data.index)
    I = list(tickers)

    # --- Precompute numeric arrays (NO pandas .loc inside loops) ---
    # Align everything explicitly on T and I
    rf  = ff3_monthly.loc[T, "RF"].to_numpy(dtype=float)
    mkt = ff3_monthly.loc[T, "Mkt-RF"].to_numpy(dtype=float)
    smb = ff3_monthly.loc[T, "SMB"].to_numpy(dtype=float)
    hml = ff3_monthly.loc[T, "HML"].to_numpy(dtype=float)

    # Excess returns matrix X[t,i] = monthly_data[t,i] - RF[t]
    X = monthly_data.loc[T, I].to_numpy(dtype=float) - rf[:, None]

    # RHS[t] = mkt_opt*Mkt-RF + smb_opt*SMB + hml_opt*HML
    RHS = (mkt_opt * mkt) + (smb_opt * smb) + (hml_opt * hml)

    # Base weights and transaction-cost coefficients
    # base_weights[i] must be indexable by ticker
    base = {i: float(base_weights[i]) for i in I}    # transaction cost coefficient per unit aux:
    # aux[i] * B * t_cost[i] / s_price[i]
    tc_coef = {i: float(B * t_cost[i] / s_price[i]) for i in I}

    # --- Build model ---
    index = LpProblem("Index", LpMinimize)

    wei    = LpVariable.dicts("Weight", I, lowBound=0)
    if c_portf is not None :   # if not setting none, we set lower weight bound to what the lower weight would be for the ticker owned 
        for i in I:            # Assumption: No personal buying or selling after portoflio starts, only prior
            if i in constrained_weigths.index:
               val = float(constrained_weigths.loc[i, 'Weight'])
               wei[i].lowBound = val
        
    aux    = LpVariable.dicts("Y",      I, lowBound=0)
    err    = LpVariable.dicts("Error",  T, lowBound=0)
    binary = LpVariable.dicts("bin",    I, cat=LpBinary)

    # Objective: minimize sum of absolute tracking errors
    index += lpSum(err[t] for t in T)

    # Weights sum to 1
    index += lpSum(wei[i] for i in I) == 1
    # Absolute deviation constraints + L1 bound
    for i in I:
        bw = base[i]
        index += aux[i] >= bw - wei[i]
        index += aux[i] >= wei[i] - bw
    index += lpSum(aux[i] for i in I) <= 1
    # Error term constraints: build portfolio return once per t
    for t_idx, t in enumerate(T):
        port = lpSum(wei[i] * X[t_idx, j] for j, i in enumerate(I))
        rhs  = float(RHS[t_idx])
        index += port - err[t] <= rhs
        index += port + err[t] >= rhs

    # Transaction cost constraint (no per-ticker tr_cost vars)
    max_tc = B * 0.002
    index += lpSum(aux[i] * tc_coef[i] for i in I) <= max_tc

    # Limit # of stocks in portfolio
    for i in I:
        index += wei[i] <= binary[i]
    index += lpSum(binary[i] for i in I) <= q
    # Solve (explicit CBC, quiet)
    index.solve(PULP_CBC_CMD(msg=False))


# In[101]:


def others():
    global sharess
    #Change in number of shares
    sharess = pd.DataFrame([v.varValue for v in index.variables() if str(v.name)[0] == 's'], index = [str(v.name) for v in index.variables() if str(v.name)[0] == 's'] , columns = ['Optimal'])
    sharess
    global tr_cost
    #Transaction Costs
    tr_cost = pd.DataFrame([v.varValue for v in index.variables() if str(v.name)[0] == 'T'], index = [str(v.name) for v in index.variables() if str(v.name)[0] == 'T'] , columns = ['Optimal'])
    tr_cost.sum()
    global weii
    #Optimal weights
    weii = pd.DataFrame([v.varValue for v in index.variables() if str(v.name)[0] == 'W'], index = [str(v.name) for v in index.variables() if str(v.name)[0] == 'W'] , columns = ['Optimal'])
    weii.sum()
    global auxx
    #Change of weights
    auxx = pd.DataFrame([v.varValue for v in index.variables() if str(v.name)[0] == 'Y'], index = [str(v.name) for v in index.variables() if str(v.name)[0] == 'Y'] , columns = ['Optimal'])
    auxx.sum()
    global errr
    #Error terms
    errr = pd.DataFrame([v.varValue for v in index.variables() if str(v.name)[0] == 'E'], index = [str(v.name) for v in index.variables() if str(v.name)[0] == 'E'] , columns = ['Optimal'])
    errr.sum()
    global binary_v
    # Check if Binary Values Constraint works
    binary_v = pd.DataFrame([v.varValue for v in index.variables() if v.varValue != 0 and str(v.name)[0] == 'b'], index = [str(v.name) for v in index.variables() if v.varValue != 0 and str(v.name)[0] == 'b'] , columns = ['Optimal'])
    binary_v.sum()
    global opt_weights 
    # Weights in Optimal Portfolio
    opt_weights = pd.DataFrame([v.varValue for v in index.variables() if v.varValue != 0 and str(v.name)[0] == 'W'], index = [str(v.name) for v in index.variables() if v.varValue != 0 and str(v.name)[0] == 'W'] , columns = ['Optimal'])
    opt_weights.style.format('{:,.2%}'.format)
    global weights_new
    weights_new = pd.DataFrame([v.varValue for v in index.variables() if str(v.name[0]) == 'W'], index = [str(v.name).split('_')[1] for v in index.variables() if str(v.name[0]) == 'W'] , columns = ['New Weights'])
    global weights
    weights = pd.DataFrame(np.zeros((len(monthly_data.columns[:-1]),3)), index=monthly_data.columns[:-1], columns=['PORTFOLIO Weights','Difference','New Weights'])
    for t in monthly_data.columns[:-1]:
        weights.loc[t][0] = base_w.loc[t]
        weights.loc[t][1] = weights_new.loc[t][0]-base_w.loc[t][0]
        weights.loc[t][2] = weights_new.loc[t]
    weights
    columns_to_remove = ['PORTFOLIO Weights', 'Difference']
    # Specify the column to filter non-zero values
    column_to_filter = 'New Weights'
    # Create a new DataFrame with selected columns and rows where New Weights is not equal to 0
    global opt_portf_weights
    opt_portf_weights = weights.drop(columns=columns_to_remove)[weights[column_to_filter] != 0]


# In[102]:


def portfolio_betas():
    # CHECK PORTFOLIO BETAS
   
    global port_betas
    port_returns = pd.DataFrame(np.zeros((len(monthly_data.index),2)), index=monthly_data.index, columns=["SP_500","Optimization"])
    for j in port_returns.index:
        port_returns.loc[j]["SP_500"] = monthly_data.loc[j]['SP_500']
        port_returns.loc[j]['Optimization'] = monthly_data.loc[j,:monthly_data.columns[-2]].dot(weights['New Weights'])
    port_returns = port_returns.merge(ff3_monthly[['Mkt-RF','SMB','HML']], left_index=True, right_index=True)
    # Create an empty DataFrame to store the Portfolio Beta
    port_betas = pd.DataFrame(np.zeros((3,4)), index=ff3_monthly.columns[0:3], columns=["SP_500", "Target", "Optimization", "Abs. Diff"])
    port_betas["Target"] = [mkt_opt, smb_opt, hml_opt]# Set the independent variables (Fama French 3 Factors)
    X = port_returns[['Mkt-RF','SMB','HML']]
    # Set the dependent variable (Return of Portfolio)
    Y = port_returns['SP_500']# Fit the multiple linear regression model
    regr = LinearRegression()
    regr.fit(X,Y)
    port_betas['SP_500'] = regr.coef_
    # Set the dependent variable (Return of Portfolio)
    Y = port_returns['Optimization']
    # Fit the multiple linear regression model
    regr = LinearRegression()
    regr.fit(X,Y)
    port_betas['Optimization'] = regr.coef_
    # Abs Difference between Target Betas & Optimal Portfolio Betas
    port_betas["Abs. Diff"] = round(abs(port_betas['Optimization'] - port_betas["Target"]),4)
    port_betas
    return port_betas


# In[104]:


def simulator(
    beta1, beta2, beta3, begin, final, budget, number, c_portf, t1, rebal_freq
):
    global start
    global end
    start = begin
    end = final
    global mkt_bet, smb_bet, hml_bet
    mkt_bet, smb_bet, hml_bet = [], [], []
    get_spy2(start, end, t1, rebal_freq,c_portf)
    # Adjusting tickers list as some tickers will not be included in the monthly_data if there is no data for test date range
    global tickers
    tickers = list(monthly_data.columns[:-1])
    tick_index = tickers + ["SP_500"]

    # TARGET FACTOR BETAS
    global base_weights
    global mkt_opt
    global smb_opt
    global hml_opt
    global B
    global q
    mkt_opt = beta1  # TARGET MKT BETA - EXPOSURE OF THE NEW PORTFOLIO TO MARKET FACTOR
    smb_opt = beta2  # TARGET SMB BETA - EXPOSURE OF THE NEW PORTFOLIO TO SIZE FACTOR
    hml_opt = beta3  # TARGET HML BETA - EXPOSURE OF THE NEW PORTFOLIO TO VALUE FACTOR
    B = budget  # BUDGET
    q = number  # NUMBER OF STOCKS IN THE NEW PORTFOLIO
    base_weights = (
        base_w.T * 0
    )  # ONLY HAVE THIS LINE OF CODE WHEN YOU ARE CONSTRUCTING THE PORTFOLIO FROM SCRATCH

    famafrenchreturns()
    to_cal_stock_price(start, final)
    Transaction_Costs()
    optimization(c_portf)
    others()
    global port_betas
    port_betas = portfolio_betas()
    mkt_bet.append(port_betas.iloc[0][2])
    smb_bet.append(port_betas.iloc[1][2])
    hml_bet.append(port_betas.iloc[2][2])


# In[105]:


def out_of_sampless(cccc, dddd):
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = cccc
    o1_end_d = dddd
    oos1_daily_data = extract_stock_data(
        new_monthly_data,
        opt_portf_weights.index.tolist(),
        start=o1_start_d,
        end=o1_end_d,
    )
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    oos1_spy_d = extract_spy_data(indexgspc, cccc, dddd)
    oos1_daily_data["SP_500"] = oos1_spy_d["SP_500"]
    oos1_daily_data["Optimized Portfolio"] = ""
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i, -1] = oos1_daily_data.iloc[i, :-2].dot(
            opt_portf_weights["New Weights"]
        )
    oos1_daily_data = oos1_daily_data.dropna()
    init = 1  # Initial Common Value (Can be thought of Initial Investment of $1 USD in each stock)
    oos1_new_returns = pd.DataFrame(
        np.ones((len(oos1_daily_data), len(oos1_daily_data.columns))),
        index=oos1_daily_data.index,
        columns=oos1_daily_data.columns,
    )
    for j in range(1, len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j - 1] * (
            oos1_daily_data.iloc[j - 1][oos1_daily_data.columns]
        )
    oos1_new_performance = pd.DataFrame(
        np.ones((len(oos1_daily_data), 2)),
        index=oos1_daily_data.index,
        columns=oos1_daily_data.columns[-2:],
    )
    for j in range(1, len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j - 1] * (
            oos1_daily_data.iloc[j - 1][oos1_daily_data.columns[-2:]] + 1
        )

    return oos1_new_performance


# In[106]:


def out_of_sample():
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = os_start
    o1_end_d   = os_end
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    oos1_spy_d=extract_spy_data(indexgspc,os_start,os_end)
    oos1_daily_data['SP_500'] = oos1_spy_d['SP_500']
    oos1_daily_data['Optimized Portfolio'] = ''
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i,-1] = oos1_daily_data.iloc[i,:-2].dot(opt_portf_weights['New Weights'])
    oos1_daily_data=oos1_daily_data.dropna()
    oos1_new_returns = pd.DataFrame(np.ones((len(oos1_daily_data),len(oos1_daily_data.columns))), index = oos1_daily_data.index, columns = oos1_daily_data.columns)
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns])
    oos1_new_performance = pd.DataFrame(np.ones((len(oos1_daily_data),2)), index = oos1_daily_data.index, columns = oos1_daily_data.columns[-2:])
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns[-2:]]+1)
    return oos1_new_performance


# In[107]:


def out_of_sample():
    global oos1_daily_data,oos1_new_returns
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = os_start
    o1_end_d   = os_end
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    oos1_spy_d=extract_spy_data(indexgspc,os_start,os_end)
    oos1_daily_data['SP_500'] = oos1_spy_d['SP_500']
    oos1_daily_data['Optimized Portfolio'] = ''
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i,-1] = oos1_daily_data.iloc[i,:-2].dot(opt_portf_weights['New Weights'])
    oos1_daily_data=oos1_daily_data.dropna()
    init = 1        #Initial Common Value (Can be thought of Initial Investment of $1 USD in each stock)
    oos1_new_returns = pd.DataFrame(np.ones((len(oos1_daily_data),len(oos1_daily_data.columns))), index = oos1_daily_data.index, columns = oos1_daily_data.columns)
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns])
    oos1_new_performance = pd.DataFrame(np.ones((len(oos1_daily_data),2)), index = oos1_daily_data.index, columns = oos1_daily_data.columns[-2:])
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns[-2:]]+1)
    
    return oos1_new_performance


# In[108]:


def new_mod_out_of_sample1(hsahs,hsahs2):
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_start_d
    global o1_end_d
    o1_start_d = hsahs
    # last_key = list(out_of_sample_year_end.keys())[-1]
    o1_end_d   = hsahs2
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    # oos1_spy_d = pd.DataFrame(yf.download('^GSPC',start=o1_start_d,end=o1_end_d,interval='1mo')['Adj Close'].pct_change())
    oos1_spy_d=extract_spy_data(indexgspc,o1_start_d,o1_end_d)
    oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
    oos1_daily_data['SP_500'] = oos1_spy_d['SP_500']
    oos1_daily_data['Optimized Portfolio'] = ''
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i,-1] = oos1_daily_data.iloc[i,:-2].dot(opt_portf_weights['New Weights'])
    oos1_daily_data
    oos1_daily_data=oos1_daily_data.dropna()
    oos1_new_returns = pd.DataFrame(np.ones((len(oos1_daily_data),len(oos1_daily_data.columns))), index = oos1_daily_data.index, columns = oos1_daily_data.columns)
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns])
    oos1_new_performance = pd.DataFrame(np.ones((len(oos1_daily_data),2)), index = oos1_daily_data.index, columns = oos1_daily_data.columns[-2:])
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns[-2:]]+1)
    
    return oos1_new_performance


# In[109]:


def mod_out_of_sample1():
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_start_d
    global o1_end_d
    o1_start_d = out_of_sample_year_start[1]
    last_key = list(out_of_sample_year_end.keys())[-1]
    o1_end_d   = out_of_sample_year_end[last_key]
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    oos1_spy_d=extract_spy_data(indexgspc,o1_start_d,o1_end_d)
    oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
    oos1_daily_data['SP_500'] = oos1_spy_d['SP_500']
    oos1_daily_data['Optimized Portfolio'] = ''
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i,-1] = oos1_daily_data.iloc[i,:-2].dot(opt_portf_weights['New Weights'])
    oos1_daily_data
    oos1_daily_data=oos1_daily_data.dropna()
    oos1_new_returns = pd.DataFrame(np.ones((len(oos1_daily_data),len(oos1_daily_data.columns))), index = oos1_daily_data.index, columns = oos1_daily_data.columns)
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns])
    oos1_new_performance = pd.DataFrame(np.ones((len(oos1_daily_data),2)), index = oos1_daily_data.index, columns = oos1_daily_data.columns[-2:])
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns[-2:]]+1)
    
    return oos1_new_performance


# In[110]:


def mod_out_of_sample():
    global oos1_daily_data
    global oos1_new_performance
    o1_start_d = os_start
    o1_end_d   = os_end
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    # oos1_spy_d = pd.DataFrame(yf.download('^GSPC',start=o1_start_d,end=o1_end_d,interval='1mo')['Adj Close'].pct_change())
    oos1_spy_d=extract_spy_data(indexgspc,o1_start_d,o1_end_d)
    oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
    oos1_daily_data['SP_500'] = oos1_spy_d['SP_500']
    oos1_daily_data['Optimized Portfolio'] = ''
    for i in range(len(oos1_daily_data.index)):
        oos1_daily_data.iloc[i,-1] = oos1_daily_data.iloc[i,:-2].dot(opt_portf_weights['New Weights'])
    oos1_daily_data
    oos1_daily_data=oos1_daily_data.dropna()
    oos1_new_returns = pd.DataFrame(np.ones((len(oos1_daily_data),len(oos1_daily_data.columns))), index = oos1_daily_data.index, columns = oos1_daily_data.columns)
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_returns.iloc[j] = oos1_new_returns.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns])
    oos1_new_performance = pd.DataFrame(np.ones((len(oos1_daily_data),2)), index = oos1_daily_data.index, columns = oos1_daily_data.columns[-2:])
    for j in range(1,len(oos1_daily_data.index)):
        oos1_new_performance.iloc[j] = oos1_new_performance.iloc[j-1]*(oos1_daily_data.iloc[j-1][oos1_daily_data.columns[-2:]]+1)
    
    return oos1_new_performance


# In[111]:


def current_date():
    global today
    global os_start
    global os_end
    global n_year_before
    global n_year_after
    from datetime import datetime, timedelta
    today = datetime.today()
    period_end = pd.to_datetime('2025-01-01')
    one_year_before = period_end - timedelta(days=365)
    os_start = period_end - timedelta(days=365)
    two_months_before = os_start - timedelta(days=2*30)
    os_start = two_months_before.replace(day=1)
    one_month_before = period_end - timedelta(days=30)
    os_end = one_month_before.replace(day=1)
    
    n_year_before = os_start - timedelta(days=(365*n_years))
    n_year_after=n_year_before+timedelta(days=(365*n_years))                           
    os_start=os_start.strftime("%Y-%m-%d")
    os_end=os_end.strftime("%Y-%m-%d")
    n_year_before=n_year_before.strftime("%Y-%m-%d")
    n_year_after=n_year_after.strftime("%Y-%m-%d")
    from datetime import date

    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    today = formatted_date


# In[112]:


def new_date_calculation1():
    from datetime import datetime, timedelta
    from datetime import date
    today = datetime.now()
    global out_of_sample_year_start
    global out_of_sample_year_end
    out_of_sample_year_start={}
    out_of_sample_year_end={}
    period_end = pd.to_datetime('2025-01-01')

    for year in range(os_years):
        out_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * (os_years - year)))
        two_months_before = (out_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month- 1))
        out_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=out_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        out_of_sample_year_end[(year+1)]=out_of_sample_year_start[(year+1)]+ timedelta(days=no_days_in_year-1)
        out_of_sample_year_start[(year+1)]=out_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        out_of_sample_year_end[(year+1)]=out_of_sample_year_end[(year+1)].strftime("%Y-%m-%d")                        
    
    global in_of_sample_year_start
    in_of_sample_year_start={}
    global in_of_sample_year_end
    in_of_sample_year_end={}
    for year in range(in_years):
        in_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * ((in_years+os_years) - year)))
        two_months_before = in_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month-1)
        in_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=in_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        in_of_sample_year_end[(year+1)]=in_of_sample_year_start[(year+1)]+ timedelta(days=no_days_in_year-1)
        in_of_sample_year_start[(year+1)]=in_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        in_of_sample_year_end[(year+1)]=in_of_sample_year_end[(year+1)].strftime("%Y-%m-%d")
    
    inner_in_of_sample_year_start={}
    for year in range(in_years+os_years):
        inner_in_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * (in_years+os_years - year)))
        two_months_before = inner_in_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month-1)
        inner_in_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=inner_in_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        inner_in_of_sample_year_start[(year+1)]=inner_in_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        

    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    today = formatted_date
    print(out_of_sample_year_start)
    print(out_of_sample_year_end)
    print(in_of_sample_year_start)
    print(in_of_sample_year_end)

    return inner_in_of_sample_year_start

def new_date_calculation():
    from datetime import datetime, timedelta
    from datetime import date
    today = datetime.now()
    global out_of_sample_year_start
    global out_of_sample_year_end
    out_of_sample_year_start={}
    out_of_sample_year_end={}
    period_end = pd.to_datetime('2025-01-01')

    for year in range(os_years):
        out_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * (os_years - year)))
        two_months_before = (out_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month- 1))
        out_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=out_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        out_of_sample_year_end[(year+1)]=out_of_sample_year_start[(year+1)]+ timedelta(days=no_days_in_year-1)
        out_of_sample_year_start[(year+1)]=out_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        out_of_sample_year_end[(year+1)]=out_of_sample_year_end[(year+1)].strftime("%Y-%m-%d")                        
    
    global in_of_sample_year_start
    in_of_sample_year_start={}
    global in_of_sample_year_end
    in_of_sample_year_end={}
    for year in range(in_years):
        in_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * ((in_years+os_years) - year)))
        two_months_before = in_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month-1)
        in_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=in_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        in_of_sample_year_end[(year+1)]=in_of_sample_year_start[(year+1)]+ timedelta(days=no_days_in_year-1)
        in_of_sample_year_start[(year+1)]=in_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        in_of_sample_year_end[(year+1)]=in_of_sample_year_end[(year+1)].strftime("%Y-%m-%d")
    
    inner_in_of_sample_year_start={}
    for year in range(in_years+os_years):
        inner_in_of_sample_year_start[(year+1)] = period_end - timedelta(days=(365 * (in_years+os_years - year)))
        two_months_before = inner_in_of_sample_year_start[(year+1)] - relativedelta(months = period_end.month-1)
        inner_in_of_sample_year_start[(year+1)] = two_months_before.replace(day=1)
        years=inner_in_of_sample_year_start[(year+1)].year
        if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):
            is_leap_year = True
            no_days_in_year = 366
        else:
            is_leap_year = False
            no_days_in_year = 365
        inner_in_of_sample_year_start[(year+1)]=inner_in_of_sample_year_start[(year+1)].strftime("%Y-%m-%d")
        

    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    today = formatted_date
    print(out_of_sample_year_start)
    print(out_of_sample_year_end)
    print(in_of_sample_year_start)
    print(in_of_sample_year_end)

    return inner_in_of_sample_year_start 


# In[294]:


def new_run_with_backtest_rebalance(inyears,outyears,betaA,betaB,betaC, rebal_freq):
    global start_date
    global end_date
    global os_years,tostorelist,nchecklist
    global in_years
    os_years=outyears
    in_years=inyears
    global performances
    performances={}
    global spy_performances
    spy_performances={}
    global new_performances
    new_performances={}
    global new_spy_performances
    new_spy_performances={}
    global inner_n_year_before_cal
    inner_n_year_before_cal=new_date_calculation()
    global n_year_before
    global n_year_after
    n_year_before=in_of_sample_year_start[1]
    n_year_after=in_of_sample_year_end[in_years]
    global newbudget
    newbudget = 1000000
    simulator(betaA,betaB,betaC,n_year_before,n_year_after,newbudget,500,None)
    global checklist
    global mchecklist
    checklist=[]
    mchecklist=[]
    tostorelist=[]
    global rebalance_opt_weights
    global port_betas_list 
    port_betas_list = []
    rebalance_opt_weights = []
    os_count = 1   
    for k in range(os_years): 
        global os_start
        global os_end
        global oos1_new_performance
        oos1_new_performance={}
        global init
        os_start=out_of_sample_year_start[1+k]
        os_end=out_of_sample_year_end[1+k]

        noos1_new_performance=pd.DataFrame()
        global checklist_1
        new_date_calculation()
        
        checking=out_of_sample()
        tostorelist.append(checking)
        inner_n_year_before=inner_n_year_before_cal[k+1]
        inner_n_year_after=out_of_sample_year_end[k+1]
        checklist.append(oos1_new_performance)
        
        if(rebal_freq == 'y'):
            if(k != 0):
                newbudget=1000000*oos1_new_performance['Optimized Portfolio'][-1]  
            simulator(betaA,betaB,betaC,inner_n_year_before,inner_n_year_after,newbudget,500,None)
            rebalance_opt_weights.append(opt_portf_weights)
            if(os_count == os_years):
                checklist=extract_performance(checklist)
                noos1_new_performance=pd.concat(checklist, ignore_index=False)
        if rebal_freq == 'dry':
            newbudget=1000000*oos1_new_performance['Optimized Portfolio'][-1]
            curr_year = pd.to_datetime(inner_n_year_after).year
            try:
                curr_df = pd.read_csv(fSCRIPT_DIR /'Reward_CSVs_Surrogate/yrebal_explored_sortino_surrogate_{curr_year}.csv')
            except:
                print('File DNE')
            curr_df = curr_df.sort_values(by='reward')
            betaA = curr_df.iloc[-1][0]
            betaB = curr_df.iloc[-1][1]
            betaC = curr_df.iloc[-1][2]
            print(f'{betaA}, {betaB}, {betaC} ')
            simulator(betaA,betaB,betaC,inner_n_year_before,inner_n_year_after,newbudget,500,None)
            rebalance_opt_weights.append(opt_portf_weights)
            if(os_count == os_years):
                checklist=extract_performance(checklist)
                noos1_new_performance=pd.concat(checklist, ignore_index=False)
        if k == 0:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1]
            start_date = os_start
        else:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1] * performances[k]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1] * spy_performances[k]
            end_date = os_end 
        os_count +=1
    for kk in range(os_years): 
        placeholder=noos1_new_performance.index[0]
        placeholder=placeholder.replace(year=placeholder.year+(kk+1))
        if placeholder in noos1_new_performance.index:
            new_spy_performances[kk + 1] = noos1_new_performance.loc[placeholder,"SP_500"]
            new_performances[kk + 1] = noos1_new_performance.loc[placeholder,"Optimized Portfolio"]
    
    new_spy_performances[os_years] = noos1_new_performance.iloc[-1].loc["SP_500"]
    new_performances[os_years] = noos1_new_performance.iloc[-1].loc["Optimized Portfolio"]
    return noos1_new_performance 


# In[237]:


def new_run_with_backtest_mrebalance(inyears,outyears,betaA,betaB,betaC,stating_budget, rebal_freq,c_portf):
    global start_date
    global start_date1
    global end_date
    global os_years
    global in_years
    global os_months
    global mkt_bet, smb_bet, hml_bet
    mkt_bet,smb_bet,hml_bet = [],[],[]
    os_years=outyears
    os_months = os_years*12
    in_years=inyears
    global performances
    performances={}
    global spy_performances
    spy_performances={}
    global new_performances
    new_performances={}
    global new_spy_performances
    new_spy_performances={}
    inner_n_year_before_cal =new_date_calculation()
    global n_year_before
    global n_year_after
    n_year_before= in_of_sample_year_start[1]
    n_year_after= in_of_sample_year_end[in_years]
    global rebalance_opt_weights
    global port_betas_list 
    port_betas_list = []
    rebalance_opt_weights = []
    prev_month_perf = 1
    noos1_new_performance=pd.DataFrame()
    global expected_betas
    expected_betas = []

    for k in range(os_months-1):   
        # so base is above, and then first step is to grab the performance of January 2020 (assuming standard run)
        # to add to noos1_perf and to update budget'
        if(rebal_freq == 'm'):
            n_year_before_updated = str(pd.to_datetime(n_year_before) + relativedelta(months=k))
            n_year_after_updated = str(pd.to_datetime(n_year_after) + relativedelta(months=k))
            start_date11 = str(pd.to_datetime(n_year_before_updated) + relativedelta(months=36))
            end_date1 = str(pd.to_datetime(n_year_before_updated) + relativedelta(months=37))
            expected_betas.append([betaA,betaB,betaC])
            simulator(betaA,betaB,betaC,n_year_before_updated,n_year_after_updated,stating_budget*prev_month_perf,50,c_portf)
            rebalance_opt_weights.append(opt_portf_weights)
            mperformance = out_of_sampless(start_date11,end_date1).copy()
            snipped_perf = mperformance.iloc[1]
            if(k==0):
                first_perf = mperformance.iloc[0]
                noos1_new_performance = pd.concat([noos1_new_performance , first_perf.to_frame().T])
            prev_month_perf = snipped_perf['Optimized Portfolio'] * prev_month_perf
            noos1_new_performance = pd.concat([noos1_new_performance , snipped_perf.to_frame().T])
        
        
        
        
        
        
        
        if(rebal_freq == 'drm'):
            n_year_before_updated = str(pd.to_datetime(n_year_before) + relativedelta(months=k))
            n_year_after_updated = str(pd.to_datetime(n_year_after) + relativedelta(months=k))
            start_date1 = str(pd.to_datetime(n_year_before_updated) + relativedelta(months=36))
            end_date1 = str(pd.to_datetime(n_year_before_updated) + relativedelta(months=37))
            curr_year = (pd.to_datetime(n_year_after_updated)+relativedelta(months=1)).year 
            print(start_date1)
            try:
                # curr_df = pd.read_csv(f'Active_Strategy_CSVs/yrebal_explored_sortino_active_{curr_year}.csv')
                curr_df = pd.read_csv(fSCRIPT_DIR /'Reward_CSVs_Surrogate/yrebal_explored_sortino_surrogate_{curr_year}.csv')    
                # curr_df = pd.read_csv(f'yrebal_explored_sortino_resample_surrogate_{curr_year}.csv')
                # curr_df = pd.read_csv(f'yrebal_explored_sortino_resample_surrogate_{pd.to_datetime(start_date1).date()}.csv')
            except FileNotFoundError:
                curr_df = pd.read_csv(fSCRIPT_DIR /'yrebal_explored_sortino_resample_surrogate_2018-07-01.csv')  
                print('File DNE')
            curr_df = curr_df.sort_values(by='reward') 
            betaA = curr_df.iloc[-1][0]
            betaB = curr_df.iloc[-1][1]
            betaC = curr_df.iloc[-1][2]

            print(f'{betaA}, {betaB}, {betaC} ')
            expected_betas.append([betaA,betaB,betaC])
            simulator(betaA,betaB,betaC,n_year_before_updated,n_year_after_updated,1000000*prev_month_perf,50,c_portf)
            rebalance_opt_weights.append(opt_portf_weights)

            mperformance = out_of_sampless(start_date1,end_date1).copy()
            snipped_perf = mperformance.iloc[1]
            if(k==0):
                first_perf = mperformance.iloc[0]
                noos1_new_performance = pd.concat([noos1_new_performance , first_perf.to_frame().T])
            prev_month_perf = snipped_perf['Optimized Portfolio'] * prev_month_perf
            noos1_new_performance = pd.concat([noos1_new_performance , snipped_perf.to_frame().T])
    noos1_new_performance = extract_performance_monthly(noos1_new_performance)
    start_date= noos1_new_performance.index[0]
    end_date = noos1_new_performance.index[-1]

    return noos1_new_performance 


def new_run_with_backtest_mrebalance_front_end(
    target_date,
    inyears,
    outyears,
    betaA,
    betaB,
    betaC,
    starting_budget,
    rebal_freq,
    c_portf,
    obj_key,
):
    # front end target date is end of last month (i.e., march 2026 is rn, feb-28-2026 is target date)
    global start_date
    global start_date1
    global end_date
    global os_years
    global in_years
    global os_months
    global mkt_bet, smb_bet, hml_bet

    mkt_bet, smb_bet, hml_bet = [], [], []
    os_years = outyears
    os_months = os_years * 12
    in_years = inyears
    global performances
    performances = {}
    global spy_performances
    spy_performances = {}
    global new_performances
    new_performances = {}
    global new_spy_performances
    new_spy_performances = {}
    global n_year_before
    global n_year_after
    n_year_after = target_date - relativedelta(years=outyears)
    anchor_date = (target_date + pd.Timedelta(days=1)) - pd.DateOffset(years=outyears)

    n_year_before = {
        1: (anchor_date - pd.DateOffset(years=3)).strftime("%Y-%m-%d"),
        2: (anchor_date - pd.DateOffset(years=2)).strftime("%Y-%m-%d"),
        3: (anchor_date - pd.DateOffset(years=1)).strftime("%Y-%m-%d"),
    }
    n_year_before = n_year_before[1]
    global rebalance_opt_weights
    global port_betas_list
    port_betas_list = []
    rebalance_opt_weights = []
    prev_month_perf = 1
    noos1_new_performance = pd.DataFrame()
    global expected_betas
    expected_betas = []
    budget = starting_budget
    for k in range(os_months -1 ):#DELETE AFTER

        # so base is above, and then first step is to grab the performance of January 2020 (assuming standard run)
        # to add to noos1_perf and to update budget'
        if rebal_freq == "m":

            n_year_before_updated = str(
                pd.to_datetime(n_year_before) + relativedelta(months=k)
            )
            n_year_after_updated = str(
                pd.to_datetime(n_year_after) + relativedelta(months=k)
            )
            start_date11 = str(
                pd.to_datetime(n_year_before_updated) + relativedelta(months=36)
            )
            end_date1 = str(
                pd.to_datetime(n_year_before_updated) + relativedelta(months=37)
            )

            expected_betas.append([betaA, betaB, betaC])
            budget = budget * prev_month_perf
            t1 = start_date11
            for attempt in range(3):
                try:
                    simulator(
                        betaA,
                        betaB,
                        betaC,
                        n_year_before_updated,
                        n_year_after_updated,
                        budget,
                        50,
                        c_portf,
                        t1,
                        rebal_freq,
                    )
                    rebalance_opt_weights.append(opt_portf_weights)
                    mperformance = out_of_sampless(start_date11, end_date1).copy()
                    snipped_perf = mperformance.iloc[1]
                    break
                except IndexError:
                    if attempt == 2:
                        raise

            if k == 0:
                first_perf = mperformance.iloc[0]
                noos1_new_performance = pd.concat(
                    [noos1_new_performance, first_perf.to_frame().T]
                )
            prev_month_perf = snipped_perf["Optimized Portfolio"]
            noos1_new_performance = pd.concat(
                [noos1_new_performance, snipped_perf.to_frame().T]
            )

        if rebal_freq == "drm":
            n_year_before_updated = str(
                pd.to_datetime(n_year_before) + relativedelta(months=k+1) # delete the + 1 if iteration is not 3
            )
            n_year_after_updated = str(
                pd.to_datetime(n_year_after) + relativedelta(months=k+1) # delete the + 1 if iteration is not 3
            )
            start_date11 = str(
                pd.to_datetime(n_year_before_updated) + relativedelta(months=36)
            )
            end_date1 = str(
                pd.to_datetime(n_year_before_updated) + relativedelta(months=37)
            )

            try:
                path = f"Front_End_Strategies_Iteration_4_excess{obj_key}/rebal_explored_{obj_key}_{(pd.to_datetime(n_year_after_updated)+ pd.offsets.MonthEnd(0)).date()}.csv"
                curr_df = pd.read_csv(SCRIPT_DIR / path)
            except FileNotFoundError:

                print("File DNE")
            best = curr_df.nlargest(1, 'reward').iloc[0]
            betaA,betaB,betaC = [best['c1'], best['c2'], best['c3']]

            expected_betas.append([betaA, betaB, betaC])
            budget = budget * prev_month_perf
            t1 = start_date11
            for attempt in range(3):
                try:
                    simulator(
                        betaA,
                        betaB,
                        betaC,
                        n_year_before_updated,
                        n_year_after_updated,
                        budget,
                        50,
                        None,
                        t1,
                        rebal_freq,
                    )
                    rebalance_opt_weights.append(opt_portf_weights)
                    mperformance = out_of_sampless(start_date11, end_date1).copy()
                    snipped_perf = mperformance.iloc[1]
                    break
                except IndexError:
                    if attempt == 2:
                        raise
   
            if k == 0:
                first_perf = mperformance.iloc[0]
                noos1_new_performance = pd.concat(
                    [noos1_new_performance, first_perf.to_frame().T]
                )
            prev_month_perf = snipped_perf["Optimized Portfolio"]
            noos1_new_performance = pd.concat(
                [noos1_new_performance, snipped_perf.to_frame().T]
            )
    noos1_new_performance = extract_performance_monthly(noos1_new_performance)
    start_date = noos1_new_performance.index[0]
    end_date = noos1_new_performance.index[-1]

    return noos1_new_performance, expected_betas, None


# In[118]:


def extract_performance_monthly(dflist):
    global monthly_returns
    dflist.index.name = 'Date'
    monthly_returns = dflist.astype(float)
    roi = monthly_returns.cumprod()
    roi.index.name='Date'
    return roi


# In[119]:


def extract_performance(dflist):
    size=len(dflist)
    for i in range(size):
        eoy_performance=dflist[i]['Optimized Portfolio'][-1]
        eoy_spy=dflist[i]['SP_500'][-1]
        if i<(size-1):
            dflist[i+1]['Optimized Portfolio']=dflist[i+1]['Optimized Portfolio']*eoy_performance
            dflist[i+1]['SP_500']=dflist[i+1]['SP_500']*eoy_spy
    dflist[1]=dflist[1].iloc[1:]
    return dflist


# In[120]:


def new_run_with_backtest(inyears,outyears,betaA,betaB,betaC):
    
    global os_years
    global in_years
    os_years=outyears
    in_years=inyears
    global performances
    performances={}
    global spy_performances
    spy_performances={}
    global new_performances
    new_performances={}
    global new_spy_performances
    new_spy_performances={}
    new_date_calculation()
    global n_year_before
    global n_year_after
    n_year_before= in_of_sample_year_start[1]
    n_year_after= in_of_sample_year_end[in_years]
    
    simulator(betaA,betaB,betaC,n_year_before,n_year_after,1000000,50,None)
    global checklist
    checklist=[]
    for k in range(os_years): 
        global os_start
        global os_end
        global oos1_new_performances
        oos1_new_performances={}
        global init
        os_start=out_of_sample_year_start[1+k]
        os_end=out_of_sample_year_end[1+k]
        out_of_sample()
        
        checklist.append(oos1_new_performance)
        if k == 0:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1]
        else:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1] * performances[k]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1] * spy_performances[k]
    mod_out_of_sample1()
    for kk in range(os_years): 
        placeholder=oos1_new_performance.index[0]
        placeholder=placeholder.replace(year=placeholder.year+(kk+1))
        if placeholder in oos1_new_performance.index:
            new_spy_performances[kk + 1] = oos1_new_performance.loc[placeholder,"SP_500"]
            new_performances[kk + 1] = oos1_new_performance.loc[placeholder,"Optimized Portfolio"]
    
    new_spy_performances[os_years] = oos1_new_performance.iloc[-1].loc["SP_500"]
    new_performances[os_years] = oos1_new_performance.iloc[-1].loc["Optimized Portfolio"]
    return oos1_new_performance


# In[121]:


def list_sharpe_ratio(dflist):
    i=0
    sharpe_list=[]
    for df in dflist:
        if i==0:
            checkff3_monthly = gff.famaFrench3Factor(frequency='m')
            checkff3_monthly
            checkff3_monthly.rename(columns={"date_ff_factors": 'Date'}, inplace=True)
            checkff3_monthly.set_index('Date', inplace=True)
            checkff3_monthly.index = checkff3_monthly.index.to_period('M').to_timestamp('D')
            checkff3_monthly=checkff3_monthly[checkff3_monthly.index >= df.index[0]]
            checkff3_monthly=checkff3_monthly[checkff3_monthly.index <= df.index[-1]]
            checkff3_monthly.drop(columns={'Mkt-RF','SMB','HML'},inplace=True)
            some_df2=df.copy()
            some_df2.drop(columns={'Optimized Portfolio'},inplace=True)
            sp500_sharpe_ratio=calculate_sharpe_ratio(some_df2,checkff3_monthly,'SP_500')
        i+=1
        some_df=df.copy()
        some_df.drop(columns={'SP_500'},inplace=True)
        df_sharpe_ratio=calculate_sharpe_ratio(some_df,checkff3_monthly,'Optimized Portfolio')
        sharpe_list.append(df_sharpe_ratio.copy())
    sharpe_list = pd.DataFrame(sharpe_list)
    sharpe_average=sharpe_list.mean()
    return sharpe_average,sharpe_list,sp500_sharpe_ratio


# In[122]:


def calculate_sharpe_ratio(portfolio_cumulative_df, risk_free_rate_df, column_name):
    portfolio_monthly_returns = portfolio_cumulative_df[column_name].pct_change().dropna()
    aligned_risk_free_rate = risk_free_rate_df.loc[portfolio_monthly_returns.index, 'RF']
    excess_returns = portfolio_monthly_returns - aligned_risk_free_rate
    avg_excess_return = excess_returns.mean()
    std_dev_return = portfolio_monthly_returns.std()
    sharpe_ratio = avg_excess_return / std_dev_return *3.3974184469680715

    return sharpe_ratio


# In[123]:


def final_visual():
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, df in enumerate(oos1_list):
        ax.plot(df['Optimized Portfolio'])
    ax.plot(oos1_list[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    last_df_index = oos1_list[-1].index
    concatenated_df = pd.concat(oos1_list, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    if (len(averaged_df.index)%12 != 0):
        full_idx = pd.date_range(
            start=averaged_df.index.min(),
            end=averaged_df.index.max(),
            freq='MS'   
        )

        missing_idx = full_idx.difference(averaged_df.index)
        # print("Missing dates:", missing_idx)

        averaged_df = (
            averaged_df
            .reindex(full_idx)          # add missing rows
            .interpolate(method='time') # fill values based on time
        )
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for every 1 dollar invested')
    ax.legend()
    #plt.show()
    return averaged_df


# In[124]:


def sp_final_visual():
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, df in enumerate(oos1_list):
        ax.plot(df['Optimized Portfolio'])
    # ax.plot(oos1_list[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    last_df_index = oos1_list[-1].index
    concatenated_df = pd.concat(oos1_list, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    # ax.set_xlabel('Months')
    # ax.set_ylabel('ROI')
    # ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for every 1 dollar invested')
    # ax.legend()
    # plt.show()
    return averaged_df


# In[125]:


def final_visuala(ddfs):
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
    fig.add_trace(
        go.Scatter(
            x=averaged_df.index,
            y=averaged_df["Optimized Portfolio"],
            mode="lines+markers",
            name="Optimized Portfolio",
            line=dict(color="royalblue", width=2.5),
            marker=dict(color="royalblue", size=5, symbol="circle"),
            hovertemplate="%{x|%b %Y}<br>Portfolio: $%{y:.3f}<extra></extra>",
        )
    )

    # Month indicators
    for date in averaged_df.index:
        fig.add_vline(
            x=date, line=dict(color="rgba(150, 150, 150, 0.2)", width=1, dash="dot")
        )

    fig.update_layout(
        title=dict(
            text="Optimized Portfolio vs S&P 500<br><sup>Growth of $1 invested</sup>",
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

    fig.plot()

    # =========================================================================
    # Performance Metrics
    # =========================================================================
    def compute_metrics(series, label):
        start = str(series.index[0])
        end   = str(series.index[-1])

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
    print(metrics)

    return averaged_df


# In[126]:


def final_visualb(hhh,fff):
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(hhh[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    
    for i, df in enumerate(hhh):
        ax.plot(df['Optimized Portfolio'],label=fff[i])
    ax.plot(hhh[-1]['Optimized Portfolio'], label='Reinforcement Portfolio', linestyle='-',  marker='o',color='black')
    last_df_index = hhh[-1].index
    concatenated_df = pd.concat(hhh, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 for every 1 dollar invested')
    ax.legend()
    plt.show()
    return averaged_df


# In[127]:


def final_visual1():
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, df in enumerate(oos1_list):
        ax.plot(df['Optimized Portfolio'], label=f'optimized_{i + 1}')
    ax.plot(oos1_list[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    last_df_index = oos1_list[-1].index
    concatenated_df = pd.concat(oos1_list, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 for every 1 dollar invested')
    ax.legend()
    plt.show()


# In[128]:


def final_visual2():
    fig, ax = plt.subplots(figsize=(12, 6))
#     for i, df in enumerate(oos1_list):
#         ax.plot(df['Optimized Portfolio'], label=f'optimized_{i + 1}')
    ax.plot(oos1_list[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    last_df_index = oos1_list[-1].index
    concatenated_df = pd.concat(oos1_list, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for every 1 dollar invested')
    ax.legend()
    plt.show()


# In[129]:


def monte_carlo_simulation(n_simulations,mbetaA,mbetaB,mbetaC):
    results = []
    yearly_returns = []
    
    for i in range(n_simulations):
        # Run simulation
        # Transaction_Costs()
        new_run_with_backtest(3,5,mbetaA,mbetaB,mbetaC)
        
        # Append results
        results.append(oos1_new_performance.copy())
        yearly_returns.append(new_performances.copy())
        
    # Convert yearly returns to DataFrame for easier averaging
    df_yearly_returns = pd.DataFrame(yearly_returns)
    
    # Calculate averages for each key
    averages = df_yearly_returns.mean().to_dict()
    
    return results, yearly_returns, averages


# In[134]:

def front_end_plug(target_mkt, target_smb, target_hml,start,end,total_value,num,constrained_holdings,
price_monthly_data1,new_monthly_data1,indexgspc1,spy_yoy_tickers1):
    global price_monthly_data 
    global new_monthly_data 
    global indexgspc 
    global spy_yoy_tickers 
    global oos1_list, oos1_list_yearly, oos1_average
    price_monthly_data = price_monthly_data1
    new_monthly_data = new_monthly_data1
 
    indexgspc = indexgspc1.copy()
    spy_yoy_tickers = spy_yoy_tickers1.copy()
    # price_monthly_data, new_monthly_data = update_stock_data(price_monthly_data, new_monthly_data,spy_yoy_tickers1)
    
    indexgspc = indexgspc1.copy()
    spy_yoy_tickers = spy_yoy_tickers1.copy()
    simulator(target_mkt, target_smb, target_hml,start,end,total_value, num,constrained_holdings,end,'m')
    return opt_portf_weights

def monte_carlo_simulation(n_simulations,mbetaA,mbetaB,mbetaC,type, in_years1, out_years, starting_budget, rebal_freq,c_portf,price_monthly_data1,
                    new_monthly_data1,
                    indexgspc1,
                    spy_yoy_tickers1,
                    obj_key
                    ): 
    global price_monthly_data
    price_monthly_data = price_monthly_data1
    global new_monthly_data 
    new_monthly_data = new_monthly_data1
    global indexgspc 
    global spy_yoy_tickers 
 
    indexgspc = indexgspc1.copy()
    spy_yoy_tickers = spy_yoy_tickers1.copy()
    results = []
    yearly_returns=[]
    global oos1_new_performance1
    for i in range(n_simulations):
        if rebal_freq == 'drm' or rebal_freq == 'm':
            oos1_new_performance, expected_betas, rebalance_opt_weights = new_run_with_backtest_mrebalance_front_end(
                type,
                in_years1,
                out_years,
                mbetaA,
                mbetaB,
                mbetaC,
                starting_budget,
                rebal_freq,
                c_portf,
                obj_key
            )
            #return oos1_new_performance, None, None, expected_betas, rebalance_opt_weights
        elif rebal_freq == 'pre_drm':
            oos1_list, oos1_avg, oos1_y, expected_betas, rebalance_opt_weights = get_premade_mrebalance_front_end(
            out_years, obj_key, n_simulations
            )
            return oos1_list, oos1_y, oos1_avg, expected_betas, rebalance_opt_weights
        globals()[f'x{i}_df']=oos1_new_performance.copy()
        globals()[f'y{i}_df']=new_performances.copy()
        results.append(globals()[f'x{i}_df'])
        yearly_returns.append(globals()[f'y{i}_df'])

    sums = {key: 0 for key in yearly_returns[0]}
    for d in yearly_returns:
        for key, value in d.items():
            sums[key] += value
    num_dicts = len(yearly_returns)
    averages = {key: sums[key] / num_dicts for key in sums}
    return results,yearly_returns,averages, expected_betas, rebalance_opt_weights
# In[135]:

def get_premade_mrebalance_front_end(os_years, obj, num_iteration):
    results = []
    expected_betas = []

    for i in range(num_iteration):
        path = SCRIPT_DIR / f"Front_End_Strategies_Iteration_4c_excess_surrogate/pre_raw/pre_made_df_{obj}.csv"
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df = df.iloc[-(os_years * 12):]
        results.append(df)

    # Build expected_betas from first run's index (all runs share same dates)
    for date in results[0].index:
        file_date = (date - pd.DateOffset(days=1)).strftime('%Y-%m-%d')
        rebal_path = (
            SCRIPT_DIR
            / f"Front_End_Strategies_Iteration_4c_excess_surrogate/{obj}/rebal_explored_{obj}_{file_date}.csv"
        )
        rebal_df = pd.read_csv(rebal_path)
        best = rebal_df.nlargest(1, 'reward').iloc[0]
        expected_betas.append([best['c1'], best['c2'], best['c3']])

    return results, None, None, expected_betas, None


def expand_performance2(df):
    # Initialize the list with the first dataframe
    dflist = [df]
    size = len(df)
    
    for i in range(1, size):  # Loop through the dataframe rows (starting from 1)
        # Get the last value of 'Optimized Portfolio' and 'SP_500' from the previous dataframe
        prev_eoy_performance = dflist[i-1]['Optimized Portfolio'][-1]
        prev_eoy_spy = dflist[i-1]['SP_500'][-1]
        
        # Create a new dataframe by copying the previous dataframe
        new_df = dflist[i-1].copy()
        
        # Apply the performance change to the new dataframe
        new_df['Optimized Portfolio'] *= prev_eoy_performance
        new_df['SP_500'] *= prev_eoy_spy
        
        # Append the new dataframe to the list
        dflist.append(new_df)
    
    return dflist


# In[136]:


# In[141]:


def famafrenchreturns_FS():
    global ff3_monthly_FS
    ff3_monthly_FS = pd.read_csv(SCRIPT_DIR / 'ff3_wrds.csv')
    ff3_monthly_FS.set_index(ff3_monthly_FS['dateff'], inplace=True)
    ff3_monthly_FS.index.name = 'Date'
    ff3_monthly_FS = ff3_monthly_FS.drop(columns={'dateff'})
    ff3_monthly_FS.columns = 'Mkt-RF','SMB','HML','RF'
    ff3_monthly_FS.index = pd.to_datetime(ff3_monthly_FS.index)
    ff3_monthly_FS.index = ff3_monthly_FS.index.to_period('M').to_timestamp('D')
    # Keeping Only the Dates in the monthly_data

    dates = rebalance_optimal_weights_appended.index
    dates_minus_3_years = pd.DatetimeIndex([d - relativedelta(years=3) for d in dates])
    combined_dates_index = dates.append(dates_minus_3_years).sort_values()

    ff3_monthly_FS = ff3_monthly_FS.loc[combined_dates_index]
    ff3_monthly_FS = ff3_monthly_FS.groupby(level=0).last()  # or .mean(), etc.
    ff3_monthly_FS = ff3_monthly_FS.asfreq('MS')  
    ff3_monthly_FS = ff3_monthly_FS.interpolate(method='linear')


def portoflio_ff3(opt_portf): # input output from optimal_weights_appended
    start_reg = opt_portf.index.min()
    end_reg = opt_portf.index.max() 

    rf = ff3_monthly.loc[start_reg:end_reg]["RF"]
    rolling_excess = opt_portf.sub(rf,axis=0)
    rebal_betas = pd.DataFrame()

    for col in rolling_excess.columns:
        # Set the dependent variable (Return of stock i)
        y = rolling_excess[col]
        # Set the independent variables (Fama French 3 Factors)
        X = (ff3_monthly[['Mkt-RF','SMB','HML']].loc[start_reg:end_reg])
        # Fit the multiple linear regression model
        model = LinearRegression()
        model.fit(X, y)
        # Store the results in the DataFrame
        rebal_betas[col] = [model.intercept_] + model.coef_.tolist()
    rebal_betas = rebal_betas.T
    rebal_betas.columns = ['Intercept','Mkt-RF','SMB','HML']
    ff3_factors = rebal_betas.mul(opt_portf.iloc[-1], axis=0).sum()
    ff3_factors = ff3_factors.iloc[1:]

    return ff3_factors*100

# In[142]:


def performance_metrics(df_roi,periods_per_year):
    start = str(df_roi.index[0])
    end   = str(df_roi.index[-1])

    rf = ff3_monthly[start:end]['RF']

    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # 1) Monthly arithmetic returns
    # ------------------------------------------------------------
    monthly_ret = df_roi.pct_change().dropna()

    # ------------------------------------------------------------
    # 2) Summary statistics
    # ------------------------------------------------------------
    # Cumulative returns
    cumulative_ret = df_roi.iloc[-1] / df_roi.iloc[0] - 1

    # Annualized returns (use number of monthly returns in denominator)
    ann_return = (1 + cumulative_ret)**(periods_per_year / len(monthly_ret)) - 1

    # Annualized volatility
    vol = monthly_ret.std() * np.sqrt(periods_per_year)

    # Proper downside deviation (Sortino) relative to monthly RF
    mar = rf.mean()
    downside_diff = np.minimum(monthly_ret - mar, 0)  # only negative deviations
    downside_vol = np.sqrt((downside_diff**2).mean()) * np.sqrt(periods_per_year)

    # Excess return vs RF
    excess = monthly_ret.sub(rf)
    ann_excess_ret = excess.mean() * periods_per_year

    # Ratios
    sharpe = ann_excess_ret / vol
    sortino = ann_excess_ret / downside_vol

    stats = pd.DataFrame({
        "Cumulative Return (%)": cumulative_ret.mul(100).round(2),
        "Annualized Return (%)": ann_return.mul(100).round(2),
        "Volatility (%)":        vol.mul(100).round(2),
        "Downside Vol (%)":      downside_vol.mul(100).round(2),
        "Sharpe":                sharpe.round(3),
        "Sortino":               sortino.round(3)
    }).T
    return(stats)


# In[143]:


def analyze_portfolios(df_roi,periods_per_year):
    #famafrenchreturns_FS()
    start = str(df_roi.index[0])
    end   = str(df_roi.index[-1])

    rf = ff3_monthly[start:end]['RF']
    # ------------------------------------------------------------
    # 1) Monthly arithmetic returns
    # ------------------------------------------------------------
    monthly_ret = df_roi.pct_change().dropna()

    # ------------------------------------------------------------
    # 2) Summary statistics
    # ------------------------------------------------------------
    # Cumulative returns
    cumulative_ret = df_roi.iloc[-1] / df_roi.iloc[0] - 1

    # Annualized returns (use number of monthly returns in denominator)
    ann_return = (1 + cumulative_ret)**(periods_per_year / len(monthly_ret)) - 1

    # Annualized volatility
    vol = monthly_ret.std() * np.sqrt(periods_per_year)

    # Proper downside deviation (Sortino) relative to monthly RF
    mar = rf.mean()
    downside_diff = np.minimum(monthly_ret - mar, 0)  # only negative deviations
    downside_vol = np.sqrt((downside_diff**2).mean()) * np.sqrt(periods_per_year)

    # Excess return vs RF
    excess = monthly_ret.sub(mar)
    ann_excess_ret = excess.mean() * periods_per_year

    # Ratios
    sharpe = ann_excess_ret / vol
    sortino = ann_excess_ret / downside_vol

    stats = pd.DataFrame({
        "Cumulative Return (%)": cumulative_ret.mul(100).round(2),
        "Annualized Return (%)": ann_return.mul(100).round(2),
        "Volatility (%)":        vol.mul(100).round(2),
        "Downside Vol (%)":      downside_vol.mul(100).round(2),
        "Sharpe":                sharpe.round(3),
        "Sortino":               sortino.round(3)
    }).T

    # ------------------------------------------------------------
    # 3) Color logic
    # ------------------------------------------------------------
    optimized_color   = '#174a7e'   # blue (for Optimized)
    yearly_dyn_color  = '#cc5500'   # orange
    nondyn_color      = 'black'     # benchmarks / others

    def color_for(col_name: str) -> str:
       # Optimized portfolios
        if "Optimized" in col_name:
            return optimized_color
        # Yearly dynamic / yearly rebalancing
        if "Yearly" in col_name:
            return yearly_dyn_color
        # Fallback for everything else (SP500, etc.)
        if "Resampled" in col_name:
            return "#0072B2"
        if "Surrogate" in col_name:
            return '#ADD8E6'
        return nondyn_color

    # Helper: mark only January points for yearly series (for dynamic yearly if needed)
    jan_marks = [i for i, d in enumerate(df_roi.index)
                 if getattr(d, "month", None) == 1]

    # ------------------------------------------------------------
    # 4) Cumulative ROI plot
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    for col in df_roi.columns:
        col_color = color_for(col)

        # Optimized: blue with a dot every month
        if "Optimized" in col:
            ax.plot(df_roi.index, df_roi[col],
                    label=col,
                    linewidth=1.8,
                    color=col_color,
                    marker="o",
                    markersize=3)
        # Optional: dynamic yearly series with Jan-only markers
        elif "Dynamic" in col and "Yearly" in col:
            ax.plot(df_roi.index, df_roi[col],
                    label=col,
                    linewidth=1.8,
                    color=col_color,
                    marker="o",
                    markersize=5,
                    markevery=jan_marks)
        else:
            ax.plot(df_roi.index, df_roi[col],
                    label=col,
                    linewidth=1.8,
                    color=col_color)

    ax.set_title("Optimized vs Dynamic Rebalancing: Cumulative ROI", fontsize=14, pad=12)
    ax.set_ylabel("ROI")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    # ------------------------------------------------------------
    # 5) Drawdown helper
    # ------------------------------------------------------------
    def drawdown(series: pd.Series) -> pd.Series:
        peak = series.cummax()
        dd = (series / peak) - 1.0
        return dd

    drawdowns = df_roi.apply(drawdown)

    # ------------------------------------------------------------
    # 6) Drawdown chart (replaces monthly returns plot)
    #    - Matches color logic
    #    - Optimized in blue with monthly dots
    # ------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(10, 5), dpi=150)

    for col in drawdowns.columns:
        col_color = color_for(col)

        if "Optimized" in col:
            ax2.plot(
                drawdowns.index,
                100 * drawdowns[col],
                label=col,
                linewidth=2,
                color=col_color,
                marker="o",
                markersize=3
            )
        else:
            ax2.plot(
                drawdowns.index,
                100 * drawdowns[col],
                label=col,
                linewidth=2,
                color=col_color
            )

    ax2.set_title("Drawdowns Over Time", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("")
    ax2.grid(alpha=0.2, linestyle="--")
    ax2.legend(frameon=False)

    # Remove top/right spines for cleaner look
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # Optional shading for benchmark + optimized
    # Adjust names if your columns differ (e.g., "SP500", "S&P 500")
    if "SP_500" in drawdowns.columns:
        sp_col = "SP_500"
        ax2.fill_between(
            drawdowns.index,
            100 * drawdowns[sp_col],
            0,
            where=(drawdowns[sp_col] < 0),
            interpolate=True,
            alpha=0.07,
            color=color_for(sp_col),
        )

    if "Optimized Portfolio" in drawdowns.columns:
        opt_col = "Optimized Portfolio"
        ax2.fill_between(
            drawdowns.index,
            100 * drawdowns[opt_col],
            0,
            where=(drawdowns[opt_col] < 0),
            interpolate=True,
            alpha=0.07,
            color=color_for(opt_col),
        )

    plt.tight_layout()
    plt.show()
    return monthly_ret, stats


# In[144]:


def plot_monthly_betas():
    rebalanced_optimal_weights_m()
    famafrenchreturns_FS()
    
    # Extracting expected values for calculation
    mkt_rf_e = np.array([x[0] for x in expected_betas])
    smbe = np.array([x[1] for x in expected_betas])
    hmle = np.array([x[2] for x in expected_betas])
    
    # Converting actual betas to numpy arrays for vector math
    mkt_rf_a = np.array(mkt_bet)
    smba = np.array(smb_bet)
    hmla = np.array(hml_bet)
    
    # 1a. Calculate MSE for each factor
    mse_mkt = np.mean((mkt_rf_a - mkt_rf_e)**2)
    mse_smb = np.mean((smba - smbe)**2)
    mse_hml = np.mean((hmla - hmle)**2)
    # 1b. Calculate MAE for each factor

    mae_mkt = np.mean(abs(mkt_rf_a - mkt_rf_e))
    mae_smb = np.mean(abs(smba - smbe))
    mae_hml = np.mean(abs(hmla - hmle))
    
    idx = rebalance_optimal_weights_appended.index
    n_p = 'Monthly'
    m_size = 3
    mark_every = 1

    # Helper to add MSE to plot
    def add_mse_label(ax, mse_val):
        textstr = f'Total MSE: {mse_val:.6f}'
        # Position box in the upper left of the plot
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)

    # --- Mkt-RF Plot ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(idx, mkt_rf_a, label='Mkt-RF (Actual)', color='red', marker='o', markersize=m_size, markevery=mark_every)
    ax.plot(idx, mkt_rf_e, label='Expected Betas', color='black', linestyle='--')
    add_mse_label(ax, mse_mkt)
    ax.set_title(f'Mkt-RF Factor {n_p}', fontsize=18, weight='bold')
    ax.legend()
    plt.xticks(rotation=45)
    plt.show()

    # --- SMB Plot ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(idx, smba, label='SMB (Actual)', color='blue', marker='o', markersize=m_size, markevery=mark_every)
    ax.plot(idx, smbe, label='Expected Betas', color='black', linestyle='--')
    add_mse_label(ax, mse_smb)
    ax.set_title(f'SMB Factor {n_p}', fontsize=18, weight='bold')
    ax.legend()
    plt.xticks(rotation=45)
    plt.show()

    # --- HML Plot ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(idx, hmla, label='HML (Actual)', color='green', marker='o', markersize=m_size, markevery=mark_every)
    ax.plot(idx, hmle, label='Expected Betas', color='black', linestyle='--')
    add_mse_label(ax, mse_hml)
    ax.set_title(f'HML Factor {n_p}', fontsize=18, weight='bold')
    ax.legend()
    plt.xticks(rotation=45)
    plt.show()

    # --- Print Summary ---
    print("-" * 30)
    print(f"BETA TRACKING ERROR (MSE)")
    print("-" * 30)
    print(f"Mkt-RF MSE: {mse_mkt:.8f}")
    print(f"SMB MSE:    {mse_smb:.8f}")
    print(f"HML MSE:    {mse_hml:.8f}")
    print(f"AVERAGE:    {(mse_mkt + mse_smb + mse_hml)/3:.8f}")
    print('**********')
    print(f"Mkt-RF MAE: {mae_mkt:.8f}")
    print(f"SMB MAE:    {mae_smb:.8f}")
    print(f"HML MAE:    {mae_hml:.8f}")
    print(f"AVERAGE:    {(mae_mkt + mae_smb + mae_hml)/3:.8f}")
    print("-" * 30)


# In[145]:


def plot_yearly_betas():
    famafrenchreturns_FS()
    monthly_beta = []
    mark_every = 12 
    m_size = 8
    rebalanced_optimal_weights_y()
    n_p = 'Yearly'
    for i,month in enumerate(rebalance_optimal_weights_appended.index):
        perfm = rebalance_optimal_weights_appended.loc[[month]]
        betas = to__cal_stock_betas_monthly(i,month,perfm)
        monthly_beta.append(betas)
    fig, ax = plt.subplots(figsize=(12, 6))
    #mkt_rf_a = [x[0] for x in monthly_beta]
    
    ax.plot(avg_dry.index, mkt_rf_a, label='Mkt-RF', color='red', marker = 'o', markersize=m_size, markevery=mark_every)
    mkt_rf_e = [x[0] for x in expected_betas]
    mkt_rf_e.append(mkt_rf_e[58])
    ax.plot(avg_dry.index, mkt_rf_e, label='Expected Betas', color='black')
    ax.set_xlabel('Date (MoM)', fontsize=14)
    ax.set_ylabel('Mkt-RF Factor Beta', fontsize = 14)
    ax.set_title(f'Mkt-RF Factor {n_p}', fontsize = 18, weight='bold')
    plt.xticks(rotation=45)
    ax.legend(fontsize=12)
    plt.show()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    smba = [x[1] for x in monthly_beta]
    ax.plot(avg_dry.index, smba, label='SMB', color='blue', marker = 'o', markersize=m_size, markevery=mark_every)
    smbe = [x[1] for x in expected_betas]
    smbe.append(smbe[58])
    ax.plot(avg_dry.index, smbe, label='Expected Betas', color='black')
    ax.set_xlabel('Date (MoM)', fontsize=14)
    ax.set_ylabel('SMB Factor Beta', fontsize = 14)
    ax.set_title(f'SMB Factor {n_p}', fontsize = 18, weight='bold')
    plt.xticks(rotation=45)
    ax.legend(fontsize=12)
    plt.show()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    hmla = [x[2] for x in monthly_beta]
    ax.plot(avg_dry.index, hmla, label='HML', color='green', marker = 'o', markersize=m_size, markevery=mark_every)
    hmle = [x[2] for x in expected_betas]
    hmle.append(hmle[58])
    ax.plot(avg_dry.index, hmle, label='Expected Betas', color='black')
    ax.set_xlabel('Date (MoM)', fontsize=14)
    ax.set_ylabel('HML Factor Beta', fontsize = 14)
    ax.set_title(f'HML Factor {n_p}', fontsize = 18, weight='bold')
    plt.xticks(rotation=45)
    ax.legend(fontsize=12)
    plt.show()


# In[146]:


def to__cal_stock_betas_monthly(i, start, opt_weights_appended):
    
    if(len(opt_weights_appended) > 1):  
        list = opt_weights_appended.iloc[i]
    else:
        list = opt_weights_appended.iloc[0]
        
    list = list[list !=0]
    
    start111 = start - relativedelta(years=3)
    end111 = start111 + relativedelta(months=35)
    rf = ff3_monthly_FS['RF'].loc[start111:end111]
    rolling_rebal = extract_stock_data(new_monthly_data, list.index, start111, end111)
    rolling_excess = rolling_rebal.sub(rf, axis=0)
    rebal_betas = pd.DataFrame()
    # Iterate over the tickers list
    for col in rolling_excess.columns:
        # Set the dependent variable (Return of stock i)
        y = rolling_excess[col]
        # Set the independent variables (Fama French 3 Factors)
        X = (ff3_monthly_FS[['Mkt-RF','SMB','HML']].loc[start111:end111])
        # Fit the multiple linear regression model
        model = LinearRegression()
        model.fit(X, y)
        # Store the results in the DataFrame
        rebal_betas[col] = [model.intercept_] + model.coef_.tolist()
    rebal_betas = rebal_betas.T
    rebal_betas.columns = ['Intercept','Mkt-RF','SMB','HML']
    ff3_factors = rebal_betas.mul(list, axis=0).sum()
    ff3_factors = ff3_factors.iloc[1:]
    
    return ff3_factors 


# In[147]:


def rebalanced_optimal_weights_y():
    global rebalance_optimal_weights_appended

    full_tickers = list(price_monthly_data.columns)

    all_years = sorted(oos1_list[0].index.year.unique())

    n_rebals = len(rebalance_opt_weights)
    rebal_years = all_years[:n_rebals]

    rebalance_optimal_weights_appended = pd.DataFrame()

    for year, df_weights in zip(rebal_years, rebalance_opt_weights):
        expanded = df_weights.reindex(full_tickers).fillna(0.0)

        expanded.columns = df_weights.columns
        temp_df = optimal_weights_appended(expanded)  # returns Date × Ticker

        mask = (temp_df.index.year == year)
        temp_df = temp_df.loc[mask]

        rebalance_optimal_weights_appended = pd.concat(
            [rebalance_optimal_weights_appended, temp_df]
        )
    non_zero_cols = (rebalance_optimal_weights_appended != 0).any(axis=0)
    rebalance_optimal_weights_appended = rebalance_optimal_weights_appended.loc[:, non_zero_cols]


# In[148]:


def rebalanced_optimal_weights_m(oos1_list,rebalance_opt_weights,price_monthly_data):
    global rebalance_optimal_weights_appended 
    
    full_tickers = price_monthly_data.columns

    # All months from your OOS index
    all_months = oos1_list.index#.to_period("M").unique()

    # Use one month per weights DataFrame
    n_rebals = len(rebalance_opt_weights)  # e.g., 59
    rebal_months = all_months[:n_rebals]

    rows = []

    for period, df_weights in zip(rebal_months, rebalance_opt_weights):        
        if isinstance(df_weights, pd.DataFrame):
            w = df_weights.iloc[:, 0]  # first (and only) column
        else:
            w = df_weights

        # Expand to full ticker universe, missing → 0
        w_full = w.reindex(full_tickers, fill_value=0.0)

        # Use the month’s date as the row index (choose start or end of month)
        w_full.name = period.to_timestamp("D")  # first of month

        rows.append(w_full)

    # Combine into a single DataFrame: Date × Ticker
    result = pd.DataFrame(rows)
    result.index.name = "Date"
    # last_month = result.iloc[-1]
    # result.loc[end_date] = last_month
    non_zero_cols = (result != 0).any(axis=0)
    rebalance_optimal_weights_appended = result.loc[:, non_zero_cols]
    return rebalance_optimal_weights_appended


# In[149]:


def optimal_weights_appended(opt_port):  
    
    tickers_opt = opt_port.index.tolist()
    prices = extract_stock_data(price_monthly_data, tickers_opt, target_date-relativedelta(years=3), target_date)
    
    # if value is NA, averages it with the before and after, as it would be too difficult to manually enter it if we scale up the use of this
    prices = prices.interpolate(method = 'linear', limit_direction = 'both') 
    base_prices = prices.iloc[0]
    holding_values = pd.DataFrame(index=prices.index, columns=prices.columns)
    for tickers_opt in prices.columns:
        weight_opt = opt_port.loc[tickers_opt].iloc[0]
        # (price / price_base) * initial_weight.
        holding_values[tickers_opt] = (prices[tickers_opt] / base_prices[tickers_opt]) * weight_opt

    # calc total portfolio value for each month.
    portfolio_value = holding_values.sum(axis=1)
    
    # normalize the values
    opt_portfolio_weights_appended = holding_values.div(portfolio_value, axis=0)
    return opt_portfolio_weights_appended


def run_sp500_data():
    
    index = pd.read_csv(SCRIPT_DIR / 'spy_data.csv')
    indexgspc1 = index.copy()
    indexgspc1.rename(columns={'DATE':'Date', 'sprtrn':'SP_500'}, inplace=True)
    indexgspc1.drop(columns={'vwretd', 'spindx'}, inplace=True)
    indexgspc1.set_index('Date', inplace=True)
    indexgspc1.index = pd.to_datetime(indexgspc1.index)
    indexgspc1 = indexgspc1.dropna()
    indexgspc1 = indexgspc1.drop(columns=['Unnamed: 0'])
    indexgspc1 = update_spy(indexgspc1)
    spy_mom = pd.read_excel(SCRIPT_DIR / 'Total SPX.xlsx')
    spy_mom['Year'] = spy_mom['Source.Name'].str.extract(r'(\d{4})').astype(int)
    spy_mom.set_index('Year', inplace = True)
    spy_mom['Ticker'] = spy_mom['Ticker'].str.replace(r' [A-Z]{2,3} Equity$', '', regex=True)
    spy_mom = spy_mom[['Ticker']]
    spy_mom = spy_mom[~spy_mom['Ticker'].str.contains(r'\d', na=False)]
    spy_mom = spy_mom.reset_index()
    grouped = spy_mom.groupby('Year')['Ticker'].apply(list)
    grouped = pd.DataFrame(grouped.tolist(), index=grouped.index)
    grouped.columns = ["" for _ in grouped.columns]
    spy_yoy_tickers1 = grouped
    
    return indexgspc1, spy_yoy_tickers1

def update_spy(indexgspc1):
    ts = TimeSeries(key='CPT85HPR5S2L405H', output_format='pandas')
    data, meta_data = ts.get_monthly_adjusted(symbol='SPY')
    
    # Clean column names
    data.columns = [col.split('. ')[1] for col in data.columns]
    
    # Sort ascending (AV returns descending)
    data = data.sort_index(ascending=True)
    
    # Calculate return: pct change from previous month's adjusted close
    data['SP_500'] = data['close'].pct_change()
    
    # Re-index to 1st of the month to match your convention
    # (Dec 1st = return from Nov 1st close to Dec 1st close)
    data.index = data.index.to_period('M').to_timestamp()  # 'MS' = month start
    
    # Filter to only new months not already in indexgspc1
    latest_date = indexgspc1.index.max()
    data = data[data.index > latest_date]
    av_spy = data['SP_500'].dropna() 
    indexgspc1 = pd.concat([indexgspc1,av_spy])
    return indexgspc1


# In[152]:


def run_N50_data():
    #   Indian Market Run 
    new_data1=pd.read_csv(SCRIPT_DIR / 'nifty_stocks_data (1).csv')
    new_data1.drop(columns='PERMNO',inplace=True)
    new_data1.rename(columns={'date':'Date','TICKER':'Ticker'},inplace=True)
    index=pd.read_csv(SCRIPT_DIR /'spy_data.csv')
    indexgspc1=index.copy()
    indexgspc1.rename(columns={'DATE':'Date','sprtrn':'SP_500'},inplace=True)
    indexgspc1.drop(columns={'vwretd','spindx'},inplace=True)
    indexgspc1.set_index('Date',inplace=True)
    indexgspc1.index = pd.to_datetime(indexgspc1.index)
    indexgspc1=indexgspc1.dropna()
    indexgspc1 = indexgspc1.drop(columns=['Unnamed: 0'])

    n_50 = pd.read_csv(SCRIPT_DIR /'Nifty_50.csv')
    n_50 = n_50.replace("BAJAJ-AUTO", np.nan)

    n_50.set_index('Year', inplace=True)
    n50_view = n_50.copy()
    n50_view.columns = [''] * n50_view.shape[1]
    n50_view.index.name = 'Year'
    n50_view.columns.name = None
    n50_view = n50_view.astype(object).where(n50_view.notna(), None)
    spy_yoy_tickers1 = n50_view.copy()
    return new_data1, indexgspc1, spy_yoy_tickers1


def update_stock_data(price_monthly_data, new_monthly_data,indexgspc1,spy_yoy_tickers1):
    global results
    if test() == None:
        return price_monthly_data, new_monthly_data
    tickers_to_scrape = spy_yoy_tickers1.stack().unique().tolist()
    total_tickers = len(tickers_to_scrape)
    current_date = pd.Timestamp.now()
    curr_month = (current_date).to_period('M').to_timestamp()
    latest_date = price_monthly_data.index.max() 
    months_to_scrape = []
    current_check = latest_date + pd.DateOffset(months=1)
    current_check = current_check.to_period('M').to_timestamp(how='start').normalize()
    while current_check <= curr_month:
        months_to_scrape.append(current_check)
        current_check = current_check + pd.DateOffset(months=1)
        current_check = current_check.to_period('M').to_timestamp(how='start').normalize()
    months_to_scrape = sorted(months_to_scrape)
    t2s = []
    if not months_to_scrape:
        log = pd.read_csv('scrape_log.csv')
        log.index = log['Ticker']
        t2s = log.loc[log['Status'] == 'RATE_LIMITED', 'Ticker'].tolist()
        tickers_to_scrape = [t for t in t2s if t in tickers_to_scrape]
    for month in price_monthly_data.index.unique():
        non_nan_count = price_monthly_data.loc[month].notna().sum()
    if non_nan_count < total_tickers * 0.65:  
        if month not in months_to_scrape:
            months_to_scrape.append(month)
    if len(tickers_to_scrape) == 0:
        return price_monthly_data, new_monthly_data
    results = []
    print(f'Updating Month(s): {months_to_scrape}')
    for tick1 in tickers_to_scrape:
        results.append(fetch_stooq_full_history(tick1))
 
    series_to_join = []
    for ticker, data, status in results:
        if status == "SUCCESS":
            series_to_join.append(data.rename(ticker.upper()))

    master_df = pd.concat(series_to_join, axis=1)

    master_df.sort_index(inplace=True)
    master_df.index = master_df.index.to_period('M').to_timestamp()
    if len(months_to_scrape) > 1: 
        master_df_adj = master_df.loc[months_to_scrape[0]:months_to_scrape[-1]]
    else: 
        master_df_adj = master_df.loc[months_to_scrape[0]:months_to_scrape[0]]
    
    # Split into existing months (need merge) vs new months (need concat)
    existing_months = [m for m in months_to_scrape if m in price_monthly_data.index]
    new_months = [m for m in months_to_scrape if m not in price_monthly_data.index]
    
    if existing_months:
        price_monthly_data = master_df_adj.loc[existing_months].combine_first(price_monthly_data)
    if new_months:
        price_monthly_data = pd.concat([price_monthly_data, master_df_adj.loc[new_months]])    
          
    price_monthly_data.to_csv('monthly_prices.csv')
    return_df = master_df.pct_change()

# Split into existing months (need merge) vs new months (need concat)
    existing_months = [m for m in return_df.index if m in new_monthly_data.index]
    new_months = [m for m in return_df.index if m not in new_monthly_data.index]

    if existing_months:
        new_monthly_data = return_df.loc[existing_months].combine_first(new_monthly_data)

    if new_months:
        new_monthly_data = pd.concat([new_monthly_data, return_df.loc[new_months]])
    new_monthly_data = new_monthly_data.replace(0.0, np.nan)
    new_monthly_data = new_monthly_data.apply(pd.to_numeric, errors='coerce')
    new_monthly_data.to_csv('monthly_returns.csv')
    log_data = [(res[0], res[2]) for res in results]
    new_log_df = pd.DataFrame(log_data, columns=['Ticker', 'Status'])
    new_log_df.to_csv('scrape_log.csv',index=False)
    
    return price_monthly_data, new_monthly_data

def test(): 
    url = f"https://stooq.com/q/d/l/?s={'a.us'}&i=m"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    text = response.text
    if 'Exceeded the daily hits limit' in text or 'daily hits limit' in text.lower():
        return None
    return 'Good'

def fetch_stooq_full_history(ticker):
    try:
        stooq_ticker = ticker.lower()
        if not stooq_ticker.endswith('.us'):
            stooq_ticker = f"{stooq_ticker}.us"
        
        url = f"https://stooq.com/q/d/l/?s={stooq_ticker}&i=m"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        text = response.text
        
        # Check for rate limit
        if 'Exceeded the daily hits limit' in text or 'daily hits limit' in text.lower():
            return ticker, None, "RATE_LIMITED"
        
        if 'Date' not in text:
            return ticker, None, "NO_DATA"
        
        # Parse CSV
        df = pd.read_csv(StringIO(text))
        if df.empty:
            return ticker, None, "EMPTY"
        
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        if 'Close' not in df.columns:
            return ticker, None, "NO_CLOSE"
        
        return ticker, df['Close'],'SUCCESS'
        
    except Exception as e:
        return ticker, None, "ERROR"
