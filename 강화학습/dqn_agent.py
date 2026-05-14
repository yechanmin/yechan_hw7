import numpy as np
import random
from replay_buffer import ReplayBuffer
from settings import (
    STATE_DIM, N_ACTIONS, HIDDEN1, HIDDEN2,
    LR, GAMMA, EPSILON_START, EPSILON_MIN, EPSILON_DECAY,
    BATCH_SIZE, TARGET_SYNC
)


def _relu(x):
    return np.maximum(0, x)

def _relu_grad(x):
    return (x > 0).astype(np.float32)


class NumpyNet:
    def __init__(self, in_dim, h1, h2, out_dim, lr):
        self.lr = lr
        scale1 = np.sqrt(2.0 / in_dim)
        scale2 = np.sqrt(2.0 / h1)
        scale3 = np.sqrt(2.0 / h2)
        self.W1 = np.random.randn(in_dim, h1).astype(np.float32) * scale1
        self.b1 = np.zeros(h1, dtype=np.float32)
        self.W2 = np.random.randn(h1, h2).astype(np.float32) * scale2
        self.b2 = np.zeros(h2, dtype=np.float32)
        self.W3 = np.random.randn(h2, out_dim).astype(np.float32) * scale3
        self.b3 = np.zeros(out_dim, dtype=np.float32)

    def forward(self, x):
        self._x  = x
        self._z1 = x @ self.W1 + self.b1
        self._a1 = _relu(self._z1)
        self._z2 = self._a1 @ self.W2 + self.b2
        self._a2 = _relu(self._z2)
        self._z3 = self._a2 @ self.W3 + self.b3
        return self._z3

    def backward(self, loss_grad):
        dz3 = loss_grad
        dW3 = self._a2.T @ dz3
        db3 = dz3.sum(axis=0)

        da2 = dz3 @ self.W3.T
        dz2 = da2 * _relu_grad(self._z2)
        dW2 = self._a1.T @ dz2
        db2 = dz2.sum(axis=0)

        da1 = dz2 @ self.W2.T
        dz1 = da1 * _relu_grad(self._z1)
        dW1 = self._x.T @ dz1
        db1 = dz1.sum(axis=0)

        clip = 1.0
        for g in [dW1, db1, dW2, db2, dW3, db3]:
            np.clip(g, -clip, clip, out=g)

        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3

    def copy_weights_from(self, other):
        self.W1 = other.W1.copy()
        self.b1 = other.b1.copy()
        self.W2 = other.W2.copy()
        self.b2 = other.b2.copy()
        self.W3 = other.W3.copy()
        self.b3 = other.b3.copy()

    def predict_single(self, x):
        z1 = _relu(x @ self.W1 + self.b1)
        z2 = _relu(z1 @ self.W2 + self.b2)
        return z2 @ self.W3 + self.b3


class DQNAgent:
    def __init__(self):
        self.epsilon       = EPSILON_START
        self.epsilon_min   = EPSILON_MIN
        self.epsilon_decay = EPSILON_DECAY
        self.gamma         = GAMMA
        self.batch_size    = BATCH_SIZE

        self.online = NumpyNet(STATE_DIM, HIDDEN1, HIDDEN2, N_ACTIONS, LR)
        self.target = NumpyNet(STATE_DIM, HIDDEN1, HIDDEN2, N_ACTIONS, LR)
        self.target.copy_weights_from(self.online)

        self.buffer     = ReplayBuffer()
        self._step_cnt  = 0
        self.loss_hist: list[float] = []

    def select_action(self, state: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.randrange(N_ACTIONS)
        q = self.online.predict_single(state)
        return int(np.argmax(q))

    def best_action(self, state: np.ndarray) -> int:
        q = self.online.predict_single(state)
        return int(np.argmax(q))

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        return self.online.predict_single(state)

    def push(self, s, a, r, ns, done):
        self.buffer.push(s, a, r, ns, done)

    def learn(self):
        if len(self.buffer) < self.batch_size:
            return
        self._step_cnt += 1

        s, a, r, ns, d = self.buffer.sample(self.batch_size)

        q_next     = self.target.forward(ns)
        q_next_max = q_next.max(axis=1)
        targets    = r + self.gamma * q_next_max * (1 - d)

        q_pred_all = self.online.forward(s)
        q_pred     = q_pred_all[np.arange(self.batch_size), a]

        loss_val   = float(np.mean((q_pred - targets) ** 2))
        self.loss_hist.append(loss_val)
        if len(self.loss_hist) > 200:
            self.loss_hist.pop(0)

        grad       = q_pred_all.copy()
        grad[np.arange(self.batch_size), a] = (q_pred - targets) * 2 / self.batch_size
        self.online.backward(grad)

        if self._step_cnt % TARGET_SYNC == 0:
            self.target.copy_weights_from(self.online)

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    @property
    def avg_loss(self) -> float:
        return float(np.mean(self.loss_hist)) if self.loss_hist else 0.0

    @property
    def buf_size(self) -> int:
        return len(self.buffer)