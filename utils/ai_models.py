import random
import os
import pickle
import logging
logger = logging.getLogger(__name__)

class DummyAgent:
    def __init__(self, name="dummy"):
        self.name = name

    def predict(self, obs, deterministic=True):
        # returns (action, _)
        return random.choice([0, 1, 2]), None

def load_trading_agent(path=None):
    if path and os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            logger.warning("Nie udało się załadować modelu binarnego, używam DummyAgent")
    return DummyAgent('trading_agent')

def load_risk_agent(path=None):
    return DummyAgent('risk_agent')

def load_monitoring_agent(path=None):
    return DummyAgent('monitoring_agent')

def analyze_sentiment(texts):
    # very simple sentiment: -1..1
    if not texts:
        return 0.0
    score = 0.0
    for t in texts[:10]:
        if 'buy' in t.lower():
            score += 0.2
        if 'sell' in t.lower():
            score -= 0.2
    return max(-1.0, min(1.0, score))

def monitor_system_health(monitoring_agent, df, trade_history):
    return monitoring_agent

def make_trading_decision(trade_history, df, sentiment, risk_params, trading_agent):
    # Simple rule-based decision for stability
    if sentiment > 0.1:
        return 'BUY'
    if sentiment < -0.1:
        return 'SELL'
    return 'HOLD'

class TrainableAgent:
    """Very small trainable agent that keeps a score for actions.

    This is a toy trainer (pure Python) that can be used where
    stable-baselines3/torch are unavailable. It learns by simple
    reward counting and selects highest-scoring action.
    Actions: 0=HOLD, 1=BUY, 2=SELL
    """
    def __init__(self):
        self.scores = {0: 0.0, 1: 0.0, 2: 0.0}

    def act(self, obs=None):
        # choose best known action with some exploration
        if random.random() < 0.2:
            return random.choice([0,1,2])
        return max(self.scores, key=lambda k: self.scores[k])

    def update(self, action, reward):
        self.scores[action] = self.scores.get(action, 0.0) * 0.9 + reward

    def save(self, path):
        target_dir = os.path.dirname(os.path.abspath(path)) or os.getcwd()
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, os.path.basename(path)), 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return cls()

def train_simple_agent(episodes=100, steps_per_episode=50, save_path='../models/trading_agent.zip'):
    agent = TrainableAgent()
    for ep in range(episodes):
        balance = 1000.0
        position = 0.0
        price = 100.0
        for s in range(steps_per_episode):
            action = agent.act()
            # simulate price random walk
            price += random.uniform(-1.0, 1.0)
            reward = 0.0
            if action == 1:  # buy
                position += 1.0
                balance -= price
            elif action == 2 and position > 0:  # sell
                position -= 1.0
                balance += price
                reward = price - 100.0
            agent.update(action, reward)
    agent.save(save_path)
    return agent
