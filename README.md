
# MultiFactor Investing 

This repository contains the full implementation and research framework for an adaptive multifactor investing strategy, orignally developed as part of a financial engineering capstone. The goal of this project is to leverage simulation-based learning algorithms to achieve five different optimazation goals: Returns, Volatility, Downside Volatility, Sharpe, and Sortino.


## Overview
This project systematically constructs equity portfolios based on the Fama-French 3-Factor Model: **Market (MKT), Size (SMB), and Value (HML)**. The Fama-French 3-Factor model is an extension of the standard mean-variance framework that captures systematic return sources beyond just market exposure.
<br>
• **MKT (Market − Risk Free):** Excess return over the risk-free rate (e.g., US Treasury Bills). This is your baseline market exposure.<br>
• **SMB (Small Minus Big):** Based on the historical tendency of small-cap stocks to outperform large-cap stocks, though with higher volatility. A positive value tilts toward small-cap, negative toward large-cap.<br>
• **HML (High Minus Low):** Based on the tendency of value stocks (high book-to-market ratio) to outperform growth stocks, though growth stocks often display more upside. A positive value tilts toward high book-to-market stocks, negative toward low book-to-market (growth).<br>

Using a 3-factor model instead of single-factor mean-variance gives more granular control over the return stream by independently adjusting exposure to each systematic factor.
The model uses linear regression to estimate how a portfolio's return stream will behave in the out-of-sample period. The inputted factor targets (e.g., MKT-Rf, SMB, HML = 1.2, 0.2, −0.2) are aligned through Linear Programming Tracking Error Minimization — the goal being to find a combination of stocks where the difference between the regression period's return stream and the Fama-French target is as small as possible. The three constraints are: the number of stocks selected (q), a transaction cost cap of 0.2% per rebalance period, and portfolio weights summing to 100%.

There are multiple optional inputs when the optimization is backtested, including the number of regression years, the number of out-of-sample months, total portfolio value, and whether the portfolio is rebalanced statically or dynamically. The static strategy rebalances each period to the same originally inputted beta points. The dynamic strategy instead rebalances to the locally optimized beta points for each period — for example, when the objective is Sortino, each rebalance period uses the historical beta combination that maximized Sortino for that window, as determined by the bandit algorithm.

---

## How It Works

### **Optimazation**: The inputted exposure is aligned in the form of:

$$
RHS_t = \beta_{Mkt} (R_{m,t} - R_{f,t}) + \beta_{SMB} (SMB_t) + \beta_{HML} (HML_t)
$$

The solver then minimzes the L1-norm tracking error (absolute deviation), an improved version of standard least-square, with the goal of minimizing to be having the out-of-sample beta points as accurate as possible. The target return (RHS) is subtracted by the portfolio's excesss returns ($X$):

$$
\min_{w} \sum_{t \in T} \left| \sum_{i \in I} (w_i \cdot X_{i,t}) - RHS_t \right|
$$

Absolute values are non-linear, so we introduce auxiliary variables ($\epsilon_t$) to "trap" the error on both sides of the target, allowing for a solveable linear system:

$$
\begin{aligned}
\sum_{i \in I} (w_i \cdot X_{i,t}) - \epsilon_t &\le RHS_t \\
\sum_{i \in I} (w_i \cdot X_{i,t}) + \epsilon_t &\ge RHS_t
\end{aligned}
$$

The number of equities being slected is limited to $q$ by a binay decision variable, and the weight total weight of all equities msut sum to 100% of the investment:

$$
\begin{aligned}
\sum w_i &= 1.0 \\
w_i &\le z_i, \quad \forall i \in I \\
\sum z_i &\le q, \quad z_i \in {0, 1}
\end{aligned}
$$

Finally the total dollar cost of moving from the current portfolio ($w_{base}$) to the new optimal weights is constrained to ≤$\le 0.2%$ of total portfolio value **B**:

$$
\sum_{i \in I} |w_i - w_{base,i}| \cdot \left( \frac{B \cdot t_{cost,i}}{P_i} \right) \le 0.002 \cdot B
$$

---

### **Adaptive Bandit Algorithm**

#### Adaptive Bandit Algorithm

The bandit algorithm is currently set up as a recency-weighted walk-forward strategy through the five most recent months. I say "currently" because this system is continuously being adjusted and improved, so the underlying logic is likely to change.

The bandit algorithm is built on a search, score, and adjust framework — a set of beta points are tried, scored by all five rewards, then based on the current objective being tested, adjusted to a new set of beta points.

The inter-objective rewarding is structured this way to maximize computational efficiency, since all rewards are computed at each simulation. When the first objective is tested (i.e., Max Return), 150 beta combinations are tried. On each combination, the rewards for the other four objectives are also saved — so once the 150 Max Return iterations finish, the next objective (Volatility) already has 150 sample points to use as a decision base, seeding from whichever beta combination produced the best Volatility score.


#### **Walk-Forward Structure**

The walk-forward design is in place to continuously expose the algorithm to the most recent data.

When optimizing for month $t$ (e.g., March 2026), the first validation month is $t-5$ (October 2025). The previous 36 months are used as the regression period for the LP optimizer:

$$
\text{Regression: } [t-41,\ t-6] \quad \text{Validation: } [t-5,\ t-1]
$$

The OOS return for October is saved, then all dates shift forward by one month — the new regression period becomes November 2022 – October 2025, optimizing for $t-4$ (November 2025). This continues until all five months are evaluated.

