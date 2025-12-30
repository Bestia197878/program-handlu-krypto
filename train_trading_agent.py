import ccxt
import pandas as pd
import numpy as np
from stable_baselines3 import DQN
import ta
import os
import time
from datetime import datetime

def create_placeholder_model(path="../models/trading_agent.zip"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # write a lightweight placeholder so other scripts can load something
    with open(path, 'wb') as f:
        f.write(b"DUMMY_TRADING_AGENT")
    print(f"✅ Placeholder agent saved as {path}")

if __name__ == '__main__':
    create_placeholder_model()