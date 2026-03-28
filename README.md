
# MultiFactor Investing 

This repository contains the full implementation and research framework for an adaptive multifactor investing strategy, orignally developed as part of a financial engineering capstone. The goal of this project is to leverage simulation-based learning algorithms to achieve five different optimazation goals: Returns, Volatility, Downside Volatility, Sharpe, and Sortino.


## Overview
This project systematically constructs equity portfolios based on the Fama-French 3-Factor Model: **Market (MKT), Size (SMB), and Value (HML)**. The Fama-French 3-Factor model is an extension of the standard mean-variance framework that captures systematic return sources beyond just market exposure.

• **MKT (Market − Risk Free):** Excess return over the risk-free rate (e.g., US Treasury Bills). This is your baseline market exposure.
• **SMB (Small Minus Big):** Based on the historical tendency of small-cap stocks to outperform large-cap stocks, though with higher volatility. A positive value tilts toward small-cap, negative toward large-cap.
• **HML (High Minus Low):** Based on the tendency of value stocks (high book-to-market ratio) to outperform growth stocks, though growth stocks often display more upside. A positive value tilts toward high book-to-market stocks, negative toward low book-to-market (growth).

Using a 3-factor model instead of single-factor mean-variance gives more granular control over the return stream by independently adjusting exposure to each systematic factor.
The model uses linear regression to estimate how a portfolio's return stream will behave in the out-of-sample period. The inputted factor targets (e.g., MKT-Rf, SMB, HML = 1.2, 0.2, −0.2) are aligned through Linear Programming Tracking Error Minimization — the goal being to find a combination of stocks where the difference between the regression period's return stream and the Fama-French target is as small as possible. The three constraints are: the number of stocks selected (q), a transaction cost cap of 0.2% per rebalance period, and portfolio weights summing to 100%.
There are multiple optional inputs when the optimization is backtested, including the number of regression years, the number of out-of-sample months, total portfolio value, and whether the portfolio is rebalanced statically or dynamically. The static strategy rebalances each period to the same originally inputted beta points. The dynamic strategy instead rebalances to the locally optimized beta points for each period — for example, when the objective is Sortino, each rebalance period uses the historical beta combination that maximized Sortino for that window, as determined by the bandit algorithm.


## How It Works

- **Optimazation**: The inputted exposure is aligned in the form of:
  $$RHS_t = \beta_{Mkt} (R_{m,t} - R_{f,t}) + \beta_{SMB} (SMB_t) + \beta_{HML} (HML_t)$$
 The solver then minimzes the L1-norm tracking error (absolute deviation), an improved version of standard least-square, with the goal of minimizing to be having the out-of-sample beta points as accurate as possible. The target return (RHS) is subtracted by the portfolio's excesss returns(X): 
  $$\min_{w} \sum_{t \in T} | \sum_{i \in I} (w_i \cdot X_{i,t}) - RHS_t |$$


  min_w  Σ_t | Σ_i (w_i · X_i,t) − RHS_t |
  
Absolute values are non-linear, so we introduce auxiliary variables ($\epsilon_t$) to "trap" the error on both sides of the target, allowing for a solveable linear system.: 
  \begin{aligned}
\sum_{i \in I} (w_i \cdot X_{i,t}) - \epsilon_t &\le RHS_t \\
\sum_{i \in I} (w_i \cdot X_{i,t}) + \epsilon_t &\ge RHS_t
\end{aligned}
  The number of equities being slected is limited to q by a binay decision variable, and the weight total weight of all equities msut sum to 100% of the investment:
$$\begin{aligned} 
\sum w_i &= 1.0 \\ 
w_i &\le z_i, \quad \forall i \in I \\ 
\sum z_i &\le q, \quad z_i \in \{0, 1\} 
\end{aligned}$$
Finally the total dollar cost of moving from the current portfolio ($w_{base}$) to the new optimal weights is constrained to less than or equal to the total portfolio value times % 0.2:
$$\sum_{i \in I} |w_i - w_{base,i}| \cdot \left( \frac{B \cdot t_{cost,i}}{P_i} \right) \le B * % 0.2$$

- **Adaptive Bandit Algorithm**
The bandit algorithm is currently set up as a recency-weighted walk-forward strategy through the five most recent months. I say 'currently' because this system is continuously being adjusted and improved, so the underlying logic is likely to change. The bandit algorithm is built on a search, score, and adjust framework — a set of beta points are tried, scored by all five rewards, then based on the current objective being tested, adjusted to a new set of beta points. The inter-objective rewarding is structured this way to maximize computational efficiency, since all rewards are computed at each simulation. When the first objective is tested (i.e., Max Return), 150 beta combinations are tried. On each combination, the rewards for the other four objectives are also saved — so once the 150 Max Return iterations finish, the next objective (Volatility) already has 150 sample points to use as a decision base, seeding from whichever beta combination produced the best Volatility score.
Walk-Forward Structure
The walk-forward design is in place to continuously expose the algorithm to the most recent data. When optimizing for month tt
t (e.g., March 2026), the first validation month is t−5t-5
t−5 (October 2025). The previous 36 months are used as the regression period for the LP optimizer:

