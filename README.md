
# MultiFactor Investing 

This repository contains the full implementation and research framework for an adaptive multifactor investing strategy, developed as part of a financial engineering capstone.

## 🔍 Overview

This project systematically constructs equity portfolios based on the Fama-French 3-Factor Model: **Market (MKT)**, **Size (SMB)**, and **Value (HML)**. It leverages simulation-based evaluation and adaptive learning algorithms to optimize downside protection and improve risk-adjusted returns.

## 📈 Key Features

- **Factor-Tilted Portfolio Simulation**: Generate returns using custom factor exposures.
- **Monte Carlo Stress Testing**: Assess long-term downside and drawdown risk.
- **Adaptive Bandit Algorithm**: Discover high-performing weight combinations using ε-decaying exploration and multi-objective reward selection.
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
*M.S. Financial Engineering'25, Lehigh University*  
*King Street Alumni | Quant Research | Data Science*  
[Website](https://johananantonpranesh.github.io/) • [LinkedIn](https://www.linkedin.com/in/johanan-anton-pranesh/) • [Email](mailto:johanananton@outlook.com)

**Vincent Batten**  
*4+1 Financial Engineering'27, Lehigh University*  

# New Contributors
**Nate Songsstad**  
*M.S. Financial Engineering'27, Lehigh University*  

**Sethu Chanra**  
*IBE Financial Engineering'28, Lehigh University*  


# Former Contributors
** Shisheng Liang**  
*M.S. Financial Engineering'25, Lehigh University*  

**Asim Turk**  
*M.S. Financial Engineering'24, Lehigh University*  
