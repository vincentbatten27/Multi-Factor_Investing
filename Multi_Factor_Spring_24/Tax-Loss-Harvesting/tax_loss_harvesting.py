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
    wei = LpVariable.dicts('Weight', tickers, lowBound=0)  # Weights for stock i in the optimal portfolio
    aux = LpVariable.dicts('Y', tickers, lowBound=0)  # Absolute value of change for stock i from base weights
    err = LpVariable.dicts('Error', monthly_data.index, lowBound=0)  # Error term for portfolio
    binary = LpVariable.dicts('bin', tickers, cat=LpBinary)  # Used if we want to limit the # of stocks we want to have in optimal portfolio
    tr_cost = LpVariable.dicts('Transaction_Cost', tickers, lowBound=0)  # Total Transaction cost for stock i in the optimal portfolio
    shares = LpVariable.dicts('shares', tickers, lowBound=0)  # Total Transaction cost for stock i in the optimal portfolio

    # New decision variable for tax-loss harvesting
    tax_harvest = LpVariable.dicts('Tax_Harvest', tickers, lowBound=0)

    # Objective Function - Minimize the error term and maximize tax benefits
    index += lpSum(err[t] for t in monthly_data.index) - lpSum(tax_harvest[i] for i in tickers)

    # Constraint: Weights sum to 1
    index += lpSum(wei[i] for i in tickers) == 1

    # Constraint: Absolute value of change in weights from base weights
    for i in tickers:
        index += aux[i] >= base_weights[i] - wei[i]
        index += aux[i] >= wei[i] - base_weights[i]

    index += lpSum(aux[i] for i in tickers) <= 1

    # Constraint: Error term
    for t in monthly_data.index:
        index += lpSum(wei[i] * (monthly_data.loc[t, i] - ff3_monthly.loc[t, 'RF']) for i in tickers) - err[t] <= (
                mkt_opt * ff3_monthly.loc[t, 'Mkt-RF'] + smb_opt * ff3_monthly.loc[t, 'SMB'] + hml_opt * ff3_monthly.loc[t, 'HML'])
        index += lpSum(wei[i] * (monthly_data.loc[t, i] - ff3_monthly.loc[t, 'RF']) for i in tickers) + err[t] >= (
                mkt_opt * ff3_monthly.loc[t, 'Mkt-RF'] + smb_opt * ff3_monthly.loc[t, 'SMB'] + hml_opt * ff3_monthly.loc[t, 'HML'])

    # Shares
    for i in tickers:
        index += shares[i] == (aux[i] * B / s_price[i])

    # Transaction Costs
    for i in tickers:
        index += lpSum(aux[i] * B * t_cost[i] / s_price[i]) == tr_cost[i]

    index += lpSum(tr_cost[i] for i in tickers) <= 2000

    # Limit # of stocks in Optimal Portfolio
    for i in tickers:
        index += wei[i] <= binary[i]

    index += lpSum(binary[i] for i in tickers) <= q

    # Tax-loss harvesting constraints
    for i in tickers:
        # Example constraint: Only harvest losses if the stock has decreased in value
        index += tax_harvest[i] <= max(0, s_price[i] - monthly_data.loc[monthly_data.index[-1], i])

    index.solve()