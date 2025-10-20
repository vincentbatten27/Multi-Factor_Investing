
# To ignore all warnings
import warnings
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
# import getFamaFrenchFactors as gff
from pandas.tseries.offsets import DateOffset
from statsmodels.formula.api import ols
import statsmodels.api as sm
import random
# yf.pdr_override()
import pulp
from sklearn.preprocessing import LabelEncoder
import pandas_datareader.data as reader
import yfinance as yf
import pandas as pd
import requests
# import getFamaFrenchFactors as gff
from pulp import LpProblem, LpMaximize, LpVariable, LpMinimize, LpBinary, lpSum
from pulp import *
import getFamaFrenchFactors as gff
import time
import requests
import os
from openpyxl import load_workbook
yf.pdr_override()
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import cm
# import requests
from bs4 import BeautifulSoup



def extract_stock_data(df, tdickers, start, end):
    """
    Extract stock data for specific tickers between the start and end dates.

    Parameters:
    - df: pandas DataFrame with rows as dates (monthly) and columns as stock tickers.
    - tickers: list of tickers to extract data for.
    - start: start date (YYYY-MM-DD) for the data extraction.
    - end: end date (YYYY-MM-DD) for the data extraction.

    Returns:
    - pandas DataFrame with the specified tickers and date range.
    """
    # Ensure the date column is in datetime format
    df.index = pd.to_datetime(df.index)
    df.index=df.index.to_period('M').to_timestamp('D')
    # Filter the DataFrame for the date range
    df_filtered = df.loc[start:end]

    # Select the tickers from the DataFrame
    df_selected = df_filtered[tdickers]
    df_selected=df_selected.loc[:, df_selected.isna().sum() <= 0].dropna()
    # df_selected.interpolate(method='linear',inplace=True)
    df_selected.index = pd.to_datetime(df_selected.index)
    df_selected = df_selected.tz_localize(None)
    columns = sorted([col for col in df_selected.columns if col != 'Date'])
    df_selected=df_selected[columns]
    for col in df_selected.columns:
        try:
            df_selected[col] = df_selected[col].astype(float)
        except ValueError:
            print(f"Column '{col}' could not be converted to float.")
    df_selected.index=df_selected.index.to_period('M').to_timestamp('D')
    df_selected.replace('C', np.nan, inplace=True)
    for col in df_selected.columns:
            try:
                df_selected[col] = df_selected[col].astype(float)
            except ValueError:
                print(f"Column '{col}' could not be converted to float.")
    df_selected.interpolate(method='linear',inplace=True)
    df_selected = df_selected.fillna(method='ffill')
    df_selected = df_selected.fillna(method='bfill')
    return df_selected



def extract_spy_data(df, start, end):
    df.index = pd.to_datetime(df.index)
    df.index=df.index.to_period('M').to_timestamp('D')
    df_filtered = df.loc[start:end]
    return df_filtered

# Creates tickers ([]), monthly_data (DF), and base_w ([])
def get_spy2(start,end):
    ### Get tickers + setup
    global tickers,spy
    requests.packages.urllib3.disable_warnings()
    # Fetch HTML content
    response = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', verify=False)
    html_content = response.content
    # Read HTML content into pandas DataFrame
    list_of_dfs = pd.read_html(html_content)
    wikitable_sp_500 = list_of_dfs[0]
    sp500_symbols = wikitable_sp_500['Symbol']
    tickers = sp500_symbols.to_list() # Converting SP_500 tickers into list 
    # Remove some tickers as they create an error for the yfinance api
    # print('\namogus\n',tickers,'amogus\n')
    # tickers[65] = 'BRK-B'
    # tickers[81] = 'BF-B'
    try:
        tickers.remove('BF-B')
        tickers.remove('BRK-B')
    except:
        print('\n')
    try:
        tickers.remove('BRK.B')
        tickers.remove('BF.B')
    except:
        print('\n')

    ### Import the monthly data
    global monthly_data
    global base_w
    monthly_data = extract_stock_data(new_monthly_data,tickers,start=start,end=end)
    if 'GEN' in monthly_data.columns:
        monthly_data.drop(columns={'GEN'},inplace=True)
    if 'COR' in monthly_data.columns:
        monthly_data.drop(columns={'COR'},inplace=True)
    if 'FI' in monthly_data.columns:
        monthly_data.drop(columns={'FI'},inplace=True) 
    if 'KEYS' in monthly_data.columns:
        monthly_data.drop(columns={'KEYS'},inplace=True) 
    if 'MS' in monthly_data.columns:
        monthly_data.drop(columns={'MS'},inplace=True) 
    if 'AXON' in monthly_data.columns:
        monthly_data.drop(columns={'AXON'},inplace=True) 
        # AXON
   
 
     # Reformat Date Index 
    # # monthly_data = monthly_data['Adj Close'].pct_change() # Turn Adj Close prices into pct returns
    # monthly_data = monthly_data.drop(monthly_data.index[0]) #Drop First row NaN values
    # monthly_data = monthly_data.dropna(axis=1) # Drop if stock doesnt have data starting from the first index date
    
    

    '''
    Structure of monthly_data:
    rows: new date
    columns: various tickers drawn from the S&P 500
    '''

    # Assign equal weight as base weights
    base_w = {k: 1/len(monthly_data.columns) for k in monthly_data.columns}
    base_w = pd.DataFrame.from_dict(base_w, orient='index', columns=['Weight'])
    # Getting SP_500 data
    # spy = pd.DataFrame(yf.download('^GSPC',start=start,end=end,interval='1mo')['Adj Close'].pct_change())#Dropping First Row(NaN) and formatting index to match monthly_data 
    # spy = spy.drop(spy.index[0]).tz_localize(None)
    # monthly_data['SP_500'] = spy['Adj Close'] # Adding SP_500 data to monthly_data
    # for col in monthly_data.columns:
    #     monthly_data[col]=monthly_data[col].astype(float)
    # monthly_data.index=monthly_data.index.to_period('M').to_timestamp('D')
    spy=extract_spy_data(indexgspc,start,end)
    print(monthly_data.index.equals(spy.index))
    if monthly_data.index.equals(spy.index)==True:
        for i,j in monthly_data.iterrows():
            monthly_data.loc[i,'SP_500']=spy.loc[i,'SP_500']
    # spy = pd.DataFrame(yf.download('^GSPC',start=start,end=end,interval='1mo')['Adj Close'].pct_change())#Dropping First Row(NaN) and formatting index to match monthly_data 
    # spy = spy.drop(spy.index[0]).tz_localize(None)#Adding SP_500 data to monthly_data
    # Adjusting tickers list as some tickers will not be included in the monthly_data if there is no data for test date range
    tickers = list(monthly_data.columns[:-1]) 
    tick_index = tickers + ['SP_500']
    # return spy



