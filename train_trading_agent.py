import ccxt
import pandas as pd
import numpy as np
from stable_baselines3 import DQN
import ta
import os
import time
from datetime import datetime

exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=26280)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

df = ta.add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume")

model = DQN(
    "MlpPolicy",
    env,
    learning_rate=0.001,
    batch_size=64,
    gamma=0.99,
    verbose=1
)
model.learn(total_timesteps=100000)
model.save("../models/trading_agent.zip")
print("✅ Agent handlowy zapisany jako ../models/trading_agent.zip")