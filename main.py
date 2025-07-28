import os
import json
import logging
import datetime
import asyncio
import threading
import requests
from flask import Flask
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(level=logging.INFO)

# Track tokens already posted
posted_tokens = {}

# Track multipliers already alerted
alerted_multipliers = {}

# Track all-time performance for weekly summary
performance_data = {}

# Get token metadata from Helius
async def fetch_tokens():
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAssetsByGroup",
        "params": {
            "groupKey": "collection",
            "groupValue": "tokens",
            "page": 1,
            "limit": 30
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        result = response.json()
        if "result" in result and "items" in result["result"]:
            return result["result"]["items"]
        else:
            logging.error("Unexpected response from Helius: %s", response.text)
    except Exception as e:
        logging.error("Error fetching Helius tokens: %s", e)
    return []

# Dexscreener API
async def get_token_data(mint):
    try:
        url = f"https://api.dexscreener.com/latest/dex/search/?q={mint}"
        response = requests.get(url)
        data = response.json()
        if data and "pairs" in data and len(data["pairs"]) > 0:
            return data["pairs"][0]
    except Exception as e:
        logging.warning("Error getting token data: %s", e)
    return None

# Async message sender
async def post_tokens():
    while True:
        logging.info("Scanning tokens from Helius...")
        tokens = await fetch_tokens()
        now = datetime.datetime.utcnow()

        for token in tokens:
            try:
                mint = token["id"]
                if mint in posted_tokens:
                    continue

                dexscreener_data = await get_token_data(mint)
                if not dexscreener_data:
                    continue

                pair_url = dexscreener_data.get("url", "N/A")
                price = float(dexscreener_data.get("priceUsd", 0))
                marketcap = float(dexscreener_data.get("fdv", 0))
                volume = float(dexscreener_data.get("volume", {}).get("h1", 0))
                liquidity = float(dexscreener_data.get("liquidity", {}).get("usd", 0))
                age = dexscreener_data.get("age", "N/A")

                message = f"""
🔔 <b>{dexscreener_data['baseToken']['name']} | {dexscreener_data['baseToken']['symbol']}</b>
<code>{mint}</code>

🧢 Marketcap: ${marketcap:,.0f}
⏱️ Age: {age}
🚀 Volume: ${volume:,.0f}
💧 Liquidity: ${liquidity:,.0f}
📊 Chart: <a href='{pair_url}'>Dexscreener</a>

💎 Gamble Play, NFA, DYOR

— Powered by Zeus Gems Bot
Trojan: https://t.me/agamemnon_trojanbot?start=r-bigfave_001
GMGNAI: https://t.me/gmgnaibot?start=i_QCOzrSSn
Axiom: http://axiom.trade/@bigfave00

<i>💬 Bonus: If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.</i>
"""
                await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)

                posted_tokens[mint] = {
                    "price": price,
                    "name": dexscreener_data['baseToken']['name']
                }
                alerted_multipliers[mint] = set()
                performance_data[mint] = {"name": dexscreener_data['baseToken']['name'], "price": price, "max": price}

            except Exception as e:
                logging.warning("Error posting token: %s", e)

        await asyncio.sleep(60)

# Price tracking and alerts
async def track_prices():
    while True:
        for mint, info in posted_tokens.items():
            try:
                data = await get_token_data(mint)
                if not data:
                    continue

                current_price = float(data.get("priceUsd", 0))
                original_price = info["price"]
                name = info["name"]

                # Update highest
                if mint in performance_data:
                    performance_data[mint]["max"] = max(performance_data[mint]["max"], current_price)

                # Calculate multiplier
                if original_price <= 0:
                    continue

                ratio = current_price / original_price
                next_x = int(ratio)

                for multiplier in range(2, next_x + 1):
                    if multiplier not in alerted_multipliers[mint]:
                        msg = f"🔥 {multiplier}x Alert!\n💎 {name} just hit {multiplier}x from when it was posted!"
                        await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                        alerted_multipliers[mint].add(multiplier)

            except Exception as e:
                logging.warning("Tracking error: %s", e)
        await asyncio.sleep(60)

# Weekly summary (placeholder)
async def send_weekly_summary():
    while True:
        try:
            summary = "<b>📈 Zeus Gems Weekly Summary</b>\n\n"
            for mint, stats in performance_data.items():
                x = stats["max"] / stats["price"] if stats["price"] > 0 else 0
                if x >= 2:
                    summary += f"💠 {stats['name']}: {x:.1f}x\n"

            if summary.strip() != "<b>📈 Zeus Gems Weekly Summary</b>":
                await bot.send_message(chat_id=CHANNEL_ID, text=summary, parse_mode="HTML")
        except Exception as e:
            logging.warning("Weekly summary error: %s", e)
        await asyncio.sleep(604800)  # 1 week

# Flask app for keep-alive
@app.route("/")
def home():
    return "<h2>Zeus Gems Bot is running! ✅</h2>"

def run_async_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(post_tokens())
    loop.create_task(track_prices())
    loop.create_task(send_weekly_summary())
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=run_async_tasks).start()
    app.run(host="0.0.0.0", port=10000)