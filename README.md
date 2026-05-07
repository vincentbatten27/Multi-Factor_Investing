# Multi-Factor Investing

This repository contains the full implementation and research framework for an adaptive multi-factor investing strategy, originally developed as part of a financial engineering capstone. The goal of this project is to leverage simulation-based learning algorithms to achieve five different optimization objectives: Returns, Volatility, Downside Volatility, Sharpe, and Sortino.


## Overview

This project systematically constructs equity portfolios based on the Fama-French 3-Factor Model: **Market (MKT), Size (SMB), and Value (HML)**. The Fama-French 3-Factor model is an extension of the standard mean-variance framework that captures systematic return sources beyond just market exposure.

• **MKT (Market − Risk Free):** Excess return over the risk-free rate (e.g., US Treasury Bills). This is the baseline market exposure.<br>
• **SMB (Small Minus Big):** Based on the historical tendency of small-cap stocks to outperform large-cap stocks, though with higher volatility. A positive value tilts toward small-cap, negative toward large-cap.<br>
• **HML (High Minus Low):** Based on the tendency of value stocks (high book-to-market ratio) to outperform growth stocks, though growth stocks often display more upside. A positive value tilts toward high book-to-market, negative toward low book-to-market (growth).<br>

Using a 3-factor model instead of single-factor mean-variance gives more granular control over the return stream by independently adjusting exposure to each systematic factor.

The model uses linear regression to estimate how a portfolio's return stream will behave in the out-of-sample period. The inputted factor targets (e.g., MKT-Rf, SMB, HML = 1.2, 0.2, −0.2) are aligned through Linear Programming Tracking Error Minimization — the goal being to find a combination of stocks where the difference between the regression period's return stream and the Fama-French target is as small as possible. The three constraints are: the number of stocks selected ($q$), a transaction cost cap of 0.2% per rebalance period, and portfolio weights summing to 100%.

There are multiple optional inputs when the optimization is backtested, including the number of regression years, the number of out-of-sample months, total portfolio value, and whether the portfolio is rebalanced statically or dynamically. The **static** strategy rebalances each period to the same originally inputted beta points. The **dynamic** strategy instead rebalances to the locally optimized beta points for each period — for example, when the objective is Sortino, each rebalance period uses the historical beta combination that maximized Sortino for that window, as determined by the bandit algorithm.

---

## How It Works

### **Optimization**

The inputted exposure is aligned in the form of:

$$
RHS_t = \beta_{Mkt} (R_{m,t} - R_{f,t}) + \beta_{SMB} (SMB_t) + \beta_{HML} (HML_t)
$$

The solver then minimizes the L1-norm tracking error (absolute deviation), an improved version of standard least-squares, with the goal of making the out-of-sample beta points as accurate as possible. The target return ($RHS$) is subtracted from the portfolio's excess returns ($X$):

$$
\min_{w} \sum_{t \in T} \left| \sum_{i \in I} (w_i \cdot X_{i,t}) - RHS_t \right|
$$

Absolute values are non-linear, so we introduce auxiliary variables ($\epsilon_t$) to "trap" the error on both sides of the target, allowing for a solvable linear system:

$$
\begin{aligned}
\sum_{i \in I} (w_i \cdot X_{i,t}) - \epsilon_t &\le RHS_t \\
\sum_{i \in I} (w_i \cdot X_{i,t}) + \epsilon_t &\ge RHS_t
\end{aligned}
$$

The number of equities being selected is limited to $q$ by a binary decision variable, and the total weight of all equities must sum to 100% of the investment:

$$
\begin{aligned}
w_i &\ge w_{i,\text{initial}} \quad \forall i \in I_{\text{existing}} \\
\sum_{i \in I} w_i &= 1
\end{aligned}
$$

The total dollar cost of moving from the current portfolio ($w_{base}$) to the new optimal weights is constrained to $\le 0.2\%$ of total portfolio value $B$:

$$
\sum_{i \in I} |w_i - w_{base,i}| \cdot \left( \frac{B \cdot t_{cost,i}}{P_i} \right) \le 0.002 \cdot B
$$

Finally, there is an optional constraint for existing weights. This allows an investor to plug in an already held portfolio, and the optimization maintains a minimum level of weights based on the starting value. The optimization model then treats the inputted weights as minimum constraints when selecting the equities to fit to the set of inputted beta points — adjusting the other equities to compensate.

---

### **Adaptive Bandit Algorithm**

The bandit algorithm is currently set up as a surrogate-based 1-year non-rebalanced validation period. I say "currently" because this system is continuously being adjusted and improved, so the underlying logic is likely to change.

The bandit is built on a **search, score, and adjust** framework: a set of beta points is tried, scored across all five rewards, then — based on the current objective being tested — adjusted to a new set of beta points.

The inter-objective rewarding is structured this way to maximize computational efficiency, since all rewards are computed at each simulation. When the first objective is tested (e.g., Max Return), 150 beta combinations are tried. On each combination, the rewards for the other four objectives are also saved — so once the 150 Max Return iterations finish, the next objective (Volatility) already has 150 sample points to use as a decision base, seeding from whichever beta combination produced the best Volatility score.

#### **Period**

The **validation** period, where the rewards are scored, runs from $t-13$ to $t-1$ (the previous 12 months). The **regression** period, where the optimization is run to estimate the classification of each Fama-French beta point, runs from $t-49$ to $t-14$ (36 months).

