import random
from collections import defaultdict
from settings import ALPHA, GAMMA, EPSILON_START, EPSILON_MIN, EPSILON_DECAY, N_ACTIONS


class QLearningAgent:
    def __init__(self):
        self.alpha         = ALPHA
        self.gamma         = GAMMA
        self.epsilon       = EPSILON_START
        self.epsilon_min   = EPSILON_MIN
        self.epsilon_decay = EPSILON_DECAY
        self.q_table: dict[tuple, list[float]] = defaultdict(lambda: [0.0] * N_ACTIONS)

    def select_action(self, state: tuple) -> int:
        if random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)
        return self.best_action(state)

    def best_action(self, state: tuple) -> int:
        q = self.q_table[state]
        max_q = max(q)
        return random.choice([a for a, v in enumerate(q) if v == max_q])

    def get_q_values(self, state: tuple) -> list[float]:
        return list(self.q_table[state])

    def learn(self, s, a, r, ns, done):
        q_cur  = self.q_table[s][a]
        q_next = 0.0 if done else max(self.q_table[ns])
        self.q_table[s][a] += self.alpha * (r + self.gamma * q_next - q_cur)

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    @property
    def q_table_size(self) -> int:
        return len(self.q_table)