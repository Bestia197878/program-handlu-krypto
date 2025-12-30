import logging
import os
from datetime import datetime
logger = logging.getLogger(__name__)

def get_market_data(symbol='BTC/USDT', timeframe='1h', limit=500):
    try:
        import ccxt
        import pandas as pd
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'enableRateLimit': True
        })
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.warning(f"Nie udało się pobrać danych rynkowych: {e}")
        return None
