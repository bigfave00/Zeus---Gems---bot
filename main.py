import requests
import time
import threading
from datetime import datetime
from flask import Flask
import os
import logging

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHANNEL_ID = "@yourchannelusername"

MIN_VOLUME_USD = 50000
MAX_VOLUME_USD = 200000
POSTED_TOKENS = {}

# === LOGGER ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# === TELEGRAM FUNCTION ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

# === GMGNAI SCANNER ===
def scan_gmg_tokens():
    logger.info("Scanning GMGNAI tokens...")
    try:
        res = requests.get("https://api.gmg.ai/api/public/tokens")
        tokens = res.json().get("tokens", [])

        for token in tokens:
            addr = token.get("mint")
            if not addr or addr in POSTED_TOKENS:
                continue

            volume = token.get("volume24h", 0)
            age_minutes = token.get("age", 999999) / 60  # assuming age in seconds

            if MIN_VOLUME_USD <= volume <= MAX_VOLUME_USD and 0 < age_minutes <= 60:
                name = token.get("name", "Unknown")
                symbol = token.get("symbol", "???")
                price = token.get("price", 0)
                mc = token.get("marketcap", 0)
                liquidity = token.get("liquidity", 0)
                dev = token.get("creator", "???")
                holders = token.get("holders", 0)
                top10 = token.get("top10Holders", "?")
                bonding = token.get("bondingCurve", "?")
                platform = token.get("platform", "?")
                link = f"https://gmg.ai/token/{addr}"

                msg = (
                    f"🔔 *{name.upper()}* | {symbol.upper()}\n"
                    f"{addr}\n\n"
                    f"🧢 Marketcap: ${mc:,.0f}\n"
                    f"⏱️ Age: {int(age_minutes)}m\n\n"
                    f"🧑‍💻 Dev: {dev[:5]}...{dev[-5:]} (💰 0%)\n"
                    f"👥 Holders: {holders}\n"
                    f"🔝 Top 10 holders: {top10}%\n"
                    f"🚀 Volume: ${volume:,.0f}\n\n"
                    f"🏛️ Platform: {platform}\n"
                    f"💧 Liquidity: ${liquidity:,.0f}\n"
                    f"📊 Bonding Curve: {bonding}%\n\n"
                    f"🌍 Socials ↴\n\n"
                    f"🐦 X profile\n\n"
                    f"📝 X post\n\n"
                    f"🔍 X community\n\n"
                    f"🤺 Similar tokens (24h)\n └ 0 Name |  0 Symbol\n"
                    f"🕛 M5\n├ M: 213 🅑 64.94%\n├ T: 439 🅑 48.52%\n└ V: 44.34K 🅑 62.73%\n"
                    f"🕐 H1\n├ M: 213 🅑 64.94%\n├ T: 439 🅑 48.52%\n└ V: 44.34K 🅑 62.73%\n"
                    f"🕑 H6\n├ M: 183 🅑 65.36%\n├ T: 373 🅑 49.06%\n└ V: 38.99K 🅑 63.71%\n"
                    f"🕒 H24\n├ M: 181 🅑 65.11%\n├ T: 371 🅑 48.79%\n└ V: 38.88K 🅑 63.6%\n\n"
                    f"(M)akers, (T)rades, (V)olume\n"
                    f"🔎 Search X: **CA** | **{name}** | **{symbol}**\n\n"
                    f"Gamble Play, NFA, DYOR\n\n"
                    f"[View Token 🔗]({link})\n\n"
                    f"👑 *Top Tools:*\n🐺 [Trojan] (https://t.me/agamemnon_trojanbot?start=r-bigfave_001)\n🤖 [GMGNAI] (https://t.me/gmgnaibot?start=i_QCOzrSSn)\n📈 [Axiom] (http://axiom.trade/@bigfave00)"
                )

                if send_telegram_message(msg):
                    POSTED_TOKENS[addr] = {
                        "price": price,
                        "time": time.time(),
                        "mc": mc
                    }
                    logger.info(f"Posted token: {symbol}")

    except Exception as e:
        logger.error(f"Error fetching GMG tokens: {e}")

# === LOOP ===
def main_loop():
    while True:
        scan_gmg_tokens()
        time.sleep(120)  # Every 2 minutes

# === UPTIMEROBOT FLASK SERVER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems GMG Bot is alive! 🔥"

# === START ===
def main():
    threading.Thread(target=main_loop).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    main()
    app.run(host="0.0.0.0", port=port)