The five return streams are then joined into a single dataframe and passed to the reward function.


#### **Neighborhood Search**

The hill-climbing step searches in increments of $$\pm 0.1$$ along each beta dimension, clipped to the following bounds:

$$
\beta_{Mkt} \in [0.7, 1.3], \quad \beta_{SMB} \in [-0.6, 0.6], \quad \beta_{HML} \in [-0.6, 0.6]
$$

After each hill-climb step, a random uniform search is checked of up to:

$$
\pm U(0.3)
$$

is applied around the current best to encourage exploration beyond the immediate neighborhood.


#### **Recency Weighting**

The weighted aspect of the bandit is implemented as a recency bias. As more months are included via the walk-forward structure, older periods may reflect less relevant market regimes.

To compensate, the five validation months are scored with increasing weight toward the present:

$$
w = [0.10,\ 0.15,\ 0.20,\ 0.25,\ 0.30]
\quad \text{for months } [t-5,\ t-4,\ t-3,\ t-2,\ t-1]
$$

As for why five months rather than one or two — optimizing over a single recent month can result in severe overfitting, where the rewards are tuned exclusively to a previous month's conditions. The recency weighting handles the relevance decay without throwing out the broader context.

---

### **Streamlit UI**
####  Input Sections
** Input Sections




## 🛠 Tech Stack

- **Languages**: Python 3
- **Core Libraries**: `pandas`, `numpy`, `matplotlib`, `scipy`, `cvxpy`, `pulp`,'streamlit'
- **Simulation**: Custom Monte Carlo with bootstrapping
- **ML/Algo**: ε-decaying bandit algorithm with multi-reward configuration
- **Optimization**: MILP with constraints on exposure, cardinality, and transaction cost

<!-- ## 📁 Project Structure -->

## 📁 Project Structure

```
Multi_Factor_25_26/
├── streamlit_optimizer.py        # Streamlit front-end: inputs, optimization, Monte Carlo visualization
├── RunSim_utils.py               # Core simulation engine: LP optimizer, walk-forward backtest, all utility functions
├── run_sim_scheduler.py          # Scheduler for running the bandit algorithm across months (WIP)
├── Run_Simulator_Messy.py        # Area for building and testing functions of Run simulator
├── RunSim_utils.ipynb            # Notebook version of RunSim_utils for development/debugging
├── Run simulator.ipynb           # Notebook for running and inspecting simulations interactively
│
├── monthly_prices.csv            # Monthly stock price data for S&P 500 universe
├── monthly_returns.csv           # Monthly return data derived from prices
├── spy_data.csv                  # S&P 500 index return data
├── ff3_wrds.csv                  # Fama-French 3-factor data from WRDS
├── daat.csv                      # Stock price data used for weight drift calculations
├── Total SPX.xlsx                # Year-by-year S&P 500 constituent membership
├── scrape_log.csv                # Log of Stooq scraping results and rate limit hits
├── requirements.txt              # Python dependencies
│
├── Front_End_Strategies/         # Bandit algorithm output CSVs — one folder per objective
│   ├── max_return/
│   ├── sharpe/
│   ├── sortino/
│   ├── volatility/
│   └── downside_vol/
│
├── Active_Strategy_CSVs/         # CSVs from active strategy runs (old)
├── Resampled_CSVs/               # CSVs from resampled backtest runs (old)
├── Resampled_Monthly/            # Monthly resampled output data (old)
├── Reward_CSVs_Surrogate/        # Surrogate model reward CSVs used in dynamic rebalancing (old)
│
├── SPY_Weights.xlsx              # SPY constituent weights
├── SPY_Ticker_Weights.csv        # Ticker-level SPY weights
├── SPY_Weights_with_T.csv        # SPY weights with transaction cost data
├── SPY_V.csv                     # SPY valuation data
├── SPY_IV.csv                    # SPY implied volatility data
├── Nifty_50.csv                  # Nifty 50 constituent data (Indian market extension)
├── nifty_stocks_data.csv         # Nifty 50 stock return data
├── nifty50_index_data.csv        # Nifty 50 index return data
│
└── Useless_csvs/                 # Deprecated or scratch output files
```



## 📜 License 
MIT License. Feel free to use, extend, and build upon this research framework. Contributions welcome.

## 👤 Authors

**Johanan Anton Pranesh**  
*M.S. Financial Engineering '25, Lehigh University*  
*King Street Alumni | Quant Research | Data Science*  
[Website](https://johananantonpranesh.github.io/) • [LinkedIn](https://www.linkedin.com/in/johanan-anton-pranesh/) • [Email](mailto:johanananton@outlook.com)

**Vincent Batten**  
*B.S. Finance '26 (Data Science and Probaility & Stat minors), Lehigh University*  
*Investment Managment | Data Science*                  
[LinkedIn](https://www.linkedin.com/in/vincentbatten27/) • [Email](mailto:vincentbatten27@gmail.com)
# Other Contributors

**Kshitij Bhandari**  
*M.S. Financial Engineering '26, Lehigh University*  

**Nate Songstad**  
*M.S. Financial Engineering '27, Lehigh University*  

# Former Contributors
**Shisheng Liang**  
*M.S. Financial Engineering'25, Lehigh University*  

**Asim Turk**  
*M.S. Financial Engineering'24, Lehigh University*  