def download_with_retry(tickers, start, end, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return extract_stock_data(new_monthly_data,tickers, start=start, end=end)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception(f"Failed to download data after {retries} attempts.")


def get_spy(beta1,beta2,beta3,start,end):
  
    global tickers
    requests.packages.urllib3.disable_warnings() 
    # Fetch HTML content
    response = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', verify=False)
    html_content = response.content
    # Read HTML content into pandas DataFrame
    list_of_dfs = pd.read_html(html_content)
    wikitable_sp_500 = list_of_dfs[0]
    sp500_symbols = wikitable_sp_500['Symbol']#Converting SP_500 tickers into list 
    tickers = sp500_symbols.to_list()#Remove some tickers as they create an error for the yfinance api
    tickers[65] = 'BRK-B'
    tickers[81] = 'BF-B'
    tickers.remove('BF-B')
    tickers.remove('BRK-B')#Start Date for In Sample Historical Data
    global monthly_data
    global base_w
    monthly_data = extract_stock_data(new_monthly_data,tickers,start=start,end=end)#Reformat Date Index 
    monthly_data.index = pd.to_datetime(monthly_data.index)
    monthly_data = monthly_data.tz_localize(None)#Turn Adj Close prices into pct returns
    monthly_data.index=monthly_data.index.to_period('M').to_timestamp('D')
    # monthly_data = monthly_data['Adj Close'].pct_change()#Drop First row NaN values
    # monthly_data = monthly_data.drop(monthly_data.index[0])#Drop if stock doesnt have data starting from the first index date
    # monthly_data = monthly_data.dropna(axis=1)#Assign equal weight as base weights
    
    base_w = {k: 1/len(monthly_data.columns) for k in monthly_data.columns}
    base_w = pd.DataFrame.from_dict(base_w, orient='index', columns=['Weight'])#Getting SP_500 data
    spy=extract_spy_data(indexgspc,start,end)
    # spy = pd.DataFrame(yf.download('^GSPC',start=start,end=end,interval='1mo')['Adj Close'].pct_change())#Dropping First Row(NaN) and formatting index to match monthly_data 
    # spy = spy.drop(spy.index[0]).tz_localize(None)#Adding SP_500 data to monthly_data
    monthly_data['SP_500'] = spy['SP_500']
    #Adjusting tickers list as some tickers will not be included in the monthly_data if there is no data for test date range
    
    tickers = list(monthly_data.columns[:-1])
    tick_index = tickers + ['SP_500']

def famafrenchreturns():
    global ff3_monthly
    # Fama French Monthly Returns Data using getFamaFrenchFactors module
    ff3_monthly = gff.famaFrench3Factor(frequency='m')
    ff3_monthly.rename(columns={"date_ff_factors": 'Date'}, inplace=True)
    ff3_monthly.set_index('Date', inplace=True)
    ff3_monthly.index = ff3_monthly.index.to_period('M').to_timestamp('D')
    # Keeping Only the Dates in the monthly_data
    ff3_monthly = ff3_monthly.loc[monthly_data.index]

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
 
def to_cal_stock_price(startt,endd,price_monthly_data):
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

def Transaction_Costs(initialize=False):
    if initialize:
        random.seed(1)  # Set seed only during initialization
    global t_cost
    t_cost = {}
    global keys
    keys = list(tickers)
    values = list(random.uniform(.01, .02) for i in range(len(tickers)))
    for key, value in zip(keys, values):
        t_cost[key] = value

def optimization():
# OPTIMIZATION MODEL
    global index
    global wei
    global aux
    global err
    global binary
    global tr_cost
    global shares
    index = LpProblem('Index', LpMinimize) 
    # Decision Variables
    wei = LpVariable.dicts('Weight',tickers,lowBound=0)                           # Weights for stock i in the optimal portfolio
    aux = LpVariable.dicts('Y',tickers,lowBound=0)                                # Absolute value of change for stock i from base weights
    err = LpVariable.dicts('Error', monthly_data.index, lowBound=0)               # Error term for portfolio
    binary = LpVariable.dicts('bin',tickers,cat=LpBinary)                         # Used if we want to limit the # of stocks we want to have in optimal portfolio
    tr_cost = LpVariable.dicts('Transaction_Cost',tickers,lowBound=0)             # Total Transaction cost for stock i in the optimal portfolio
    shares = LpVariable.dicts('shares',tickers,lowBound=0)                        # Total Transaction cost for stock i in the optimal portfolio
    #Objective Function - Minimize the error term 
    index +=  lpSum(err[t] for t in monthly_data.index) # Constraint: Weights sum to 1 
    index += lpSum(wei[i] for i in tickers) == 1
    # Constraint: Absolute value of change in weights from base weigths
    for i in tickers:
        index += aux[i] >= base_weights[i]  - wei[i]
        index += aux[i] >= wei[i] - base_weights[i]
    index += lpSum(aux[i] for i in tickers) <= 1 
    # Constraint: Error term
    for t in monthly_data.index:
        index += lpSum(wei[i]*(monthly_data.loc[t,i]-ff3_monthly.loc[t,'RF']) for i in tickers) - err[t] <= (mkt_opt*ff3_monthly.loc[t,'Mkt-RF']+smb_opt*ff3_monthly.loc[t,'SMB']+hml_opt*ff3_monthly.loc[t,'HML'])
        index += lpSum(wei[i]*(monthly_data.loc[t,i]-ff3_monthly.loc[t,'RF']) for i in tickers) + err[t] >= (mkt_opt*ff3_monthly.loc[t,'Mkt-RF']+smb_opt*ff3_monthly.loc[t,'SMB']+hml_opt*ff3_monthly.loc[t,'HML'])
    # Shares
    for i in tickers:
        index += shares[i] == (aux[i]*B/s_price[i])
    # Transaction Costs
    for i in tickers:
        index += lpSum(aux[i] *B*t_cost[i]/s_price[i]) == tr_cost[i]
    index += lpSum(tr_cost[i] for i in tickers) <= 2000
    # Limit # of stocks in Optimal Portfolio
    for i in tickers: # Forces weight of stock i to be less than binary value of stock i. If stock is not selected binary variable is 0 which then forces weight of stock i to be in the optimal portfolio to be 0.
        index += wei[i] <= binary[i]
    index += lpSum(binary[i] for i in tickers) <= q
    index.solve()

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
    
def simulator(beta1,beta2,beta3,begin,final,budget,number,universe,new_monthly_data,indexgspc,price_monthly_data):
    global start
    global end
    start=begin
    end=final
    
    # get_spy2(start,end)
    get_spy2(start,end,universe,new_monthly_data,indexgspc)
    #Adjusting tickers list as some tickers will not be included in the monthly_data if there is no data for test date range
    global tickers
    tickers = list(monthly_data.columns[:-1])
    tick_index = tickers + ['SP_500']
    

    # TARGET FACTOR BETAS 
    global base_weights
    global mkt_opt
    global smb_opt
    global hml_opt
    global B
    global q
    
    mkt_opt = beta1                          # TARGET MKT BETA - EXPOSURE OF THE NEW PORTFOLIO TO MARKET FACTOR 
    smb_opt = beta2                           # TARGET SMB BETA - EXPOSURE OF THE NEW PORTFOLIO TO SIZE FACTOR 
    hml_opt = beta3                           # TARGET HML BETA - EXPOSURE OF THE NEW PORTFOLIO TO VALUE FACTOR 
    B = budget                             # BUDGET
    q = number                                # NUMBER OF STOCKS IN THE NEW PORTFOLIO
    base_weights = base_w.T*0               # ONLY HAVE THIS LINE OF CODE WHEN YOU ARE CONSTRUCTING THE PORTFOLIO FROM SCRATCH 
    
    famafrenchreturns()
    to__cal_stock_betas()
    to_cal_stock_price(start,end,price_monthly_data)
    Transaction_Costs()
    optimization()
    others()
    portfolio_betas()
    opt_portf_weights
    global port_betas
    opt_portf_weights

def out_of_sampless(cccc,dddd,new_monthly_data,indexgspc):
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = cccc
    o1_end_d   = dddd
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    oos1_spy_d=extract_spy_data(indexgspc,cccc,dddd)
    # oos1_spy_d = pd.DataFrame(yf.download('^GSPC',start=o1_start_d,end=o1_end_d,interval='1mo')['Adj Close'].pct_change())
    # oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
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

def out_of_sample(new_monthly_data,indexgspc):
    global oos1_daily_data
    global oos1_spy_d
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = os_start
    o1_end_d   = os_end
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    # oos1_spy_d = pd.DataFrame(yf.download('^GSPC',start=o1_start_d,end=o1_end_d,interval='1mo')['Adj Close'].pct_change())
    # oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
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

def out_of_sample(new_monthly_data,indexgspc):
    global oos1_daily_data,oos1_new_returns
    global oos1_new_performance
    global o1_end_d
    global o1_start_d
    o1_start_d = os_start
    o1_end_d   = os_end
    oos1_daily_data = extract_stock_data(new_monthly_data,opt_portf_weights.index.tolist(),start=o1_start_d,end=o1_end_d)
    # oos1_daily_data = oos1_daily_data['Adj Close'].pct_change().dropna()
    oos1_daily_data = oos1_daily_data.tz_localize(None)
    # oos1_spy_d = pd.DataFrame(yf.download('^GSPC',start=o1_start_d,end=o1_end_d,interval='1mo')['Adj Close'].pct_change())
    # oos1_spy_d = oos1_spy_d.drop(oos1_spy_d.index[0]).tz_localize(None)
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

def new_mod_out_of_sample1(hsahs,hsahs2,new_monthly_data,indexgspc):
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

def mod_out_of_sample1(new_monthly_data,indexgspc):
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

def mod_out_of_sample(new_monthly_data,indexgspc):
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

def run_with_backtest(nyears,new_monthly_data,indexgspc,price_monthly_data):
    
    global n_years
    n_years=nyears
    current_date()
    simulator(1,0,0,n_year_before,n_year_after,1000000,50,new_monthly_data,indexgspc,price_monthly_data) 
    out_of_sample(new_monthly_data,indexgspc)
  
    return oos1_new_performance
    
    
def current_date():
    global today
    global os_start
    global os_end
    global n_year_before
    global n_year_after
    from datetime import datetime, timedelta
    today = datetime.today()
    one_year_before = today - timedelta(days=365)
    os_start = today - timedelta(days=365)
    two_months_before = os_start - timedelta(days=2*30)
    os_start = two_months_before.replace(day=1)
    one_month_before = today - timedelta(days=30)
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

def new_date_calculation():
    from datetime import datetime, timedelta
    from datetime import date
    today = datetime.now()
    global out_of_sample_year_start
    global out_of_sample_year_end
    out_of_sample_year_start={}
    out_of_sample_year_end={}
    for year in range(os_years):
        out_of_sample_year_start[(year+1)] = today - timedelta(days=(365 * (os_years - year)))
        two_months_before = out_of_sample_year_start[(year+1)] - timedelta(days=2 * 30)
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
        in_of_sample_year_start[(year+1)] = today - timedelta(days=(365 * ((in_years+os_years) - year)))
        two_months_before = in_of_sample_year_start[(year+1)] - timedelta(days=2 * 30)
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
        inner_in_of_sample_year_start[(year+1)] = today - timedelta(days=(365 * (in_years+os_years - year)))
        two_months_before = inner_in_of_sample_year_start[(year+1)] - timedelta(days=2 * 30)
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
    return inner_in_of_sample_year_start

def new_run_with_backtest_rebalance(inyears,outyears,betaA,betaB,betaC,universee,new_monthly_data,indexgspc,price_monthly_data):
    
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
    inner_n_year_before_cal=new_date_calculation()
    global n_year_before
    global n_year_after
    n_year_before=in_of_sample_year_start[1]
    n_year_after=in_of_sample_year_end[in_years]
    simulator(betaA,betaB,betaC,n_year_before,n_year_after,1000000,50,universee,new_monthly_data,indexgspc,price_monthly_data)
    global checklist
    checklist=[]
    nchecklist=[]
    tostorelist=[]
    noos1_new_performance=pd.DataFrame()
    for k in range(os_years): 
        global os_start
        global os_end
        global oos1_new_performances
        oos1_new_performances={}
        global init
        os_start=out_of_sample_year_start[1+k]
        os_end=out_of_sample_year_end[1+k]
        out_of_sample(new_monthly_data,indexgspc)
        checking=out_of_sample(new_monthly_data,indexgspc)
        tostorelist.append(checking)
        # mod_out_of_sample(new_monthly_data,indexgspc)
        
        checklist.append(oos1_new_performance)
        nchecklist.append(oos1_new_performance)
        if k == 0:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1]
            
            # multiplier=oos1_new_performance['Optimized Portfolio'][-1]
        else:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1] * performances[k]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1] * spy_performances[k]
            
            # oos1_new_performance['Optimized Portfolio']=oos1_new_performance['Optimized Portfolio']*multiplier
            # noos1_new_performance=pd.concat([noos1_new_performance, oos1_new_performance], ignore_index=False)
            # multiplier=noos1_new_performance['Optimized Portfolio'][-1]
        newbudget=1000000*oos1_new_performance['Optimized Portfolio'][-1]
        inner_n_year_before=inner_n_year_before_cal[k+2]
        inner_n_year_after=out_of_sample_year_end[1+k]
        simulator(betaA,betaB,betaC,inner_n_year_before,inner_n_year_after,newbudget,50,universee,new_monthly_data,indexgspc,price_monthly_data)
      
    checklist=extract_performance(checklist)
    noos1_new_performance=pd.concat(checklist, ignore_index=False)
    for kk in range(os_years): 
        placeholder=noos1_new_performance.index[0]
        # performances[k + 1] = oos1_new_performance.loc[placeholder,"SP_500"]
        # performances[k + 1] = oos1_new_performance.loc[placeholder,"Optimized Portfolio"]
        placeholder=placeholder.replace(year=placeholder.year+(kk+1))
        if placeholder in noos1_new_performance.index:
            new_spy_performances[kk + 1] = noos1_new_performance.loc[placeholder,"SP_500"]
            new_performances[kk + 1] = noos1_new_performance.loc[placeholder,"Optimized Portfolio"]
    
    new_spy_performances[os_years] = noos1_new_performance.iloc[-1].loc["SP_500"]
    new_performances[os_years] = noos1_new_performance.iloc[-1].loc["Optimized Portfolio"]
    return noos1_new_performance 
    