For example, if we were optimizing beta points for April 1, 2026, the validation period would run from April 1, 2025 to March 31, 2026, and the regression period would run from April 1, 2022 to March 31, 2025. For each sequential month, all dates are iterated by one ($t \rightarrow t+1$).

#### **Surrogate**

The necessity of surrogate strategies is a complex argument, but in short: risk-adjusted return formulas do not have the intrinsic additive and convex properties that a surrogate strategy can have. That is, we take the formula for, say, Sharpe:

$$
R^{\text{sharpe}} = \frac{\text{mean}(r^{\text{OPT}} - r_f)}{\text{std}(r^{\text{OPT}})}
$$

and then approximate an additive and convex solution that converges to it:

$$
R^{\text{sharpe-surrogate}} = \text{mean}(r^{\text{OPT}} - r_f) - \lambda_{sh} \cdot \text{std}(r^{\text{OPT}})^2
$$

The same framework applies to Sortino, where the penalty is the mean squared downside deviation below the minimum acceptable return (MAR = 0):

$$
R^{\text{sortino}} = \frac{\text{mean}(r^{\text{OPT}} - r_f)}{\text{mean}(\sigma^-)}
$$

$$
R^{\text{sortino-surrogate}} = \text{mean}(r^{\text{OPT}} - r_f) - \lambda_{so} \cdot \text{mean}\left(\min(r^{\text{OPT}} - r_f - \text{MAR},\ 0)^2\right)
$$

where $r^{\text{OPT}}$ is the optimized portfolio's return stream over the validation window, $r_f$ is the risk-free rate, and $\lambda$ is the calibration parameter that controls the weight of the variance (Sharpe) or downside deviation (Sortino) penalty. Current calibrated values: $\lambda_{sh} = 7$, $\lambda_{so} = 60$.

To calibrate $\lambda$ so that the surrogate properly estimates the true risk-adjusted reward, we run a Monte Carlo simulation of 45 runs that cycles through different $\lambda$ values — with varying periods and beta combinations. The Monte Carlo is then scored on two criteria: **top-5 point overlap** and **Spearman rank correlation ($\rho$)**. Criterion 1 requires that the top 5 performing beta combinations under the surrogate match those under the true objective. For all $\lambda$ values where that is the case, we then choose the $\lambda$ with the highest rank correlation. From there, we repeat the process on new data and average the two beta combinations that scored best.

#### **Neighborhood Search**

The hill-climbing step searches in increments of $\pm 0.1$ along each beta dimension, clipped to the following bounds:

$$
\beta_{Mkt} \in [0.7, 1.5], \quad \beta_{SMB} \in [-0.6, 0.6], \quad \beta_{HML} \in [-0.6, 0.6]
$$

After each hill-climb step, a random uniform beta shift of $\pm U(0.3)$ is applied around the current best to encourage exploration beyond the immediate neighborhood.

---

### **Streamlit UI**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://multi-factor-investing.streamlit.app/)

#### User Interface

The Streamlit UI is the front end of the optimization and bandit algorithm system. It creates an environment where optional inputs can be selected, and the current weights and historical performance are displayed. It allows users to decide what beta points to set a portfolio to, any constrained holdings or previous portfolios, and the Fama-French beta targets — whether custom or recommended by the adaptive bandit algorithm.

#### Presets

Each preset (Max Return, Min Volatility, etc.) is populated dynamically from the bandit's best-found beta combination for that objective as of the current month's CSV. Selecting a preset locks the constrained holdings toggle and passes two keys: `drm` for dynamic rebalancing monthly, and the preset objective that was selected. The historical performance is iteratively rebalanced to its own locally optimal betas rather than holding the selected preset fixed (as the custom option does).

---

## 🛠 Tech Stack

- **Languages**: Python 3
- **Core Libraries**: `pandas`, `numpy`, `matplotlib`, `scipy`, `pulp`, `streamlit`, `datetime`
- **Simulation**: Custom Monte Carlo with bootstrapping
- **ML/Algo**: ε-decaying bandit algorithm with multi-reward configuration
- **Optimization**: MILP with constraints on exposure, cardinality, and transaction cost

---

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

---

## License

MIT License. Feel free to use, extend, and build upon this research framework. Contributions welcome.

Data is sourced from WRDS, Stooq, and Alpha Vantage.

---

# 👤 Authors

**Johanan Anton Pranesh**
*M.S. Financial Engineering '25, Lehigh University*
*King Street Alumni | Quant Research | Data Science*
[Website](https://johananantonpranesh.github.io/) • [LinkedIn](https://www.linkedin.com/in/johanan-anton-pranesh/) • [Email](mailto:johanananton@outlook.com)

**Vincent Batten**
*B.S. Finance '26 (Data Science and Probability & Statistics minors), Lehigh University* <br>
*Investment Management | Data Science* <br>
[LinkedIn](https://www.linkedin.com/in/vincentbatten27/) • [Email](mailto:vincentbatten27@gmail.com)

**Nate Songstad**
*M.S. Financial Engineering '27, Lehigh University*
[LinkedIn](https://www.linkedin.com/in/nate-songstad/) • [Email](songstad.nathaniel@gmail.com)

## Other Contributors

**Kshitij Bhandari**
*M.S. Financial Engineering '26, Lehigh University*

## Former Contributors

**Asim Turk**
*M.S. Financial Engineering '24, Lehigh University*
