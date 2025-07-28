import os
import time
import threading
import datetime
import requests
import logging
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode
import asyncio

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Track posted tokens
posted_tokens = {}

# Async helper
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def fetch_tokens():
    url = f"https://api.helius.xyz/v1/mintlist?api-key={HELIUS_API_KEY}"
    payload = {
        "query": {
            "types": ["token"],
            "conditions": [
                {"field": "created_at", "operator": ">", "value": int(time.time()) - 3600},
            ]
        },
        "limit": 10
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"Unexpected response from Helius: {res.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching tokens: {e}")
        return []

def create_token_message(token):
    mint = token.get("mint")
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "N/A")
    marketcap = token.get("marketcap", "N/A")
    age = token.get("age", "N/A")
    dev = token.get("dev", "N/A")
    holders = token.get("holders", "N/A")
    top_holders = token.get("top_holders", "N/A")
    volume = token.get("volume", "N/A")
    platform = token.get("platform", "Solana")
    liquidity = token.get("liquidity", "N/A")
    bonding = token.get("bonding_curve", "N/A")
    socials = token.get("socials", "N/A")

    dexscreener_link = f"https://dexscreener.com/solana/{mint}"

    return f"""
🔔 <b>{name}</b> | <b>{symbol}</b>
<code>{mint}</code>

🧢 <b>Marketcap:</b> {marketcap}
⏱️ <b>Age:</b> {age}
🧑‍💻 <b>Dev:</b> {dev}
👥 <b>Holders:</b> {holders}
🔝 <b>Top 10 holders:</b> {top_holders}
🚀 <b>Volume:</b> {volume}
🏛️ <b>Platform:</b> {platform}
💧 <b>Liquidity:</b> {liquidity}
📊 <b>Bonding Curve:</b> {bonding}
🌍 <b>Socials:</b> {socials}
📈 <a href='{dexscreener_link}'>Dexscreener Chart</a>

<b>Play carefully, NFA, DYOR</b> 🧠

🔥 Trojan Sniper: https://t.me/agamemnon_trojanbot?start=r-bigfave_001
🚀 GMGNAI Sniper: https://t.me/gmgnaibot?start=i_QCOzrSSn
📊 Axiom Trade: http://axiom.trade/@bigfave00

<b>If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.</b>
"""

async def post_tokens():
    while True:
        logger.info("Scanning tokens from Helius...")
        tokens = fetch_tokens()
        now = datetime.datetime.utcnow()

        for token in tokens:
            mint = token.get("mint")
            if not mint:
                continue
            if mint not in posted_tokens:
                message = create_token_message(token)
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
                posted_tokens[mint] = {
                    "time": now,
                    "mc": token.get("marketcap", 0),
                    "2x": False,
                    "3x": False,
                    "4x": False
                }

            # Simulate live MC for now
            current_mc = posted_tokens[mint]["mc"] * 1.1

            if not posted_tokens[mint]["2x"] and current_mc >= 2 * posted_tokens[mint]["mc"]:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=f"🔥 <b>{token.get('name')}</b> just hit <b>2x!</b>", parse_mode=ParseMode.HTML)
                posted_tokens[mint]["2x"] = True
            if not posted_tokens[mint]["3x"] and current_mc >= 3 * posted_tokens[mint]["mc"]:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=f"🚀 <b>{token.get('name')}</b> just hit <b>3x!</b>", parse_mode=ParseMode.HTML)
                posted_tokens[mint]["3x"] = True
            if not posted_tokens[mint]["4x"] and current_mc >= 4 * posted_tokens[mint]["mc"]:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=f"💎 <b>{token.get('name')}</b> just hit <b>4x!</b>", parse_mode=ParseMode.HTML)
                posted_tokens[mint]["4x"] = True

        await asyncio.sleep(60)

def run_async_loop():
    loop.run_until_complete(post_tokens())

@app.route("/")
def home():
    return "<h2>✅ Zeus Gems Bot is Live</h2>"

if __name__ == "__main__":
    threading.Thread(target=run_async_loop).start()
    app.run(host="0.0.0.0", port=10000)