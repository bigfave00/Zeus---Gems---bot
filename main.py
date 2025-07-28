import requests
import time
import threading
import datetime
import logging
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

bot = Bot(token=BOT_TOKEN)

posted_tokens = {}
performance_data = {}

# Referral Links
REF_LINKS = (
    "\n\n🤖 *Partner Bots:*\n"
    "🔹 [Trojan Sniper](https://t.me/agamemnon_trojanbot?start=r-bigfave_001)\n"
    "🔹 [GMGNAI](https://t.me/gmgnaibot?start=i_QCOzrSSn)\n"
    "🔹 [Axiom](http://axiom.trade/@bigfave00)"
)

def format_token_message(token):
    mint = token.get("mint")
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "Unknown")
    mc = token.get("marketCap", 0)
    age = token.get("age", "?")
    dev = token.get("developer", "?")
    holders = token.get("holders", 0)
    top10 = token.get("top10Holders", "?")
    volume = token.get("volume", 0)
    platform = token.get("platform", "Solana")
    liquidity = token.get("liquidity", 0)
    bonding_curve = token.get("bondingCurve", "?")
    socials = token.get("socials", "None")

    dexscreener_link = f"https://dexscreener.com/solana/{mint}"

    return f"""
🔔 *{name} | {symbol}*
`{mint}`

🧢 *Marketcap:* ${mc:,.0f}
⏱️ *Age:* {age}
🧑‍💻 *Dev:* {dev}
👥 *Holders:* {holders}
🔝 *Top 10 holders:* {top10}
🚀 *Volume:* ${volume:,.0f}
🏛️ *Platform:* {platform}
💧 *Liquidity:* ${liquidity:,.0f}
📊 *Bonding Curve:* {bonding_curve}
🌍 *Socials:* {socials}

📈 [View on Dexscreener]({dexscreener_link})

🎲 *Gamble Play, NFA, DYOR* {REF_LINKS}

💡 *Bonus:* If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.
"""

def fetch_helius_tokens():
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Unexpected response from Helius: {response.text}")
    except Exception as e:
        logger.error(f"Error fetching tokens: {e}")
    return []

def post_tokens():
    while True:
        tokens = fetch_helius_tokens()
        if tokens:
            now = datetime.datetime.utcnow()
            for token in tokens:
                try:
                    mint = token["mint"]
                    if mint in posted_tokens:
                        continue

                    marketcap = token.get("marketCap", 0)
                    volume = token.get("volume", 0)
                    if 50000 <= volume <= 200000 and marketcap <= 300000:
                        message = format_token_message(token)
                        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN)
                        posted_tokens[mint] = {
                            "marketcap": marketcap,
                            "timestamp": now,
                            "name": token.get("name", "?"),
                            "symbol": token.get("symbol", "?")
                        }
                        performance_data[mint] = marketcap
                        logger.info(f"Posted token: {token.get('name')}")
                except Exception as e:
                    logger.error(f"Error posting token: {e}")
        time.sleep(60)

def check_performance():
    while True:
        for mint, data in posted_tokens.items():
            current_tokens = fetch_helius_tokens()
            for token in current_tokens:
                if token["mint"] == mint:
                    try:
                        current_mc = token.get("marketCap", 0)
                        original_mc = data["marketcap"]
                        if current_mc >= 4 * original_mc:
                            multiplier = "4x"
                        elif current_mc >= 3 * original_mc:
                            multiplier = "3x"
                        elif current_mc >= 2 * original_mc:
                            multiplier = "2x"
                        else:
                            continue
                        bot.send_message(chat_id=CHAT_ID,
                                         text=f"🔥 *{data['name']}* (${data['symbol']}) just hit *{multiplier}*! 🚀\n\n💰 Marketcap: ${current_mc:,.0f}",
                                         parse_mode=ParseMode.MARKDOWN)
                        logger.info(f"{data['name']} hit {multiplier}")
                        del posted_tokens[mint]  # Alert only once
                    except Exception as e:
                        logger.error(f"Error checking token {mint}: {e}")
        time.sleep(300)

def weekly_summary():
    while True:
        now = datetime.datetime.utcnow()
        if now.weekday() == 6 and now.hour == 18:  # Sunday 6pm UTC
            best_tokens = sorted(performance_data.items(), key=lambda x: x[1], reverse=True)[:5]
            summary = "📊 *Weekly Summary of Top Tokens*\n\n"
            for mint, mc in best_tokens:
                summary += f"🔹 `{mint}`: ${mc:,.0f}\n"
            summary += "\nKeep grinding. DYOR, NFA."
            bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode=ParseMode.MARKDOWN)
            time.sleep(3600)  # Wait an hour to avoid re-sending
        time.sleep(600)  # Check every 10 min

@app.route("/")
def home():
    return "Zeus Gems bot is live!"

if __name__ == '__main__':
    threading.Thread(target=post_tokens).start()
    threading.Thread(target=check_performance).start()
    threading.Thread(target=weekly_summary).start()
    app.run(host='0.0.0.0', port=10000)