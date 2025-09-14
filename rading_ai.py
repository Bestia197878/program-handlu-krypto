import ccxt
import pandas as pd
import numpy as np
import time
import json
import logging
import os
import ta
import requests
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import tweepy
import praw
from stable_baselines3 import DQN, PPO
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from utils import api, risk_management, data_processing, ai_models

with open('config/config.json') as f:
    config = json.load(f)

os.makedirs(os.path.dirname(config['log_file']), exist_ok=True)
logging.basicConfig(
    filename=config['log_file'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'enableRateLimit': True,
    'urls': {
        'api': {
            'public': 'https://testnet.binance.vision/api/v3',
            'private': 'https://testnet.binance.vision/api/v3'
        }
    }
})
logger.info("✅ Połączono z Binance Testnet")

try:
    tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    logger.info("✅ Agent sentimentu (LLM) załadowany pomyślnie")
except Exception as e:
    logger.error(f"❌ Błąd ładowania agenta sentimentu: {str(e)}")
    raise

try:
    trading_agent = ai_models.load_trading_agent(config['trading_agent_path'])
    logger.info("✅ Agent handlowy (RL) załadowany pomyślnie")
except Exception as e:
    logger.error(f"❌ Błąd ładowania agenta handlowego: {str(e)}")
    raise

try:
    risk_agent = ai_models.load_risk_agent(config['risk_agent_path'])
    logger.info("✅ Agent ryzyka (RL) załadowany pomyślnie")
except Exception as e:
    logger.error(f"❌ Błąd ładowania agenta ryzyka: {str(e)}")
    raise

try:
    monitoring_agent = ai_models.load_monitoring_agent(config['monitoring_agent_path'])
    logger.info("✅ Agent monitorujący (RL) załadowany pomyślnie")
except Exception as e:
    logger.error(f"❌ Błąd ładowania agenta monitorującego: {str(e)}")
    raise

twitter_client = None
if config.get('twitter_bearer_token'):
    try:
        twitter_client = tweepy.Client(bearer_token=config['twitter_bearer_token'])
        logger.info("✅ Twitter API połączony")
    except Exception as e:
        logger.error(f"❌ Błąd Twitter API: {str(e)}")

reddit_client = None
if all([config.get('reddit_client_id'), config.get('reddit_client_secret'), config.get('reddit_user_agent')]):
    try:
        reddit_client = praw.Reddit(
            client_id=config['reddit_client_id'],
            client_secret=config['reddit_client_secret'],
            user_agent=config['reddit_user_agent']
        )
        logger.info("✅ Reddit API połączony")
    except Exception as e:
        logger.error(f"❌ Błąd Reddit API: {str(e)}")

def main():
    logger.info("🚀 Start systemu AI Handlu Krypto (Testnet)")
    trade_history = []
    last_model_reset = datetime.now()
    
    if os.path.exists(config['drawdown_save_file']):
        with open(config['drawdown_save_file'], 'r') as f:
            state = json.load(f)
            peak_portfolio = state['peak_portfolio']
            last_portfolio = state['last_portfolio']
    else:
        peak_portfolio = 10000.0
        last_portfolio = 10000.0
    
    while True:
        try:
            print("\n" + "="*50)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            balance = exchange.fetch_balance()
            quote_currency = config['symbol'].split('/')[1]
            base_currency = config['symbol'].split('/')[0]
            current_portfolio = (
                balance[base_currency]['free'] * exchange.fetch_ticker(config['symbol'])['last'] +
                balance[quote_currency]['free']
            )
            
            logger.info(f"📊 Portfel: {balance[base_currency]['free']} {base_currency} | {balance[quote_currency]['free']} {quote_currency}")
            logger.info(f"💰 Aktualna wartość portfela: ${current_portfolio:.2f}")
            
            if current_portfolio > peak_portfolio:
                peak_portfolio = current_portfolio
                
            drawdown = (peak_portfolio - current_portfolio) / peak_portfolio
            logger.info(f"📉 Drawdown: {drawdown:.2%}")
            
            if drawdown > config['max_drawdown_percent'] / 100:
                alert_msg = f"🚨 DRAWDOWN PRZEKROCZONY! {drawdown:.2%} > {config['max_drawdown_percent']}%"
                logger.critical(alert_msg)
                api.send_alert(alert_msg)
                
                with open(config['drawdown_save_file'], 'w') as f:
                    json.dump({
                        'peak_portfolio': peak_portfolio,
                        'last_portfolio': current_portfolio
                    }, f)
                
                time.sleep(86400)
                sys.exit(1)
            
            if datetime.now().minute % 10 == 0:
                with open(config['drawdown_save_file'], 'w') as f:
                    json.dump({
                        'peak_portfolio': peak_portfolio,
                        'last_portfolio': current_portfolio
                    }, f)
            
            if (datetime.now() - last_model_reset).days > config['model_reset_days']:
                logger.info("🔄 Resetowanie modelu...")
                last_model_reset = datetime.now()
                logger.info("✅ Model został zresetowany")
            
            df = data_processing.get_market_data()
            if df is None or len(df) < 50:
                logger.error("❌ Brak wystarczających danych do analizy")
                time.sleep(config['sleep_seconds'])
                continue
            
            texts = []
            texts.extend(api.fetch_news())
            texts.extend(api.fetch_tweets())
            texts.extend(api.fetch_reddit_posts())
            sentiment = ai_models.analyze_sentiment(texts)
            
            risk_params = risk_management.get_risk_parameters(config)
            new_risk = risk_management.manage_system_parameters(trade_history, df, sentiment, risk_agent)
            risk_params['risk_percent'] = new_risk
            
            monitoring_agent = ai_models.monitor_system_health(monitoring_agent, df, trade_history)
            
            decision = ai_models.make_trading_decision(trade_history, df, sentiment, risk_params, trading_agent)
            logger.info(f"💡 Decyzja: {decision}")
            
            if decision in ["BUY", "SELL"]:
                current_price = exchange.fetch_ticker(config['symbol'])['last']
                amount = risk_management.calculate_position_size(decision, current_price, trade_history, risk_params)
                if amount > 0:
                    api.execute_trade(decision, amount, trade_history, current_price)
                else:
                    logger.warning("❌ Nie wykonano transakcji - nieprawidłowy rozmiar pozycji")
            
            sleep_time = config['sleep_seconds']
            logger.info(f"⏳ Czekam {sleep_time} sekund przed kolejną decyzją")
            time.sleep(sleep_time)
            
        except Exception as e:
            error_msg = f"❌ BŁĄD KRYTYCZNY: {str(e)}"
            logger.critical(error_msg)
            api.send_alert(error_msg)
            time.sleep(60)

if __name__ == "__main__":
    main()