def yearly_index(averaged_dff,indexname):
    nddew_spy_performances={}
    for kk in range(5): 
        pplaceholder=averaged_dff.index[0]
        pplaceholder=pplaceholder.replace(year=pplaceholder.year+(kk+1))
        if pplaceholder in averaged_dff.index:
            nddew_spy_performances[kk + 1] = averaged_dff.loc[pplaceholder,indexname]
    nddew_spy_performances[kk + 1] = averaged_dff.loc[averaged_dff.index[-1],indexname]
    return nddew_spy_performances      
            
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
            
def new_run_with_backtest(inyears,outyears,betaA,betaB,betaC,universee,new_monthly_data,indexgspc,price_monthly_data):
    
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
    
    simulator(betaA,betaB,betaC,n_year_before,n_year_after,1000000,50,universee,new_monthly_data,indexgspc,price_monthly_data)
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
        out_of_sample(new_monthly_data,indexgspc)
        # mod_out_of_sample(new_monthly_data,indexgspc)
        
        checklist.append(oos1_new_performance)
        if k == 0:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1]
        else:
            performances[k + 1] = oos1_new_performance["Optimized Portfolio"].iloc[-1] * performances[k]
            spy_performances[k + 1] = oos1_new_performance["SP_500"].iloc[-1] * spy_performances[k]
    mod_out_of_sample1(new_monthly_data,indexgspc)
    for kk in range(os_years): 
        placeholder=oos1_new_performance.index[0]
        # performances[k + 1] = oos1_new_performance.loc[placeholder,"SP_500"]
        # performances[k + 1] = oos1_new_performance.loc[placeholder,"Optimized Portfolio"]
        placeholder=placeholder.replace(year=placeholder.year+(kk+1))
        if placeholder in oos1_new_performance.index:
            new_spy_performances[kk + 1] = oos1_new_performance.loc[placeholder,"SP_500"]
            new_performances[kk + 1] = oos1_new_performance.loc[placeholder,"Optimized Portfolio"]
    
    new_spy_performances[os_years] = oos1_new_performance.iloc[-1].loc["SP_500"]
    new_performances[os_years] = oos1_new_performance.iloc[-1].loc["Optimized Portfolio"]
    return oos1_new_performance

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
        
def calculate_sharpe_ratio(portfolio_cumulative_df, risk_free_rate_df, column_name):
    portfolio_monthly_returns = portfolio_cumulative_df[column_name].pct_change().dropna()
    aligned_risk_free_rate = risk_free_rate_df.loc[portfolio_monthly_returns.index, 'RF']
    excess_returns = portfolio_monthly_returns - aligned_risk_free_rate
    avg_excess_return = excess_returns.mean()
    std_dev_return = portfolio_monthly_returns.std()
    sharpe_ratio = avg_excess_return / std_dev_return *3.3974184469680715

    return sharpe_ratio


def final_visual1():

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(oos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))  # Varying from light to dark blue
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(oos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue,linestyle='--')  # Use the corresponding blue shade
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    

def final_visual():
    fig, ax = plt.subplots(figsize=(12, 8))
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
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for every 1 dollar invested')
    ax.legend()
    plt.show()
    return averaged_df


def sp_final_visual(oos1_list2):
    oos1_list=oos1_list2.copy()
    # fig, ax = plt.subplots(figsize=(12, 8))
    # for i, df in enumerate(oos1_list):
    #     ax.plot(df['Optimized Portfolio'])
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



def final_visuala(ddfs):
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, df in enumerate(ddfs):
        ax.plot(df['Optimized Portfolio'],label='reinforcement performance',color='blue')
    ax.plot(ddfs[-1]['SP_500'], label='SP_500', linestyle='--',  marker='o',color='brown')
    last_df_index = ddfs[-1].index
    concatenated_df = pd.concat(ddfs, axis=1)
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='expectation', marker='o', color='black')
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for every 1 dollar invested')
    ax.legend()
    plt.show()
    return averaged_df



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



def final_visual1():

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(oos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))  # Varying from light to dark blue
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(oos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blues,linestyle='--')  # Use the corresponding blue shade
    
    # Plot the SP_500 line
    # ax.plot(oos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    last_df_index = oos1_list[-1].index
    concatenated_df = pd.concat(oos1_list, axis=1)
    
    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    return averaged_df


def final_visual2(hiii,oos1_listt):
    fig, ax = plt.subplots(figsize=(12, 8))
#     for i, df in enumerate(oos1_list):
#         ax.plot(df['Optimized Portfolio'], label=f'optimized_{i + 1}')
    ax.plot(oos1_listt[-1]['SP_500'], label=hiii, marker='o', color='darkorange')
    last_df_index = oos1_listt[-1].index
    concatenated_df = pd.concat(oos1_listt, axis=1)
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



def Rfinal_visual2(hiii):
    fig, ax = plt.subplots(figsize=(12, 8))
#     for i, df in enumerate(oos1_list):
#         ax.plot(df['Optimized Portfolio'], label=f'optimized_{i + 1}')
    ax.plot(oos1_list[-1]['SP_500'], label=hiii, marker='o', color='darkorange')
    ax.plot(storesp['SP_500'], label='SP_500', marker='o', color='green')
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
    ax.set_title('Optimized Portfolio Comparison with SP_500, Russell 2000 and Average for every 1 dollar invested')
    ax.legend()
    plt.show()



def final_visual1():

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(oos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))  # Varying from light to dark blue
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(oos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue,linestyle='--',label=f'{i}')  # Use the corresponding blue shade
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    

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

def calculate_yearly_returns_from_start(df):
    df.index = pd.to_datetime(df.index)
    start_date = df.index[0] 
    start_month = start_date.month
    start_year = start_date.year

    yearly_returns = {}
    for year_offset in range(1, df.index[-1].year - start_year + 1):
        comparison_date = pd.Timestamp(start_year + year_offset, start_month, 1)
        if comparison_date in df.index:
            start_value = df.iloc[0, 1]  # Value at the start (first month)
            comparison_value = df.loc[comparison_date, df.columns[1]]
            yearly_return = (comparison_value / start_value) - 1
            yearly_returns[comparison_date.year] = yearly_return
        else: 
            start_value = df.iloc[0, 1]
            comparison_date=df.index[-1]
            comparison_value = df.loc[comparison_date, df.columns[1]]
            yearly_return = (comparison_value / start_value) - 1
            yearly_returns[comparison_date.year] = yearly_return
            

    return yearly_returns

def calculate_yearly_returns_from_start2(df):
    df.index = pd.to_datetime(df.index)
    start_date = df.index[0] 
    start_month = start_date.month
    start_year = start_date.year

    yearly_returns = {}
    for year_offset in range(1, df.index[-1].year - start_year + 1):
        comparison_date = pd.Timestamp(start_year + year_offset, start_month, 1)
        if comparison_date in df.index:
            start_value = df.iloc[0, 0]  # Value at the start (first month)
            comparison_value = df.loc[comparison_date, df.columns[0]]
            yearly_return = (comparison_value / start_value) - 1
            yearly_returns[comparison_date.year] = yearly_return
        else: 
            start_value = df.iloc[0, 0]
            comparison_date=df.index[-1]
            comparison_value = df.loc[comparison_date, df.columns[0]]
            yearly_return = (comparison_value / start_value) - 1
            yearly_returns[comparison_date.year] = yearly_return

    return yearly_returns


def new_calculate_yearly_returns(df):
    yearly_returns = {}
    start_index = df.index[0]  
    end_index = df.index[-1] 
    current_start = start_index
    year_counter = 1

    while current_start < end_index:
        next_year_end = current_start + pd.DateOffset(months=12)
        if next_year_end > end_index:
            next_year_end = end_index
        if next_year_end in df.index:
            start_value = df.loc[current_start, 'Optimized Portfolio']
            end_value = df.loc[next_year_end, 'Optimized Portfolio']
            yearly_returns[year_counter] = (end_value / start_value) - 1
            year_counter += 1
        current_start = current_start + pd.DateOffset(months=12)
        
    return yearly_returns

def new_calculate_yearly_returns2(df):
    yearly_returns = {}
    start_index = df.index[0]  
    end_index = df.index[-1] 
    current_start = start_index
    year_counter = 1

    while current_start < end_index:
        next_year_end = current_start + pd.DateOffset(months=12)
        if next_year_end > end_index:
            next_year_end = end_index
        if next_year_end in df.index:
            start_value = df.loc[current_start, 'SP_500']
            end_value = df.loc[next_year_end, 'SP_500']
            yearly_returns[year_counter] = (end_value / start_value) - 1
            year_counter += 1
        current_start = current_start + pd.DateOffset(months=12)
        
    return yearly_returns

def new_get_all_yearly_returns(listof):
    yearly_data = {}

    for i, df in enumerate(listof):
        df_yearly_returns = new_calculate_yearly_returns(df)
        
        for year, return_value in df_yearly_returns.items():
            if year not in yearly_data:
                yearly_data[year] = {}
            yearly_data[year][f'df_{i + 1}'] = return_value  # Store return with df number as key

    return yearly_data
def new_calculate_percentiles(yearly_data):
    percentiles_data = {}

    for year, year_returns in yearly_data.items():
        returns = list(year_returns.values())
        
        percentile_99 = np.percentile(returns, 99)
        percentile_1 = np.percentile(returns, 1)
        median = np.median(returns)

        percentiles_data[year] = {
            '99th Percentile': percentile_99,
            'Median': median,
            '1st Percentile': percentile_1
        }

    return percentiles_data