Regression: [t−41, t−6]Validation: [t−5, t−1]\text{Regression: } [t-41,\ t-6] \qquad \text{Validation: } [t-5,\ t-1]
Regression: [t−41, t−6]Validation: [t−5, t−1]
The OOS return for October is saved, then all dates shift forward by one month — the new regression period becomes November 2022 – October 2025, optimizing for t−4t-4
t−4 (November 2025). This continues until all five months are evaluated. The five return streams are then joined into a single dataframe and passed to the reward function.

Neighborhood Search
The hill-climbing step searches in increments of ±0.1 along each beta dimension, clipped to the following bounds:
βMkt∈[0.7, 1.3],βSMB∈[−0.6, 0.6],βHML∈[−0.6, 0.6]\beta_{Mkt} \in [0.7,\ 1.3], \qquad \beta_{SMB} \in [-0.6,\ 0.6], \qquad \beta_{HML} \in [-0.6,\ 0.6]
βMkt​∈[0.7, 1.3],βSMB​∈[−0.6, 0.6],βHML​∈[−0.6, 0.6]
After each hill-climb step, a random perturbation of up to ±0.3 is applied around the current best to encourage exploration beyond the immediate neighborhood.
Recency Weighting
The weighted aspect of the bandit is implemented as a recency bias. As more months are included via the walk-forward structure, older periods may reflect less relevant market regimes. To compensate, the five validation months are scored with increasing weight toward the present:
w=[0.10, 0.15, 0.20, 0.25, 0.30]for months [t−5, t−4, t−3, t−2, t−1]w = [0.10,\ 0.15,\ 0.20,\ 0.25,\ 0.30] \quad \text{for months } [t-5,\ t-4,\ t-3,\ t-2,\ t-1]
w=[0.10, 0.15, 0.20, 0.25, 0.30]for months [t−5, t−4, t−3, t−2, t−1]
As for why five months rather than one or two — optimizing over a single recent month can result in severe overfitting, where the rewards are tuned exclusively to a previous month's conditions. The recency weighting handles the relevance decay without throwing out the broader context.
  
- 
- **MILP-Based Optimization**: Convert theoretical exposures into implementable portfolios, minimizing error and transaction costs.
- **Hedging Overlay**: Stabilize factor drift with synthetic hedge logic.



## 🛠 Tech Stack

- **Languages**: Python 3
- **Core Libraries**: `pandas`, `numpy`, `matplotlib`, `scipy`, `cvxpy`, `pulp`
- **Simulation**: Custom Monte Carlo with bootstrapping
- **ML/Algo**: ε-decaying bandit algorithm with multi-reward configuration
- **Optimization**: MILP with constraints on exposure, cardinality, and transaction cost

<!-- ## 📁 Project Structure -->

## 📁 Project Structure

```
/MultiFactor/
├── build/                      #custom version control (testing)
├── dist/                       #custom version support (testing)
├── Johanan's_tenure/           #project 
├── gitattributes               #git settings
├── gitignore                   #git settings

/MultiFactor/Johanan's_tenure    #project
├── __pycache__/                 # Python cache files (auto-generated; can be ignored)
├── background_scripts/          # Core Python scripts for analysis and logic
├── input_data/                  # Input data used to generate results
├── old/                         # Legacy notebooks and files (before Jan '23)
├── outputs/                     # Generated outputs including results and strategies
├── requirements/                # Dependencies and tech stack required to run the project
├── Run simulator copy/          # Duplicate notebooks with full code stack (ignore)
├── strategies/                  # Algorithmic methods and bandit strategy implementations
├── Run bandit.ipynb             # Notebook for developing the bandit algorithm
├── Run convex_optimizer.ipynb   # Notebook for convex portfolio optimization
├── Run future_simulator.ipynb   # Notebook for futures-based portfolio hedging
├── Run simulator safety.ipynb   # Development notebook with full functionality (use for development)
└── Run simulator.ipynb          # Main notebook for running the project in production
```



## 📜 License 
MIT License. Feel free to use, extend, and build upon this research framework. Contributions welcome.

## 👤 Authors

**Johanan Anton Pranesh**  
*M.S. Financial Engineering '25, Lehigh University*  
*King Street Alumni | Quant Research | Data Science*  
[Website](https://johananantonpranesh.github.io/) • [LinkedIn](https://www.linkedin.com/in/johanan-anton-pranesh/) • [Email](mailto:johanananton@outlook.com)

**Vincent Batten**  
*B.S. Finance '26, Lehigh University*  
*Investment Managment | Data Science*                  
[LinkedIn](https://www.linkedin.com/in/vincentbatten27/)
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
