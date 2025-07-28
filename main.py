import os
import requests
import time
import logging
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from telegram import Bot

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("CHANNEL_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
posted_tokens = {}
performance_log = {}

def format_token_message(token, mc, age_min, liquidity, volume):
    dex_url = f"https://dexscreener.com/solana/{token['mint']}"
    return f"""
🔔 {token['name']} | {token['symbol']}
{token['mint']}

🧢 Marketcap: ${mc:,.0f}
⏱️ Age: {age_min}m

🧑‍💻 Dev: {token.get('owner', 'N/A')[:5]}...{token.get('owner', 'N/A')[-5:]} (💰 0%)
👥 Holders: {token.get('holders', 0)}
🔝 Top 10 holders: {token.get('top10', 0)}%
🚀 Volume: ${volume:,.0f}

🏛️ Platform: {token.get('platform', 'Unknown')}
💧 Liquidity: ${liquidity:,.0f}
📊 Bonding Curve: {token.get('curve', 0)}%

🌍 Socials ↴
🐦 X profile
📝 X post
🔍 X community

📈 [View on Dexscreener]({dex_url})

🔗 Referrals:
• [Trojan Sniper](https://t.me/agamemnon_trojanbot?start=r-bigfave_001)
• [GMGNAI Intel](https://t.me/gmgnaibot?start=i_QCOzrSSn)
• [Axiom DEX](http://axiom.trade/@bigfave00)

Gamble Play, NFA, DYOR
"""

def fetch_new_tokens():
    url = f"https://api.helius.xyz/v0/token-metadata?api-key={HELIUS_API_KEY}"
    now = datetime.utcnow()
    cutoff_time = now - timedelta(minutes=60)
    
    # Dummy mint list for demo (replace with real discovered mints)
    mint_list = ["So11111111111111111111111111111111111111112"]  # Add real tokens here

    headers = {"accept": "application/json", "content-type": "application/json"}
    body = {"mintAccounts": mint_list}
    try:
        response = requests.post(url, headers=headers, json=body)
        data = response.json()
        return data
    except Exception as e:
        logging.error(f"Error fetching Helius tokens: {e}")
        return []

def post_tokens():
    while True:
        logging.info("Scanning tokens from Helius...")
        tokens = fetch_new_tokens()
        for token in tokens:
            mint = token["mint"]
            if mint in posted_tokens:
                continue

            mc = token.get("marketCap", 30000)
            volume = token.get("volume", 60000)
            liquidity = token.get("liquidity", 20000)
            created_at = datetime.utcnow() - timedelta(minutes=token.get("age", 2))
            age_min = int((datetime.utcnow() - created_at).total_seconds() / 60)

            if 50000 <= volume <= 200000 and liquidity > 10000 and mc > 30000:
                message = format_token_message(token, mc, age_min, liquidity, volume)
                bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode="Markdown", disable_web_page_preview=False)

                posted_tokens[mint] = {
                    "initial_mc": mc,
                    "current_mc": mc,
                    "last_update": time.time()
                }
                performance_log[mint] = {"name": token["name"], "mc": mc}

        check_performance_updates()
        time.sleep(300)

def check_performance_updates():
    for mint, info in posted_tokens.items():
        try:
            url = f"https://api.helius.xyz/v0/token-metadata?api-key={HELIUS_API_KEY}"
            headers = {"accept": "application/json", "content-type": "application/json"}
            body = {"mintAccounts": [mint]}
            response = requests.post(url, headers=headers, json=body)
            data = response.json()

            if data and isinstance(data, list):
                current_mc = data[0].get("marketCap", 0)
                multiplier = current_mc / info["initial_mc"]

                alert_msg = None
                if multiplier >= 4 and info.get("last_alert") != "4x":
                    alert_msg = f"🚨 {data[0]['name']} just hit **4x** from its original MC!"
                    posted_tokens[mint]["last_alert"] = "4x"
                elif multiplier >= 3 and info.get("last_alert") != "3x":
                    alert_msg = f"🚨 {data[0]['name']} just hit **3x**!"
                    posted_tokens[mint]["last_alert"] = "3x"
                elif multiplier >= 2 and info.get("last_alert") != "2x":
                    alert_msg = f"🚨 {data[0]['name']} just hit **2x**!"
                    posted_tokens[mint]["last_alert"] = "2x"

                if alert_msg:
                    bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=alert_msg)
        except Exception as e:
            logging.error(f"Performance check failed for {mint}: {e}")

def send_weekly_summary():
    while True:
        now = datetime.utcnow()
        if now.weekday() == 6 and now.hour == 18:
            summary = "📊 Weekly Token Summary:\n\n"
            sorted_perf = sorted(performance_log.items(), key=lambda x: x[1]["mc"], reverse=True)
            top = sorted_perf[:5]
            for mint, data in top:
                summary += f"- {data['name']}: ${data['mc']:,.0f} MC\n"
            bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=summary)
            time.sleep(86400)
        else:
            time.sleep(3600)

@app.route('/')
def home():
    return "Zeus Gems Bot is live!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    Thread(target=post_tokens).start()
    Thread(target=send_weekly_summary).start()