def monte_carlo_simulation(n_simulations,mbetaA,mbetaB,mbetaC,type,inn,outt):
    results = []
    yearly_returns=[]
    for i in range(n_simulations):
        if type == 'rebalance':
            oos1_new_performance=new_run_with_backtest_rebalance(inn,outt,mbetaA,mbetaB,mbetaC)
        else:
            oos1_new_performance=new_run_with_backtest(inn,outt,mbetaA,mbetaB,mbetaC)
        globals()[f'x{i}_df']=oos1_new_performance.copy()
        globals()[f'y{i}_df']=new_performances.copy()
        results.append(globals()[f'x{i}_df'])
        yearly_returns.append(globals()[f'y{i}_df'])
        # results.append(oos1_new_performance.deepcopy())
        # yearly_returns.append(new_performances.__deepcopy__copy())
        # results[f'os_df{i}'] = oos1_new_performance.copy()
        # yearly_returns[f'return_df{i}'] = new_performances.copy()
        # results.append(oos1_new_performance)
        # yearly_returns.append(new_performances)
    
    sums = {key: 0 for key in yearly_returns[0]}
    for d in yearly_returns:
        for key, value in d.items():
            sums[key] += value
    num_dicts = len(yearly_returns)
    averages = {key: sums[key] / num_dicts for key in sums}
    return results,yearly_returns,averages
def monte_carlo_simulation(n_simulations,mbetaA,mbetaB,mbetaC,type,inn,outt,placemonthly,spymonthly,pprice_monthly_data,universee):
    results = []
    yearly_returns=[]
    new_monthly=placemonthly.copy()
    new_monthly_data=placemonthly.copy()
    indexgspc=spymonthly.copy()
    indexgspc=spymonthly.copy()
    price_monthly_data=pprice_monthly_data.copy()
    for i in range(n_simulations):
        if type == 'rebalance':
            oos1_new_performance=new_run_with_backtest_rebalance(inn,outt,mbetaA,mbetaB,mbetaC,universee,new_monthly_data,indexgspc,price_monthly_data)
        else:
            oos1_new_performance=new_run_with_backtest(inn,outt,mbetaA,mbetaB,mbetaC,universee,new_monthly_data,indexgspc,price_monthly_data)
        globals()[f'x{i}_df']=oos1_new_performance.copy()
        globals()[f'y{i}_df']=new_performances.copy()
        results.append(globals()[f'x{i}_df'])
        yearly_returns.append(globals()[f'y{i}_df'])
        # results.append(oos1_new_performance.deepcopy())
        # yearly_returns.append(new_performances.__deepcopy__copy())
        # results[f'os_df{i}'] = oos1_new_performance.copy()
        # yearly_returns[f'return_df{i}'] = new_performances.copy()
        # results.append(oos1_new_performance)
        # yearly_returns.append(new_performances)
    
    sums = {key: 0 for key in yearly_returns[0]}
    for d in yearly_returns:
        for key, value in d.items():
            sums[key] += value
    num_dicts = len(yearly_returns)
    averages = {key: sums[key] / num_dicts for key in sums}
    return results,yearly_returns,averages

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



