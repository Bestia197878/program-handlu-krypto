import requests
import ccxt
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger()

def fetch_with_retry(func, max_retries=5, initial_delay=1):
    for i in range(max_retries):
        try:
            return func()
        except ccxt.BaseError as e:
            if "rate limit" in str(e).lower() or e.code == 429:
                delay = initial_delay * (2 ** i)
                logger.warning(f"⚠️ Osiągnięto limit API - czekam {delay} sekund")
                time.sleep(delay)
            else:
                raise
    raise Exception("Przekroczono maksymalną liczbę prób")

def fetch_news():
    if not os.getenv('NEWSAPI_KEY'):
        return []
    try:
        url = f"https://newsapi.org/v2/everything?q=bitcoin&apiKey={os.getenv('NEWSAPI_KEY')}"
        response = requests.get(url)
        articles = response.json().get('articles', [])
        return [article['title'] + ' ' + article['description'] for article in articles[:5]]
    except Exception as e:
        logger.error(f"❌ NewsAPI error: {str(e)}")
        return []

def fetch_tweets():
    if not os.getenv('TWITTER_BEARER_TOKEN'):
        return []
    try:
        client = tweepy.Client(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
        tweets = client.search_recent_tweets(query="bitcoin", max_results=10, tweet_fields=['text'])
        return [tweet.text for tweet in tweets.data] if tweets.data else []
    except Exception as e:
        logger.error(f"❌ Twitter error: {str(e)}")
        return []

def fetch_reddit_posts():
    if not all([os.getenv('REDDIT_CLIENT_ID'), os.getenv('REDDIT_CLIENT_SECRET'), os.getenv('REDDIT_USER_AGENT')]):
        return []
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        subreddit = reddit.subreddit('bitcoin')
        posts = subreddit.search("bitcoin", limit=10)
        return [post.title + ' ' + post.selftext for post in posts]
    except Exception as e:
        logger.error(f"❌ Reddit error: {str(e)}")
        return []

def send_alert(message):
    try:
        if os.getenv('SENDGRID_API_KEY') and os.getenv('ALERT_EMAIL'):
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
                "Content-Type": "application/json"
            }
            payload = {
                "personalizations": [{
                    "to": [{"email": os.getenv('ALERT_EMAIL')}]
                }],
                "from": {"email": "system@example.com"},
                "subject": "ALERT: System Handlu Krypto",
                "content": [{"type": "text/plain", "value": message}]
            }
            requests.post(url, headers=headers, json=payload)
        
        if os.getenv('SLACK_WEBHOOK_URL'):
            payload = {
                "text": f"🚨 *Crypto Trading Alert*\n```{message}```",
                "mrkdwn": True
            }
            requests.post(os.getenv('SLACK_WEBHOOK_URL'), json=payload)
            
        if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
            url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
            payload = {
                "chat_id": os.getenv('TELEGRAM_CHAT_ID'),
                "text": f"🚨 *Crypto Trading Alert*\n```{message}```",
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload)
            
        logger.info(f"🔔 Alert wysłany: {message}")
    except Exception as e:
        logger.error(f"❌ Błąd wysyłania alertu: {str(e)}")

def execute_trade(action, amount, trade_history, current_price):
    try:
        if amount <= 0:
            logger.warning("❌ Nie wykonano transakcji - rozmiar 0")
            return False
            
        min_size = get_min_order_size()
        if amount < min_size:
            logger.warning(f"⚠️ Rozmiar {amount} mniejszy niż minimalny {min_size}")
            return False
            
        if action == 'buy':
            order = exchange.create_market_buy_order('BTC/USDT', amount)
            logger.info(f"✅ Kupiono {amount} BTC za {order['cost']} USDT")
            trade_history.append({
                'action': 'buy',
                'entry_price': current_price,
                'amount': amount,
                'cost': order['cost'],
                'timestamp': datetime.now()
            })
        elif action == 'sell':
            order = exchange.create_market_sell_order('BTC/USDT', amount)
            logger.info(f"✅ Sprzedano {amount} BTC za {order['cost']} USDT")
            last_buy = next((t for t in trade_history if t['action'] == 'buy' and not t.get('sold', False)), None)
            if last_buy:
                profit = (order['cost'] - last_buy['cost'])
                trade_history[-1]['sold'] = True
                trade_history[-1]['profit'] = profit
        else:
            logger.info("➡️ Trzymanie pozycji")
            return True
            
        order_status = exchange.fetch_order(order['id'], 'BTC/USDT')
        if order_status['status'] != 'closed':
            logger.warning(f"⚠️ Zamówienie nie zostało zamknięte: {order_status['status']}")
            return False
            
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "insufficient" in error_msg.lower():
            logger.error(f"❌ Niewystarczające środki: {error_msg}")
        elif "rate limit" in error_msg.lower():
            logger.error(f"❌ Osiągnięto limit API: {error_msg}")
            time.sleep(60)
        else:
            logger.error(f"❌ Błąd transakcji: {error_msg}")
        return False