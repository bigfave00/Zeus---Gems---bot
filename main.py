import os
import requests
import time
import threading
import logging
import datetime
from flask import Flask
from telegram import Bot

# Setup
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("CHANNEL_ID")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
posted_tokens = {}
performance_data = {}

# Simulated tokens for testing (replace this with real API logic)
def get_token_info():
    tokens = [
        {
            "mint": f"TestMint{i}",
            "name": f"Token{i}",
            "symbol": f"TKN{i}",
            "market_cap": 100_000 + i * 50000,
            "volume": 60000 + i * 10000,
            "liquidity": 20000 + i * 5000,
            "age_minutes": i * 15,
            "holders": 150 + i * 10,
            "top10": "90%",
            "bonding_curve": "Linear",
            "platform": "Solana"
        } for i in range(1, 4)
    ]
    return tokens

def format_message(token):
    mint = token["mint"]
    name = token["name"]
    symbol = token["symbol"]
    market_cap = token["market_cap"]
    volume = token["volume"]
    liquidity = token["liquidity"]
    age = token["age_minutes"]
    holders = token["holders"]
    top10 = token["top10"]
    bonding_curve = token["bonding_curve"]
    platform = token["platform"]
    dexscreener_link = f"https://dexscreener.com/solana/{mint}"

    message = f"""
🔔 <b>{name} | {symbol}</b>
<code>{mint}</code>
🧢 Marketcap: ${market_cap:,}
⏱️ Age: {age} minutes
🧑‍💻 Dev: Unknown
👥 Holders: {holders}
🔝 Top 10 holders: {top10}
🚀 Volume: ${volume:,}
🏛️ Platform: {platform}
💧 Liquidity: ${liquidity:,}
📊 Bonding Curve: {bonding_curve}
📈 Chart: <a href="{dexscreener_link}">Dexscreener</a>

👑 Trojan: <a href="https://t.me/agamemnon_trojanbot?start=r-bigfave_001">Click Here</a>
🤖 GMGNAI: <a href="https://t.me/gmgnaibot?start=i_QCOzrSSn">Click Here</a>
📉 Axiom: <a href="http://axiom.trade/@bigfave00">Click Here</a>

⚠️ Gamble Play, NFA, DYOR.

💎 <i>Zeus Gems Bot</i>
🧠 <b>If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.</b>
"""
    return message

def post_tokens():
    while True:
        logging.info("Scanning tokens from Helius...")
        tokens = get_token_info()
        now = datetime.datetime.utcnow()

        for token in tokens:
            mint = token["mint"]
            if mint not in posted_tokens:
                message = format_message(token)
                try:
                    bot.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    posted_tokens[mint] = {
                        "market_cap": token["market_cap"],
                        "timestamp": now
                    }
                    performance_data[mint] = {
                        "name": token["name"],
                        "symbol": token["symbol"],
                        "posted_cap": token["market_cap"],
                        "current_cap": token["market_cap"],
                        "times": []
                    }
                except Exception as e:
                    logging.error(f"Error sending message: {e}")

        time.sleep(300)

def check_performance():
    while True:
        for mint, data in performance_data.items():
            try:
                for x in [2, 3, 4]:
                    target = data["posted_cap"] * x
                    if x not in data["times"] and data["current_cap"] >= target:
                        alert = f"🔥 <b>{data['name']} ({data['symbol']}) just hit {x}x!</b>\n<code>{mint}</code>"
                        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=alert, parse_mode="HTML")
                        data["times"].append(x)
            except Exception as e:
                logging.error(f"Error checking performance: {e}")
        time.sleep(180)

def send_weekly_summary():
    while True:
        now = datetime.datetime.utcnow()
        if now.weekday() == 6 and now.hour == 20:  # Sunday 8PM UTC
            summary = "📊 <b>Weekly Zeus Gems Summary</b>\n\n"
            for mint, data in performance_data.items():
                summary += f"🔹 {data['name']} ({data['symbol']}) — Posted: ${data['posted_cap']:,}, Now: ${data['current_cap']:,}\n"
            bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=summary, parse_mode="HTML")
            time.sleep(3600 * 24)
        time.sleep(3600)

@app.route("/")
def home():
    return "Zeus Gems Bot is Live!"

if __name__ == "__main__":
    threading.Thread(target=post_tokens).start()
    threading.Thread(target=check_performance).start()
    threading.Thread(target=send_weekly_summary).start()
    app.run(host="0.0.0.0", port=10000)