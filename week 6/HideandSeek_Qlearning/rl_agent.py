# dqn_agent.py
import random
from collections import defaultdict

class QLearningAgent:
    def __init__(self):
        self.action_size = 5
        self.alpha = 0.2 #학습률
        self.gamma = 0.98 #감마, 미래값 반영정도

        self.epsilon = 1.0 # 초기 탐험 확률 (100% 랜덤으로 시작)
        self.epsilon_min = 0.02 # 최소 탐험 확률
        self.epsilon_decay = 0.999 # 매 에피소드마다 감소 비율
        self.q_table = defaultdict(lambda: [0.0] * self.action_size)

    #학습 중 행동 선택
    def select_action(self, state):
        if random.random() < self.epsilon: #epsilon 보다 작으면 랜덤 행동
            return random.randint(0, self.action_size - 1)
        q_values = self.q_table[state]
        max_q = max(q_values)
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions) # 아니면 최적 행동
    # 순수 그리디 정책 (탐험 없음)
    def best_action(self, state):
        q_values = self.q_table[state]
        max_q = max(q_values)
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)
    #Q-learning의 핵심 Q_table 업데이트
    def learn(self, state, action, reward, next_state, done):
        current_q = self.q_table[state][action]
        next_max_q = 0 if done else max(self.q_table[next_state])
        target = reward + self.gamma * next_max_q
        self.q_table[state][action] += self.alpha * (target - current_q)

    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            if self.epsilon < self.epsilon_min:
                self.epsilon = self.epsilon_min

    def get_q_values(self, state):
        return self.q_table[state]