def final_visual(hiii,oos1_listt):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(oos1_listt)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))  # Varying from light to dark blue
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(oos1_listt, blues)):
        ax.plot(df['Optimized Portfolio'], color='steelblue')  # Use the corresponding blue shade
    
    # Plot the SP_500 line
    ax.plot(oos1_listt[-1]['SP_500'], label=hiii, marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    last_df_index = oos1_listt[-1].index
    concatenated_df = pd.concat(oos1_listt, axis=1)
    
    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    return averaged_df



def Rfinal_visual(hiii,roos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(roos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color='steelblue',linestyle='--')  # Use the corresponding blue shade
    
    # Plot the SP_500 line
    ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='darkorange')
    ax.plot(storesp['SP_500'], label='SP_500', marker='o', color='green')
    
    # Concatenate all dataframes for averaging
    last_df_index = roos1_list[-1].index
    concatenated_df = pd.concat(roos1_list, axis=1)
    
    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500, Russell 2000 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    return averaged_df



def cfinal_visual(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # Plot each optimized portfolio with varying shades of blue
    for i, (df, violet) in enumerate(zip(roos1_list, violets)):
        ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    for i, (df, blue) in enumerate(zip(doos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='brown')
    ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation1', marker='o', color='green')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    return aaveraged_df,averaged_df



def ffinal_visual(hiii,listolist):
    fig, ax = plt.subplots(figsize=(12, 8))
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for doos1_list in listolist:
        j=j+1
        num_lines = len(doos1_list) 
        if j==1:
            xx = cm.Purples(np.linspace(0.2, 1, num_lines))
        elif j==2:
            xx = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        elif j==3:
            xx=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        elif j==4:
            xx=cm.Greys(np.linspace(0.3, 0.8, num_lines))
        else:
            xx=cm.RdPu(np.linspace(0.3, 0.8, num_lines))
         
        for i, (df, xz) in enumerate(zip(doos1_list, xx)):
            ax.plot(df['Optimized Portfolio'], color=xz) 
     
    for i, (df, orange) in enumerate(zip(listolist, orange)):
        ax.plot(listolist[i][-1]['SP_500'], label=hiii[i], marker='o', color=orange)
        # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    shades_of_black = [ "#3A3A3A",  "#4B4B4B", "#5E5E5E",  "#707070","#585858", "#6A6A6A", "#7D7D7D",  "#8F8F8F", "#A0A0A0",  "#B3B3B3", "#141414", "#1A1A1A", "#0D0D0D", ]

    z=0
    aa=[]
    for roos1_list in listolist:
        z=z+1
        llast_df_index = roos1_list[-1].index
        cconcatenated_df = pd.concat(roos1_list, axis=1)
    
        aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
        aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
        aaveraged_df = pd.DataFrame({
            hiii[z-1]: aaveraged_df_A,
            'Optimized Portfolio': aaveraged_df_B
        })

        ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
        aa.append(aaveraged_df)
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison and its Average along with {hiii} indices')
    ax.legend()
    
    # Show the plot
    plt.show()

    
    return aa



def ffinal_visual1(hiii,listolist):
    fig, ax = plt.subplots(figsize=(12, 8))
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for i in listolist:
        j=j+1
        num_lines = len(i) 
        if j==1:
            violets = cm.Purples(np.linspace(0.2, 1, num_lines))
        if j==2:
            blues = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        if j==3:
            indigo=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        if j==4:
            grays=cm.Greys(np.linspace(0.3, 0.8, num_lines))
         
        # # Plot each optimized portfolio with varying shades of blue
        # for i, (df, violet) in enumerate(zip(roos1_list, violets)):
        #     ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
        # for i, (df, blue) in enumerate(zip(doos1_list, blues)):
        #     ax.plot(df['Optimized Portfolio'], color=blue)
     
    for i, (df, orange) in enumerate(zip(listolist, orange)):
        ax.plot(listolist[i][-1]['SP_500'], label=hiii[i], marker='o', color=orange)
        # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    shades_of_black = [ "#3A3A3A",  "#4B4B4B", "#5E5E5E",  "#707070","#585858", "#6A6A6A", "#7D7D7D",  "#8F8F8F", "#A0A0A0",  "#B3B3B3", "#141414", "#1A1A1A", "#0D0D0D", ]

    z=0
    for roos1_list in listolist:
        z=z+1
        llast_df_index = roos1_list[-1].index
        cconcatenated_df = pd.concat(roos1_list, axis=1)
    
        aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
        aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
        aaveraged_df = pd.DataFrame({
            hiii[z-1]: aaveraged_df_A,
            'Optimized Portfolio': aaveraged_df_B
        })

        ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Average Optimized Portfolio  & {hiii} indices')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def ffinal_visual2(hiii,listolist):
    fig, ax = plt.subplots(figsize=(12, 8))
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for doos1_list in listolist:
        j=j+1
        num_lines = len(doos1_list) 
        if j==1:
            xx = cm.Purples(np.linspace(0.2, 1, num_lines))
        elif j==2:
            xx = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        elif j==3:
            xx=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        elif j==4:
            xx=cm.Greys(np.linspace(0.3, 0.8, num_lines))
        else:
            xx=cm.RdPu(np.linspace(0.3, 0.8, num_lines))
         
        # for i, (df, xz) in enumerate(zip(doos1_list, xx)):
            # ax.plot(df['Optimized Portfolio'], color=xz) 
     
    for i, (df, orange) in enumerate(zip(listolist, orange)):
        ax.plot(listolist[i][-1]['SP_500'], label=hiii[i], marker='o', color=orange)
        # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    # shades_of_black = ['black',"#343434", "#36454F",  "#353839",  "#555D50",  "#141414", "#2C2A29","#1C1C1C",  "#1A1110", "#2E1C18",  "#0C0C0C", "#3B3C36",  "#292D3D", "#4A4A48", "#4F4A4A","#2E2A47"]

    # z=0
    # aa=[]
    # for roos1_list in listolist:
    #     z=z+1
    #     llast_df_index = roos1_list[-1].index
    #     cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    #     aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    #     aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    #     aaveraged_df = pd.DataFrame({
    #         hiii[z-1]: aaveraged_df_A,
    #         'Optimized Portfolio': aaveraged_df_B
    #     })

    #     ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
    #     aa.append(aaveraged_df)
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'{hiii} market indices')
    ax.legend()
    
    # Show the plot
    plt.show()

    
    



def ffinal_visual3(hiii,listolist):
    fig, ax = plt.subplots(figsize=(12, 8))
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for doos1_list in listolist:
        j=j+1
        num_lines = len(doos1_list) 
        if j==1:
            xx = cm.Purples(np.linspace(0.2, 1, num_lines))
        elif j==2:
            xx = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        elif j==3:
            xx=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        elif j==4:
            xx=cm.RdPu(np.linspace(0.3, 0.8, num_lines))
            
        else:
            xx=cm.Greys(np.linspace(0.3, 0.8, num_lines))
         
        # for i, (df, xz) in enumerate(zip(doos1_list, xx)):
            # ax.plot(df['Optimized Portfolio'], color=xz) 
     
    # for i, (df, orange) in enumerate(zip(listolist, orange)):
    #     ax.plot(listolist[i][-1]['SP_500'], label=listolist[i][-1].columns[1]+' '+hiii[i], marker='o', color=orange)
    #     # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    shades_of_black = [ "#3A3A3A",  "#4B4B4B", "#5E5E5E",  "#707070","#585858", "#6A6A6A", "#7D7D7D",  "#8F8F8F", "#A0A0A0",  "#B3B3B3", "#141414", "#1A1A1A", "#0D0D0D", ]

    z=0
    aa=[]
    for roos1_list in listolist:
        z=z+1
        llast_df_index = roos1_list[-1].index
        cconcatenated_df = pd.concat(roos1_list, axis=1)
    
        aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
        aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
        aaveraged_df = pd.DataFrame({
            hiii[z-1]: aaveraged_df_A,
            'Optimized Portfolio': aaveraged_df_B
        })

        ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
        aa.append(aaveraged_df)
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Average of {hiii} Optimized Portfolio')
    ax.legend()
    
    # Show the plot
    plt.show()

    
    



def ffinal_visual4(hiii,listolist):
    fig, ax = plt.subplots(figsize=(12, 8))
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for doos1_list in listolist:
        j=j+1
        num_lines = len(doos1_list) 
        if j==1:
            xx = cm.Purples(np.linspace(0.2, 1, num_lines))
        elif j==2:
            xx = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        elif j==3:
            xx=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        elif j==4:
            xx=cm.RdPu(np.linspace(0.3, 0.8, num_lines))
            
        else:
            xx=cm.Greys(np.linspace(0.3, 0.8, num_lines))
         
        for i, (df, xz) in enumerate(zip(doos1_list, xx)):
            ax.plot(df['Optimized Portfolio'], color=xz) 
     
    # for i, (df, orange) in enumerate(zip(listolist, orange)):
    #     ax.plot(listolist[i][-1]['SP_500'], label=listolist[i][-1].columns[1]+' '+hiii[i], marker='o', color=orange)
    #     # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    # shades_of_black = ["#343434", "#36454F",  "#353839",  "#555D50",  "#141414", "#2C2A29","#1C1C1C",  "#1A1110", "#2E1C18",  "#0C0C0C", "#3B3C36",  "#292D3D", "#4A4A48", "#4F4A4A","#2E2A47"]

    # z=0
    # aa=[]
    # for roos1_list in listolist:
    #     z=z+1
    #     llast_df_index = roos1_list[-1].index
    #     cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    #     aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    #     aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    #     aaveraged_df = pd.DataFrame({
    #         hiii[z-1]: aaveraged_df_A,
    #         'Optimized Portfolio': aaveraged_df_B
    #     })

    #     ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
    #     aa.append(aaveraged_df)
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized {hiii} Portfolio')
    ax.legend()
    
    # Show the plot
    plt.show()

    
    


def ffinal_visual5(hiii,listolist):
    
    dnum_lines = len(listolist)    
    orange = cm.Oranges(np.linspace(0.2, 1, dnum_lines))
    j=0
    for doos1_list in listolist:
        fig, ax = plt.subplots(figsize=(12, 8))
        j=j+1
        num_lines = len(doos1_list) 
        if j==1:
            xx = cm.Purples(np.linspace(0.2, 1, num_lines))
        elif j==2:
            xx = cm.Blues(np.linspace(0.3, 0.8, num_lines))
        elif j==3:
            xx=cm.BuPu(np.linspace(0.3, 0.8, num_lines))
        elif j==4:
            xx=cm.RdPu(np.linspace(0.3, 0.8, num_lines))
            
        else:
            xx=cm.Greys(np.linspace(0.3, 0.8, num_lines))
         
        for i, (df, xz) in enumerate(zip(doos1_list, xx)):
            ax.plot(df['Optimized Portfolio'], color=xz)
        ax.set_xlabel('Months')
        ax.set_ylabel('ROI')
        ax.set_title(f'Optimized Portfolios of {hiii[j-1]} for Every 1 Dollar Invested')
        ax.legend()
        plt.show() 
     
    # for i, (df, orange) in enumerate(zip(listolist, orange)):
    #     ax.plot(listolist[i][-1]['SP_500'], label=listolist[i][-1].columns[1]+' '+hiii[i], marker='o', color=orange)
    #     # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    # shades_of_black = ["#343434", "#36454F",  "#353839",  "#555D50",  "#141414", "#2C2A29","#1C1C1C",  "#1A1110", "#2E1C18",  "#0C0C0C", "#3B3C36",  "#292D3D", "#4A4A48", "#4F4A4A","#2E2A47"]

    # z=0
    # aa=[]
    # for roos1_list in listolist:
    #     z=z+1
    #     llast_df_index = roos1_list[-1].index
    #     cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    #     aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    #     aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    #     aaveraged_df = pd.DataFrame({
    #         hiii[z-1]: aaveraged_df_A,
    #         'Optimized Portfolio': aaveraged_df_B
    #     })

    #     ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label=f'Expectation {hiii[z-1]}', marker='o', color=shades_of_black[z])
    #     aa.append(aaveraged_df)
    
    # Set the plot labels and title
    

    
    


def cfinal_visual1(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # # Plot each optimized portfolio with varying shades of blue
    # for i, (df, violet) in enumerate(zip(roos1_list, violets)):
    #     ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    # for i, (df, blue) in enumerate(zip(doos1_list, blues)):
    #     ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='brown')
    ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation', marker='o', color='green')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def cfinal_visual1a(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # # Plot each optimized portfolio with varying shades of blue
    # for i, (df, violet) in enumerate(zip(roos1_list, violets)):
    #     ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    # for i, (df, blue) in enumerate(zip(doos1_list, blues)):
    #     ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    # ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='brown')
    # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='o', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation', marker='o', color='green')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='o', color='black')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def cfinal_visual2(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # Plot each optimized portfolio with varying shades of blue
    for i, (df, violet) in enumerate(zip(roos1_list, violets)):
        ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    for i, (df, blue) in enumerate(zip(doos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    # ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='yellow')
    # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='D', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    # ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='D', color='brown')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def cfinal_visual3(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # Plot each optimized portfolio with varying shades of blue
    for i, (df, violet) in enumerate(zip(roos1_list, violets)):
        ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    # for i, (df, blue) in enumerate(zip(doos1_list, blues)):
    #     ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    # ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='yellow')
    # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='D', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    # ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='D', color='brown')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def cfinal_visual4(hiii,roos1_list,doos1_list):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(roos1_list)  # Number of portfolios to plot
    violets = cm.Purples(np.linspace(0.3, 0.8, num_lines))
    
    
    nnum_lines = len(doos1_list)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, nnum_lines))


    # Plot each optimized portfolio with varying shades of blue
    # for i, (df, violet) in enumerate(zip(roos1_list, violets)):
    #     ax.plot(df['Optimized Portfolio'], color=violet)  # Use the corresponding blue shade
    
    for i, (df, blue) in enumerate(zip(doos1_list, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue) 

    # Plot the SP_500 line
    # ax.plot(roos1_list[-1]['SP_500'], label=hiii, marker='o', color='yellow')
    # ax.plot(doos1_list[-1]['SP_500'], label='SP_500', marker='D', color='darkorange')
    
    # Concatenate all dataframes for averaging
    llast_df_index = roos1_list[-1].index
    cconcatenated_df = pd.concat(roos1_list, axis=1)
    
    aaveraged_df_A = cconcatenated_df.filter(like='SP_500').mean(axis=1)
    aaveraged_df_B = cconcatenated_df.filter(like='Optimized Portfolio').mean(axis=1)

    # Create a DataFrame for the averaged values
    aaveraged_df = pd.DataFrame({
        hiii: aaveraged_df_A,
        'Optimized Portfolio': aaveraged_df_B
    })

    # ax.plot(aaveraged_df.index, aaveraged_df['Optimized Portfolio'], label='Expectation', marker='o', color='black')

    last_df_index = doos1_list[-1].index
    concatenated_df = pd.concat(doos1_list, axis=1)

    # Calculate the averages for SP_500 and Optimized Portfolio
    averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # Create a DataFrame for the averaged values
    averaged_df = pd.DataFrame({
        'SP_500': averaged_df_A,
        'Optimized Portfolio': averaged_df_B
    })
    
    # Plot the averaged 'Optimized Portfolio' line in black
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Expectation_SP', marker='D', color='brown')
    
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title(f'Optimized Portfolio Comparison with SP_500, {hiii} and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
    # return aaveraged_df,averaged_df



def finale_visual(diction,word):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Iterate over the dictionary (key as label, value as DataFrame)
    for label, df in diction.items():
        if word not in label:
            ax.plot(df['Optimized Portfolio'], label=f'{label}_optimized')
    
    # Plot the SP_500 from the last DataFrame (assuming it exists in the last DataFrame)
    # last_df = list(diction.values())[-1]
    # ax.plot(last_df['SP_500'], label='SP_500', linestyle='--', marker='o', color='red')
    
    # # Concatenate all DataFrames (along the columns)
    # concatenated_df = pd.concat(diction.values(), axis=1)
    
    # # Average the columns related to 'SP_500' and 'Optimized Portfolio'
    # averaged_df_A = concatenated_df.filter(like='SP_500').mean(axis=1)
    # averaged_df_B = concatenated_df.filter(like='Optimized Portfolio').mean(axis=1)
    
    # # Create a DataFrame for the averaged values
    # averaged_df = pd.DataFrame({
    #     'SP_500': averaged_df_A,
    #     # 'Optimized Portfolio': averaged_df_B
    # })
    
    # # Uncomment if you want to plot the averaged data
    # ax.plot(averaged_df.index, averaged_df['Optimized Portfolio'], label='Average optimized performance', marker='o', color='black')
    
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Various Optimized Portfolio Comparison for every 1 dollar invested')
    ax.legend()
    plt.show()

def save_df_to_existing_excel(df, filename, sheet_name, start_row=0, start_col=0, gap=0):
    
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
        if sheet_name not in writer.book.sheetnames:
            writer.book.create_sheet(sheet_name)
        df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, startcol=start_col, index=False)
        
        return start_row + len(df) + gap

def save_df_to_existing_excel(df, filename, sheet_name, start_row=0, start_col=0, gap=0):
    
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
        if sheet_name not in writer.book.sheetnames:
            writer.book.create_sheet(sheet_name)
        df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, startcol=start_col, index=False)
        
        return start_row + len(df) + gap
    


def save_df_with_combination_to_excel(df, filename, sheet_name, combination, start_row=0, start_col=0, gap=0):
    if not isinstance(combination, (list, tuple)):
        raise ValueError("Combination should be a list or tuple of values.")
    df_transposed = df.T
    df_transposed.columns = [f"Year {i+1}" for i in range(len(df_transposed.columns))]
    combined_row = list(combination) + df_transposed.iloc[0].tolist()
    combined_df = pd.DataFrame([combined_row], columns=[f"Beta {i+1}" for i in range(len(combination))] + df_transposed.columns.tolist())

    try:
        book = load_workbook(filename)
        if sheet_name in book.sheetnames:
            header = False  
        else:
            header = True
    except FileNotFoundError:
        header = True  

    with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        combined_df.to_excel(
            writer,
            sheet_name=sheet_name,
            startrow=start_row,
            startcol=start_col,
            index=False,
            header=header
        )
        return start_row + len(combined_df) + gap, 

#future price function

def get_last_future_price(symbol):
    future = yf.Ticker(symbol)
    data = future.history(period="1d")
    last_price = data['Close'].iloc[-1]
    return last_price
def random_generate_beta(l,u):
    upper_limit=u
    lower_limit=l
    random_number=round(random.uniform(lower_limit, upper_limit), 2)
    return random_number

def cumulative_returns_cal(somelist):
    final_returns = {f"df {i + 1}": df.iloc[-1, 1] for i, df in enumerate(somelist)}
    final_return_values = list(final_returns.values())
    percentile_99_value = np.percentile(final_return_values, 99)
    percentile_1_value = np.percentile(final_return_values, 1)
    index_99 = min(range(len(final_return_values)), key=lambda i: abs(final_return_values[i] - percentile_99_value))
    index_1 = min(range(len(final_return_values)), key=lambda i: abs(final_return_values[i] - percentile_1_value))
    key_99 = list(final_returns.keys())[index_99]
    key_1 = list(final_returns.keys())[index_1]
    df_99 = somelist[int(key_99.split()[1]) - 1]  
    df_1 = somelist[int(key_1.split()[1]) - 1]
    yearly_returns_99 = calculate_yearly_returns_from_start(df_99)
    yearly_returns_1 = calculate_yearly_returns_from_start(df_1)
    yearly_returns_sp = calculate_yearly_returns_from_start2(df_1)
    yearly_returns_avg = calculate_yearly_returns_from_start(avg_100)
    yearly_returns_99 = {key: value * 100 for key, value in yearly_returns_99.items()}
    yearly_returns_1 = {key: value * 100 for key, value in yearly_returns_1.items()}
    yearly_returns_sp = {key: value * 100 for key, value in yearly_returns_sp.items()}
    yearly_returns_avg = {key: value * 100 for key, value in yearly_returns_avg.items()}
    data = {
        '99 percentile': pd.Series(yearly_returns_99),
        'Average': pd.Series(yearly_returns_avg),
        '1 percentile': pd.Series(yearly_returns_1),
        'sp500': pd.Series(yearly_returns_sp)
    }
    returns_df = pd.DataFrame(data)
    returns_df.index.name = 'Year'
    returns_df.columns.name = 'Percentile'
    returns_df = returns_df.T
    newyearly_data = new_get_all_yearly_returns(somelist)
    newpercentiles_data = new_calculate_percentiles(newyearly_data)
    sp500_newyearly_data = new_calculate_yearly_returns2(somelist[0])
    final_return_df = pd.DataFrame(newpercentiles_data)
    final_return_df.loc['SP500'] = pd.Series(sp500_newyearly_data)
    final_return_df = (final_return_df * 100).round(2)
    first_panknakercentile = {key: value['1st Percentile'] for key, value in newpercentiles_data.items()}
    one_percentile_df = pd.DataFrame(list(first_panknakercentile.items()), columns=['Year', '1 percentile return in %'])
    one_percentile_df.set_index('Year',inplace=True)
    one_percentile_df=(one_percentile_df * 100).round(2)

    
    return returns_df,final_return_df,one_percentile_df
def variable_current_date():
    global today
    global os_start
    global os_end
    global n_year_before
    global n_year_after
    os_years
def visual():
      plt.style.use('ggplot')
      fig = plt.figure(figsize=(12,8), dpi=100)
      axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])   # left, bottom, width, height (range 0 to 1)
      for i in range(0,len(oos1_daily_data.columns[-2:])):
        axes.plot(oos1_new_performance.index, oos1_new_performance.iloc[:,i], linewidth=1)
      axes.set_xlabel('Date')
      axes.set_ylabel('Performance')
      axes.set_title('Out of Sample 1 - Daily Performance of $1 USD of Portfolios')
      axes.legend(oos1_daily_data.columns[-2:], bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0, fontsize='small')
      plt.savefig('oos1_daily_performance.png') 
      plt.show()




class AdaptiveBandit:
    def __init__(self, target_years=5, objective='max_return'):
        self.target_years = target_years
        self.objective = objective.lower()
        self.best_combination = np.array([1.0, 0.0, 0.0])
        self.best_return = -np.inf
        self.storage_file = f"explored_{self.objective}.csv"
        self.explored = self.load_explored_combinations()

    def load_explored_combinations(self):
        if os.path.exists(self.storage_file):
            df = pd.read_csv(self.storage_file)
            df[['c1', 'c2', 'c3', 'reward']] = df[['c1', 'c2', 'c3', 'reward']].astype(float)
            return df
        return pd.DataFrame(columns=['c1', 'c2', 'c3', 'reward'])
    
    def save_combination(self, combination, reward):
        combination = np.array(combination, dtype=float)
        reward = float(reward)
        new_entry = pd.DataFrame([{
            'c1': combination[0],
            'c2': combination[1],
            'c3': combination[2],
            'reward': reward
        }])
        self.explored = pd.concat([self.explored, new_entry], ignore_index=True)
        self.explored.to_csv(self.storage_file, index=False)

    def save_combination(self, combination, reward):
        combination = self.round_combination(combination)
        reward = float(reward)
    
        if self.check_existing_combination(combination) is not None:
            return  # Skip if already saved

        new_entry = pd.DataFrame([{
            'c1': combination[0],
            'c2': combination[1],
            'c3': combination[2],
            'reward': reward
        }])
        self.explored = pd.concat([self.explored, new_entry], ignore_index=True)
        self.explored.to_csv(self.storage_file, index=False)



    def check_existing_combination(self, combination):
        combination = self.round_combination(combination)
        match = self.explored[
            (self.explored['c1'] == combination[0]) &
            (self.explored['c2'] == combination[1]) &
            (self.explored['c3'] == combination[2])
        ]
        if not match.empty:
            return match.iloc[0]['reward']
        return None

    def round_combination(self, combination):
        return np.round(np.array(combination, dtype=float), 1)

    def evaluate_combination(self, beta_combination):
        oos1_list, oos1_list_yearly, oos1_average = monte_carlo_simulation(
            2, 1, 0, 0, 'rebalance', 3, 5, new_monthly_data, indexgspc
        )
        if self.objective == 'max_return':
            simulated_df = sp_final_visual(oos1_list)
        else:
            simulated_df = get_consistently_worst_portfolio(oos1_list, 'Optimized Portfolio')
        return simulated_df

    def reward_function(self, simulated_df):
        if self.objective in ['max_return', 'downside_protection']:
            optimized = simulated_df['Optimized Portfolio'].iloc[-1]
            benchmark = simulated_df['SP_500'].iloc[-1]
            return optimized / benchmark

        returns = simulated_df['Optimized Portfolio'].pct_change().dropna()
        if self.objective == 'sharpe':
            return returns.mean() / returns.std() if returns.std() != 0 else -np.inf
        elif self.objective == 'sortino':
            downside_std = returns[returns < 0].std()
            return returns.mean() / downside_std if downside_std != 0 else -np.inf
        else:
            raise ValueError(f"Unknown objective: {self.objective}")
        
    def explore_direction(self, base_combination):
        candidates = []
        directions = [-0.1, 0.2]
        lower_bounds = np.array([0.9, 0.0, 0.0])
        upper_bounds = np.array([2.3, 2.2, 2.2])
        found_new = False

        for i in range(3):
            for delta in directions:
                new_combination = base_combination.copy()
                new_combination[i] += delta
                new_combination = np.clip(new_combination, lower_bounds, upper_bounds)

                if self.check_existing_combination(new_combination) is not None:
                    continue  # Already explored, skip it

                new_combination = np.round(new_combination, 1)
                simulated_df = self.evaluate_combination(new_combination)
                reward = self.reward_function(simulated_df)
                self.save_combination(new_combination, reward)
                candidates.append((new_combination, reward))
                found_new = True
        return candidates, found_new
    
    def select_next_combination(self):
        candidates, found_new = self.explore_direction(self.best_combination)

        if not candidates:
            return self.best_combination, False  # No new exploration found

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate, best_reward = candidates[0]

        if best_reward > self.best_return:
            self.best_combination = best_candidate
            self.best_return = best_reward

        return self.best_combination, found_new
    
    def run_bandit(self, iterations=3, initializer='yes'):
        print(f"Running bandit optimization for objective: '{self.objective}'")

    # Base initialization
        if initializer == 'yes':
            base = np.array([1.0, 0.0, 0.0])
        else:
            if not self.explored.empty:
                best_row = self.explored.loc[self.explored['reward'].idxmax()]
                base = np.array([best_row['c1'], best_row['c2'], best_row['c3']])
            else:
                print("No previous data found. Using default base combination.")
                base = np.array([1.0, 0.0, 0.0])

    # Evaluate base combo
        reward = self.check_existing_combination(base)
        if reward is None:
            simulated_df = self.evaluate_combination(base)
            reward = self.reward_function(simulated_df)
            self.save_combination(base, reward)

        self.best_combination = base
        self.best_return = reward

        print(f"Base Combination: {self.best_combination}, Base Score: {self.best_return:.4f}")

        valid_iterations = 0
        attempt_cap = iterations * 10  # Avoid infinite loops

        while valid_iterations < iterations and attempt_cap > 0:
            new_combination, found_new = self.select_next_combination()
            attempt_cap -= 1

            if found_new:
                valid_iterations += 1
                print(f"[{valid_iterations}] New Combo: {new_combination} → Score: {self.best_return:.4f}")
            else:
                print("No new combination found. Expanding search...")

            # Optional: add random direction or noise when stuck
                random_combo = self.best_combination + np.random.uniform(-0.2, 0.2, size=3)
                random_combo = np.clip(random_combo, [0.9, 0.0, 0.0], [2.3, 2.2, 2.2])

                if self.check_existing_combination(random_combo) is None:
                    simulated_df = self.evaluate_combination(random_combo)
                    reward = self.reward_function(simulated_df)
                    self.save_combination(random_combo, reward)

                    if reward > self.best_return:
                        self.best_combination = random_combo
                        self.best_return = reward
                        valid_iterations += 1
                        print(f"[{valid_iterations}] Random Exploration: {random_combo} → Score: {self.best_return:.4f}")

        print("\nFinal Best Combination:")
        print(f"{self.best_combination} → Score: {self.best_return:.4f}")





def get_consistently_worst_portfolio(dfs, portfolio_col='portfolio'):
    """
    Returns the DataFrame whose portfolio is consistently the worst performer.

    Parameters:
        dfs (list of pd.DataFrame): Each must have a 'portfolio' and 'sp500' column.
        portfolio_col (str): The portfolio column name.

    Returns:
        pd.DataFrame: The worst performing portfolio's full DataFrame.
    """

    # Extract portfolio series and align them
    portfolio_series_list = [df[portfolio_col] for df in dfs]

    # Get the common index (intersection of all time indices)
    common_index = set(portfolio_series_list[0].index)
    for series in portfolio_series_list[1:]:
        common_index &= set(series.index)
    common_index = sorted(common_index)

    # Reindex all series to the common index
    aligned_series = [s.loc[common_index] for s in portfolio_series_list]

    # Combine into a single DataFrame and give column names as their list indices
    combined_portfolios = pd.concat(aligned_series, axis=1)
    combined_portfolios.columns = list(range(len(dfs)))  # [0, 1, 2, ...]

    # Count how often each column has the minimum value across rows
    min_indices = combined_portfolios.idxmin(axis=1)
    min_counts = min_indices.value_counts()

    # Find the column (index) that was the minimum most often
    worst_index = min_counts.idxmax()

    # Return the corresponding original DataFrame
    return dfs[worst_index]


def final_visual1(oos1_listt):

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a colormap (blue shades)
    num_lines = len(oos1_listt)  # Number of portfolios to plot
    blues = cm.Blues(np.linspace(0.2, 1, num_lines))  # Varying from light to dark blue
    
    # Plot each optimized portfolio with varying shades of blue
    for i, (df, blue) in enumerate(zip(oos1_listt, blues)):
        ax.plot(df['Optimized Portfolio'], color=blue,linestyle='--')  # Use the corresponding blue shade
    # Set the plot labels and title
    ax.set_xlabel('Months')
    ax.set_ylabel('ROI')
    ax.set_title('Optimized Portfolio Comparison with SP_500 and Average for Every 1 Dollar Invested')
    ax.legend()
    
    # Show the plot
    plt.show()
    
def get_spy2(start,end,universe,new_monthly_data,indexgspc):
    ### Get tickers + setup
    global tickers,spy
    global monthly_data
    global base_w
    if universe=='spy':
        requests.packages.urllib3.disable_warnings()
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        html_content = response.content
        # Read HTML content into pandas DataFrame
        list_of_dfs = pd.read_html(html_content)
        wikitable_sp_500 = list_of_dfs[0]
        sp500_symbols = wikitable_sp_500['Symbol']
        tickers = sp500_symbols.to_list() # Converting SP_500 tickers into list 
        # Remove some tickers as they create an error for the yfinance api
        # print('\namogus\n',tickers,'amogus\n')
        # tickers[65] = 'BRK-B'
        # tickers[81] = 'BF-B'
        try:
            tickers.remove('BF-B')
            tickers.remove('BRK-B')
        except:
            print('\n')
        try:
            tickers.remove('BRK.B')
            tickers.remove('BF.B')
        except:
            print('\n')

        ### Import the monthly data
        # global monthly_data
        # global base_w
        for a in ['XYZ', 'PSKY']:
            if a in tickers:
            
                tickers.remove(a)
        monthly_data = extract_stock_data(new_monthly_data,tickers,start=start,end=end)
        if 'GEN' in monthly_data.columns:
            monthly_data.drop(columns={'GEN'},inplace=True)
        if 'COR' in monthly_data.columns:
            monthly_data.drop(columns={'COR'},inplace=True)
        if 'FI' in monthly_data.columns:
            monthly_data.drop(columns={'FI'},inplace=True) 
        if 'KEYS' in monthly_data.columns:
            monthly_data.drop(columns={'KEYS'},inplace=True) 
        if 'MS' in monthly_data.columns:
            monthly_data.drop(columns={'MS'},inplace=True) 
        if 'AXON' in monthly_data.columns:
            monthly_data.drop(columns={'AXON'},inplace=True)
        if 'COHR' in monthly_data.columns:
            monthly_data.drop(columns={'COHR'},inplace=True) 
            # AXON
        '''
        Structure of monthly_data:
        rows: new date
        columns: various tickers drawn from the S&P 500
        '''
        base_w = {k: 1/len(monthly_data.columns) for k in monthly_data.columns}
        base_w = pd.DataFrame.from_dict(base_w, orient='index', columns=['Weight'])
        spy=extract_spy_data(indexgspc,start,end)
        print(monthly_data.index.equals(spy.index))
        if monthly_data.index.equals(spy.index)==True:
            for i,j in monthly_data.iterrows():
                monthly_data.loc[i,'SP_500']=spy.loc[i,'SP_500']
        tickers = list(monthly_data.columns[:-1]) 
        tick_index = tickers + ['SP_500']

    if universe=='russell1000':
        requests.packages.urllib3.disable_warnings()
        response = requests.get('https://en.wikipedia.org/wiki/Russell_1000_Index', verify=False)
        html_content = response.content
        # Read HTML content into pandas DataFrame
        list_of_dfs = pd.read_html(html_content)
        wikitable_sp_500 = list_of_dfs[3]
        sp500_symbols = wikitable_sp_500['Symbol']
        tickers = sp500_symbols.to_list() # Converting SP_500 tickers into list 
        # Remove some tickers as they create an error for the yfinance api
        # print('\namogus\n',tickers,'amogus\n')
        # tickers[65] = 'BRK-B'
        # tickers[81] = 'BF-B'
        try:    
            tickers.remove('BF-B')
            tickers.remove('BF-A')
            tickers.remove('BRK-B')
            tickers.remove('BRK-A')
            
        except:
            print('\n')
        try:
            tickers.remove('BRK.A')
            tickers.remove('BF.A')
            tickers.remove('BRK.B')
            tickers.remove('BF.B')
            
            
        except:
            print('\n')
 
        
        avoidlist=['BRK.B', 'XYZ', 'BF.A', 'BF.B', 'CWEN.A', 'HEI.A', 'LEN.B', 'MRP', 'UHAL.B','JBTM', 'ADRO','CSW', 'MOGA', 'XTSLA', 'CLSKW', 'AAMI', 'NAGE', 'MSFUT', 'PRSU', 'MTSR', 'FLOC', 'GEFB', 'BBNX', 'TBCH', 'CRDA', 'INR', 'MAZE', 'TEAD', 'CMDB', 'RHLD', 'INH', '--', '--','--','--','WLLBW', 'P5N994', 'RTYM5']
        for i in avoidlist:
            try:
                tickers.remove(i)
            except:
                print('\n')
        avoidlist2=['BRK', 'SQ', 'BF']
        for i in avoidlist2:
            try:
                tickers.append(i)
            except:
                print('\n')

        ### Import the monthly data
        # global monthly_data
        # global base_w
        monthly_data = extract_stock_data(new_monthly_data,tickers,start=start,end=end)
        if 'GEN' in monthly_data.columns:
            monthly_data.drop(columns={'GEN'},inplace=True)
        if 'COR' in monthly_data.columns:
            monthly_data.drop(columns={'COR'},inplace=True)
        if 'FI' in monthly_data.columns:
            monthly_data.drop(columns={'FI'},inplace=True) 
        if 'KEYS' in monthly_data.columns:
            monthly_data.drop(columns={'KEYS'},inplace=True) 
        if 'MS' in monthly_data.columns:
            monthly_data.drop(columns={'MS'},inplace=True) 
        if 'AXON' in monthly_data.columns:
            monthly_data.drop(columns={'AXON'},inplace=True)
        if 'COHR' in monthly_data.columns:
            monthly_data.drop(columns={'COHR'},inplace=True)  
            
            # AXON
        '''
        Structure of monthly_data:
        rows: new date
        columns: various tickers drawn from the S&P 500
        '''
        base_w = {k: 1/len(monthly_data.columns) for k in monthly_data.columns}
        base_w = pd.DataFrame.from_dict(base_w, orient='index', columns=['Weight'])
        spy=extract_spy_data(indexgspc,start,end)
        print(monthly_data.index.equals(spy.index))
        if monthly_data.index.equals(spy.index)==True:
            for i,j in monthly_data.iterrows():
                monthly_data.loc[i,'SP_500']=spy.loc[i,'SP_500']
        tickers = list(monthly_data.columns[:-1]) 
        tick_index = tickers + ['SP_500']
        # return list_of_dfs

    if universe=='russell2000':
        # global tickers,spy
        requests.packages.urllib3.disable_warnings()
        holdings=pd.read_csv('input_data/RTY_data_holding.csv')
        holdings_symbols = holdings['Ticker']
        tickers = holdings_symbols.to_list()
        try:    
            tickers.remove('BF-B')
            tickers.remove('BF-A')
            tickers.remove('BRK-B')
            tickers.remove('BRK-A')
            
        except:
            print('\n')
        try:
            tickers.remove('BRK.A')
            tickers.remove('BF.A')
            tickers.remove('BRK.B')
            tickers.remove('BF.B')
            
            
        except:
            print('\n')
        tickers.append('BRK')
        # tickers.append('BF')
        avoidlist=['JBTM', 'ADRO','CSW', 'MOGA', 'XTSLA', 'CLSKW', 'AAMI', 'NAGE', 'MSFUT', 'PRSU', 'MTSR', 'FLOC', 'GEFB', 'BBNX', 'TBCH', 'CRDA', 'INR', 'MAZE', 'TEAD', 'CMDB', 'RHLD', 'INH', '--', '--','--','--','WLLBW', 'P5N994', 'RTYM5']
        for i in avoidlist:
            try:
                tickers.remove(i)
            except:
                print('\n')
        monthly_data = extract_stock_data(new_monthly_data,tickers,start=start,end=end)
        if 'GEN' in monthly_data.columns:
            monthly_data.drop(columns={'GEN'},inplace=True)
        if 'COR' in monthly_data.columns:
            monthly_data.drop(columns={'COR'},inplace=True)
        if 'FI' in monthly_data.columns:
            monthly_data.drop(columns={'FI'},inplace=True) 
        if 'KEYS' in monthly_data.columns:
            monthly_data.drop(columns={'KEYS'},inplace=True) 
        if 'MS' in monthly_data.columns:
            monthly_data.drop(columns={'MS'},inplace=True) 
        if 'AXON' in monthly_data.columns:
            monthly_data.drop(columns={'AXON'},inplace=True)
        if 'COHR' in monthly_data.columns:
            monthly_data.drop(columns={'COHR'},inplace=True)
        '''
        Structure of monthly_data:
        rows: new date
        columns: various tickers drawn from the S&P 500
        '''
        base_w = {k: 1/len(monthly_data.columns) for k in monthly_data.columns}
        base_w = pd.DataFrame.from_dict(base_w, orient='index', columns=['Weight'])
        spy=extract_spy_data(indexgspc,start,end)
        print(monthly_data.index.equals(spy.index))
        if monthly_data.index.equals(spy.index)==True:
            for i,j in monthly_data.iterrows():
                monthly_data.loc[i,'SP_500']=spy.loc[i,'SP_500']
        tickers = list(monthly_data.columns[:-1]) 
        tick_index = tickers + ['SP_500']
    
def initialize_type(indexdata):
    if indexdata=='spy':
        new_data=pd.read_csv('input_data/daat.csv')
        new_data.drop(columns='PERMNO',inplace=True)
        new_data.rename(columns={'date':'Date','TICKER':'Ticker'},inplace=True)
        price_monthly_data=new_data.drop(columns='RET')
        new_monthly_data=new_data.drop(columns='PRC')
        price_monthly_data
        price_monthly_data=price_monthly_data.pivot_table(index='Date', columns='Ticker', values='PRC', aggfunc='first')
        new_monthly_data
        new_monthly_data=new_monthly_data.pivot_table(index='Date', columns='Ticker', values='RET', aggfunc='first')
        monthly_data=new_monthly_data.copy()
        index=pd.read_csv('input_data/spy_data.csv')
        indexgspc=index.copy()
        indexgspc.rename(columns={'DATE':'Date','sprtrn':'SP_500'},inplace=True)
        indexgspc.drop(columns={'vwretd','spindx'},inplace=True)
        indexgspc.set_index('Date',inplace=True)
        indexgspc.index = pd.to_datetime(indexgspc.index)
        indexgspc=indexgspc.dropna()
    if indexdata=='russell2000':
        new_data=pd.read_csv('input_data/daat.csv')
        new_data.drop(columns='PERMNO',inplace=True)
        new_data.rename(columns={'date':'Date','TICKER':'Ticker'},inplace=True)
        price_monthly_data=new_data.drop(columns='RET')
        new_monthly_data=new_data.drop(columns='PRC')
        price_monthly_data
        price_monthly_data=price_monthly_data.pivot_table(index='Date', columns='Ticker', values='PRC', aggfunc='first')
        new_monthly_data
        new_monthly_data=new_monthly_data.pivot_table(index='Date', columns='Ticker', values='RET', aggfunc='first')
        monthly_data=new_monthly_data.copy()
        index=pd.read_csv('input_data/RTY_data.csv')
        indexgspc=index.copy()
        indexgspc.rename(columns={'datadate':'Date','prccm':'price'},inplace=True)
        indexgspc['SP_500'] = indexgspc['price'].pct_change()
        indexgspc.drop(columns={'tic','gvkeyx','price'},inplace=True)
        indexgspc.set_index('Date',inplace=True)
        indexgspc.index = pd.to_datetime(indexgspc.index)
        indexgspc=indexgspc.dropna()
        indexgspc=indexgspc.iloc[:-5]
    if indexdata=='russell1000':
        new_data=pd.read_csv('input_data/daat.csv')
        new_data.drop(columns='PERMNO',inplace=True)
        new_data.rename(columns={'date':'Date','TICKER':'Ticker'},inplace=True)
        price_monthly_data=new_data.drop(columns='RET')
        new_monthly_data=new_data.drop(columns='PRC')
        price_monthly_data
        price_monthly_data=price_monthly_data.pivot_table(index='Date', columns='Ticker', values='PRC', aggfunc='first')
        new_monthly_data
        new_monthly_data=new_monthly_data.pivot_table(index='Date', columns='Ticker', values='RET', aggfunc='first')
        monthly_data=new_monthly_data.copy()
        indexgspc=pd.read_csv('input_data/RTY1000_data.csv')
        indexgspc.rename(columns={'Date ':'Date'},inplace=True)
        indexgspc.drop(columns={'High','Low','Open','Close'},inplace=True)
        indexgspc.set_index('Date',inplace=True)
        indexgspc.index = pd.to_datetime(indexgspc.index)
        indexgspc.sort_index(inplace=True)
        indexgspc = indexgspc.apply(lambda x: x.astype(str).str.replace(',', '').astype(float))
        indexgspc['SP_500'] = indexgspc['Adj'].pct_change()
        indexgspc.drop(columns={'Adj'},inplace=True)
        indexgspc=indexgspc.dropna()
        indexgspc=indexgspc.iloc[:-7]
        
        
    return new_monthly_data,monthly_data,price_monthly_data,indexgspc

def converter_cumulative(df,name):
    df2=pd.DataFrame()
    df2=df.copy()
    df2['SP_500']=df2['SP_500'].pct_change()
    df2['Optimized Portfolio']=df2['Optimized Portfolio'].pct_change()
    df2=df2.fillna(0)
    plt.plot(df2.index, df2['SP_500'], label=name)
    plt.plot(df2.index, df2['Optimized Portfolio'], label='Optimized Portfolio')
    mean1=df2['SP_500'].mean()
    mean2=df2['Optimized Portfolio'].mean()
    plt.axhline(mean1, color='black', linestyle='--', label=f'Mean {name}')
    plt.axhline(mean2, color='brown', linestyle='--', label=f'Mean Optimized {name}')
    plt.xlabel('Months')
    plt.ylabel('percentage changes')
    plt.title(f'Line Plot of {name} and Optimized Portfolio')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return df2



def correlation_of_all_returns(df1, df2, df3):
    """
    Takes 3 DataFrames, each with 2 columns:
    - First column: Benchmark Return
    - Second column: Portfolio Return
    
    Combines all six return series and returns a correlation matrix.
    """
   
    # Concatenate all return series side by side
    combined = pd.concat([df1, df2, df3], axis=1)

    # Drop any rows with missing values
    combined = combined.dropna()

    # Compute and return correlation matrix
    return combined.corr()


def mean_and_std_of_returns(df1, df2, df3):

    stats = []

    # Compute the mean and std for each benchmark and portfolio
    for i, df in enumerate([df1, df2, df3], 1):
        # Extract statistics for benchmarks and portfolios
        stats.append([df.columns[0], df.iloc[:, 0].mean(), df.iloc[:, 0].std()])
        stats.append([df.columns[1], df.iloc[:, 1].mean(), df.iloc[:, 1].std()])
    
    # Convert to DataFrame
    stats_df = pd.DataFrame(stats, columns=['Asset', 'Mean', 'Std'])
    
    return stats_df




def lowest_5_values(df,j):
    lowest_values = {}
    for column in df.columns:
        lowest_values[column] = df[column].nsmallest(j).values
    return lowest_values


def yoy_return(values):
    return [(values[i] - values[i-1]) / values[i-1] * 100 for i in range(1, len(values))]

def dict_to_list(data_dict):
    return [1] + [data_dict[k] for k in sorted(data_dict.keys())]

# oxford=pd.read_csv('Download Data.csv')
# oxford = oxford.set_index('Date')
# oxford.rename(columns={'Close':'ONTTF'},inplace=True)
# dsa=pd.DataFrame()
# dsa = oxford[['ONTTF']] 
# dsa.index = pd.to_datetime(dsa.index, format='%y-%b') 

# dsa = dsa.sort_index()
# dsa['return'] = round(dsa['ONTTF'].pct_change(),4)
# dsa['marketcap'] = (dsa['ONTTF']*963780000) g=['Oxford Nanopore Technologies PLC','BASF SE','Siemens AG','GE Aerospace','Materialise NV','Chubb','Emerson Electric Co','3M Co','Hippo Insurance','Conagra Brands Inc','Wise PLC','Heico Corp','Corning Inc','Intuitive Surgical Inc','Goodrx Holdings Inc','Bayer AG','Honeywell International Inc','DuPont de Nemours Inc','Cardinal Health Inc','Heidelberg Materials','Caterpillar Inc','Corecivic Inc','Ensign Group Inc','Life Time Group Holdings Inc','Ryanair Holdings plc','Danaher Corp','Schneider Electric SE','Plug Power Inc','Air Products and Chemicals Inc','Holcim AG']
# len(g) j=['ONTTF','BASFY','SIEGY','GE','MTLS','CB','EMR','MMM','HIPO','CAG','WIZEY','HEI','GLW','ISRG','GDRX','BAYRY','HON','DD','CAH','HDLMY','CAT','CXW','ENSG','LTH','RYAAY','DHR','SBGSY','PLUG','APD','HCMLY']

