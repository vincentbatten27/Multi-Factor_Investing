## Attempted Reinfrocement Leanring Algorithm
#### This strategy did not work in the slightest. It was so counterproductive, that randomly guessing beta points and holding them constant would signifanctly outperform optimzied objectives
### Why?
#### This strategy was overly ambitious and overly complex, these changes were tried all in one go instead of incrmenetally calibrated and tested. Current modeling is simpler and improved due to adhering to better model creation practices.

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

After each hill-climb step, a random uniform beta shift is applied to expand the search:

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
