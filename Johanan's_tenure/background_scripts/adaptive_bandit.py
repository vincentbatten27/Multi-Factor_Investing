import numpy as np
import pandas as pd
import os
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
class AdaptiveBandit:
    def __init__(self, target_years=5, objective='max_return', strategy=None):
        self.target_years = target_years
        self.objective = objective.lower()
        self.best_combination = np.array([1.0, 0.0, 0.0])
        self.best_return = -np.inf
        self.storage_file = f"explored_{self.objective}.csv"
        self.explored = self.load_explored_combinations()
        self.strategy = strategy

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

    def check_existing_combination(self, combination):
        rounded = np.round(combination, 4)
        match = self.explored[
            (np.isclose(self.explored['c1'], rounded[0])) &
            (np.isclose(self.explored['c2'], rounded[1])) &
            (np.isclose(self.explored['c3'], rounded[2]))
        ]
        if not match.empty:
            return match.iloc[0]['reward']
        return None

    def evaluate_combination(self, beta_combination):
        # Simulate portfolio using your logic
        # Example placeholder below:
        simulated_df = sp_final_visual() if self.objective == 'max_return' else get_consistently_worst_portfolio(None, 'Optimized Portfolio')
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
        directions = [-0.1, 0.1]
        for i in range(3):
            for delta in directions:
                new_combination = base_combination.copy()
                new_combination[i] += delta
                new_combination = np.clip(new_combination, 0.9, 2.2)

                existing = self.check_existing_combination(new_combination)
                if existing is not None:
                    reward = existing
                else:
                    simulated_df = self.evaluate_combination(new_combination)
                    reward = self.reward_function(simulated_df)
                    self.save_combination(new_combination, reward)

                candidates.append((new_combination, reward))

        return candidates

    def run_bandit(self, iterations=50, initializer='yes'):
        print(f"Running bandit optimization for objective: '{self.objective}' using {self.strategy.__class__.__name__}")

        # Initialization
        base = np.array([1.0, 0.0, 0.0])
        if initializer == 'yes':
            simulated_df = self.evaluate_combination(base)
            reward = self.reward_function(simulated_df)
            self.save_combination(base, reward)
            self.best_combination = base
            self.best_return = reward
        else:
            existing = self.check_existing_combination(base)
            if existing is not None:
                self.best_combination = base
                self.best_return = existing

        print(f"Base Combination: {self.best_combination}, Base Score ({self.objective}): {self.best_return:.4f}")

        for i in range(iterations):
            combination = self.strategy.select_combination(self)

            reward = self.check_existing_combination(combination)
            if reward is None:
                simulated_df = self.evaluate_combination(combination)
                reward = self.reward_function(simulated_df)
                self.save_combination(combination, reward)

            if reward > self.best_return:
                self.best_combination = combination
                self.best_return = reward
                print(f"New Best! Combination: {self.best_combination}, Reward: {self.best_return:.4f}")

        print("\nFinal Best Combination Found:")
        print(f"Best Combination: {self.best_combination}, Best Score ({self.objective}): {self.best_return:.4f}")
