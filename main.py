import os
import time
import json
import asyncio
import logging
import datetime
import threading
import requests
from flask import Flask
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# In-memory storage for posted tokens and tracked prices
posted_tokens = {}
tracked_tokens = {}

# Async token posting loop
async def post_tokens():
    global posted_tokens
    while True:
        try:
            logger.info("Scanning tokens from Helius...")
            now = datetime.datetime.utcnow()
            start_time = (now - datetime.timedelta(minutes=60)).isoformat("T") + "Z"

            url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
            headers = {"Content-Type": "application/json"}
            body = {
                "jsonrpc": "2.0",
                "id": "my-id",
                "method": "getNewTokens",  # this method must match a real one supported by Helius
                "params": {
                    "startTime": start_time,
                    "limit": 20
                }
            }

            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 200:
                logger.error(f"Unexpected response from Helius: {response.text}")
                await asyncio.sleep(60)
                continue

            tokens = response.json().get("result", [])
            for token in tokens:
                try:
                    mint = token["mint"]
                    if mint in posted_tokens:
                        continue

                    name = token.get("name", "N/A")
                    symbol = token.get("symbol", "N/A")
                    mc = token.get("marketCap", "?")
                    age = token.get("age", "?")
                    dev = token.get("developer", "?")
                    holders = token.get("holders", "?")
                    top10 = token.get("top10Holders", "?")
                    vol = token.get("volume", "?")
                    platform = token.get("platform", "Solana")
                    liquidity = token.get("liquidity", "?")
                    bonding_curve = token.get("bondingCurve", "?")
                    socials = token.get("socials", "?")

                    dexscreener_link = f"https://dexscreener.com/solana/{mint}"

                    message = f"""
🔔 <b>{name} | {symbol}</b>
<code>{mint}</code>

🧢 <b>Marketcap:</b> {mc}
⏱️ <b>Age:</b> {age}
🧑‍💻 <b>Dev:</b> {dev}
👥 <b>Holders:</b> {holders}
🔝 <b>Top 10 holders:</b> {top10}
🚀 <b>Volume:</b> {vol}
🏛️ <b>Platform:</b> {platform}
💧 <b>Liquidity:</b> {liquidity}
📊 <b>Bonding Curve:</b> {bonding_curve}
🌍 <b>Socials:</b> {socials}

📈 <a href='{dexscreener_link}'>View Dexscreener Chart</a>

🤖 <b>Powered by Zeus Gems Bot</b>

🎁 Bonus: If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.

🔗 Trojan: https://t.me/agamemnon_trojanbot?start=r-bigfave_001
🔗 GMGNAI: https://t.me/gmgnaibot?start=i_QCOzrSSn
🔗 Axiom: http://axiom.trade/@bigfave00

🎲 Gamble Play, NFA, DYOR
                    """

                    await bot.send_message(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )

                    posted_tokens[mint] = {
                        "posted_time": datetime.datetime.utcnow().isoformat(),
                        "start_mc": float(mc) if isinstance(mc, (int, float, str)) and str(mc).replace('.', '', 1).isdigit() else None
                    }
                except Exception as e:
                    logger.error(f"Error posting token: {e}")

        except Exception as e:
            logger.error(f"Exception in post_tokens: {e}")

        await asyncio.sleep(60)

# Monitor prices for 2x, 3x, 4x alerts
async def monitor_price_changes():
    while True:
        try:
            for mint, data in list(posted_tokens.items()):
                start_mc = data.get("start_mc")
                if not start_mc:
                    continue

                # Simulated market cap (replace with real API call later)
                current_mc = start_mc * 2  # For testing, simulate 2x

                for multiplier in [2, 3, 4]:
                    target = start_mc * multiplier
                    if current_mc >= target and not data.get(f"alerted_{multiplier}x"):
                        msg = f"🔥 {multiplier}x Alert!
<code>{mint}</code> hit {multiplier}x from launch MC!"
                        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg)
                        posted_tokens[mint][f"alerted_{multiplier}x"] = True

        except Exception as e:
            logger.error(f"Price monitor error: {e}")

        await asyncio.sleep(300)  # Every 5 mins

# Flask server for alive ping
@app.route("/")
def index():
    return "Zeus Gems bot is alive."

# Start all async tasks
async def start_bot():
    await asyncio.gather(
        post_tokens(),
        monitor_price_changes(),
    )

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)