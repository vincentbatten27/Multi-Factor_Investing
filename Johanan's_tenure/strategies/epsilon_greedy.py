import numpy as np
import random
from strategies.base import Strategy

class EpsilonGreedyStrategy(Strategy):
    def __init__(self, epsilon=1.0, decay=0.95, min_epsilon=0.01):
        self.epsilon = epsilon
        self.decay = decay
        self.min_epsilon = min_epsilon

    def select_combination(self, bandit):
        if random.random() < self.epsilon:
            combination = np.random.uniform(low=0.9, high=2.2, size=3)
            print(f"[Exploration] ε={self.epsilon:.4f}")
        else:
            candidates = bandit.explore_direction(bandit.best_combination)
            candidates.sort(key=lambda x: x[1], reverse=True)
            combination = candidates[0][0]
            print(f"[Exploitation] ε={self.epsilon:.4f}")

        self.epsilon = max(self.epsilon * self.decay, self.min_epsilon)
        return combination
