import getFamaFrenchFactors as gff
import pandas as pd
import numpy as np, numpy.random
from sklearn.linear_model import LinearRegression
def famafrenchreturns(df,df2):
    # global ff3_monthly
    # Fama French Monthly Returns Data using getFamaFrenchFactors module
    # ff3_monthly = gff.famaFrench3Factor(frequency='d')
    # ff3_monthly.rename(columns={"date_ff_factors": 'Date'}, inplace=True)
    # ff3_monthly.set_index('Date', inplace=True)
    ff3_monthly=df2.copy()
    ff3_monthly.rename(columns={'Unnamed: 0':'Date'},inplace=True)
    ff3_monthly['Date']=pd.to_datetime(ff3_monthly['Date'].astype(str), format='%Y%m%d')
    ff3_monthly.set_index('Date',inplace=True)
    ff3_monthly.index = ff3_monthly.index.to_period('D').to_timestamp('D')
    # Keeping Only the Dates in the monthly_data
    ff3_monthly = ff3_monthly.loc[df['date']]
    return ff3_monthly

def to__cal_stock_betas(df,df3):
    # global stock_betas
    stock_betas = pd.DataFrame()
    df4=df3.copy()
    # Iterate over the tickers list
    unique_permnos = df['permno'].unique()
    dflist=[]
    for permno in unique_permnos:
        permno_data = df[df['permno'] == permno]
        y= permno_data['rtc']
        ff3_monthly=famafrenchreturns(permno_data,df4)
        
        # y = df[col]
        # Set the independent variables (Fama French 3 Factors)
        X = ff3_monthly[['Mkt-RF','SMB','HML']]
        # Fit the multiple linear regression model
        # model = LinearRegression()
        # model.fit(X, y)
        # # Store the results in the DataFrame
        # stock_betas[permno] = [model.intercept_] + list(model.coef_)
        # stock_betas = stock_betas.T
        stock_betas=compute_betas(X,y)
        stock_betas.columns = ['Intercept','Mkt-RF','SMB','HML']
        stock_betas['permno'] = permno  
        dflist.append(stock_betas)
    stacked_df = pd.concat(dflist, ignore_index=False)    
    return stacked_df

def compute_betas(df_X, df_y):
    """
    Compute the regression betas for each day using a sliding window of 30 previous days (including the current day).
    
    Parameters:
    - df_X: DataFrame with features, indexed by date
    - df_y: Series with target values, indexed by date
    
    Returns:
    - DataFrame with betas (intercept, mkt, smb, hml)
    """
    betas = []
    for t in range(30, len(df_X)):
        current_date = df_X.index[t]
        X_window = df_X.iloc[t-30:t+1]  
        y_window = df_y.iloc[t-30:t+1]
        X_window_b = np.c_[np.ones(X_window.shape[0]), X_window]  # Add bias (intercept)
        beta_t = np.linalg.inv(X_window_b.T.dot(X_window_b)).dot(X_window_b.T).dot(y_window)
        betas.append((current_date, beta_t))
    betas_df = pd.DataFrame([beta[1] for beta in betas], index=[beta[0] for beta in betas], columns=['Intercept', 'MKT', 'SMB','HML'])
    
    return betas_df
# checkdf=pd.read_csv('input_data/F-F_Research_Data_Factors_daily.CSV')
# to__cal_stock_betas(merged,checkdf)