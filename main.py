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
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200

# === DEXSCREENER SCANNER ===
def scan_dexscreener_tokens():
    logger.info("Scanning Dexscreener tokens...")
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"

    try:
        res = requests.get(url)
        data = res.json()
        pairs = data.get("pairs", [])

        for token in pairs:
            addr = token.get("pairAddress")
            if not addr or addr in POSTED_TOKENS:
                continue

            base_token = token.get("baseToken", {})
            name = base_token.get("name", "Unknown")
            symbol = base_token.get("symbol", "???")
            price_usd = float(token.get("priceUsd") or 0)
            volume = float(token.get("volume", {}).get("h24") or 0)
            liquidity = float(token.get("liquidity", {}).get("usd") or 0)
            mc = float(token.get("fdv") or 0)
            age = int((time.time() - token.get("pairCreatedAt", 0) / 1000) / 60)

            if MIN_VOLUME_USD <= volume <= MAX_VOLUME_USD and 0 < age <= 60:
                msg = (
                    f"🔔*{name}* | {symbol}\n"
                    f"`{addr}`\n\n"
                    f"🧢 Marketcap: ${mc:,.0f}\n"
                    f"⏱️ Age: {age}m\n\n"
                    f"🧑‍💻 Dev: Not Available\n"
                    f"👥 Holders: N/A\n"
                    f"🔝 Top 10 holders: N/A\n"
                    f"🚀 Volume: ${volume:,.0f}\n\n"
                    f"🏛️ Platform: Dexscreener\n"
                    f"💧 Liquidity: ${liquidity:,.0f}\n"
                    f"📊 Bonding Curve: N/A\n\n"
                    f"🌍 Socials ↴\n\n"
                    f"🐦 X profile\n"
                    f"📝 X post\n"
                    f"🔍 X community\n\n"
                    f"🤺 Similar tokens (24h)\n"
                    f" └ 0 Name |  0 Symbol\n"
                    f"🕛 M5\n├ M: N/A\n├ T: N/A\n└ V: N/A\n"
                    f"🕐 H1\n├ M: N/A\n├ T: N/A\n└ V: N/A\n"
                    f"🕑 H6\n├ M: N/A\n├ T: N/A\n└ V: N/A\n"
                    f"🕒 H24\n├ M: N/A\n├ T: N/A\n└ V: N/A\n"
                    f"(M)akers, (T)rades, (V)olume\n"
                    f"🔎 Search X&src=typed_query): **CA** | **Name** | **Symbol**\n\n"
                    f"🔗 Partners:\n- [Trojan](https://t.me/agamemnon_trojanbot?start=r-bigfave_001)\n- [GMGNAI](https://t.me/gmgnaibot?start=i_QCOzrSSn)\n- [Axiom](http://axiom.trade/@bigfave00)\n\nGamble Play, NFA, DYOR"
                )
                if send_telegram_message(msg):
                    POSTED_TOKENS[addr] = {
                        "price": price_usd,
                        "mc": mc,
                        "time": time.time(),
                        "symbol": symbol,
                        "name": name
                    }
                    logger.info(f"Posted token: {symbol}")

    except Exception as e:
        logger.error(f"Error fetching Dexscreener tokens: {e}")

# === MULTIPLIER ALERTS ===
def check_multipliers():
    for addr, tracked in POSTED_TOKENS.items():
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{addr}"
            res = requests.get(url)
            data = res.json()
            current_price = float(data.get("pair", {}).get("priceUsd") or 0)
            original_price = tracked["price"]

            for x in [2, 3, 4]:
                if current_price >= x * original_price and f"{x}x" not in tracked:
                    send_telegram_message(
                        f"🚀 *{tracked['symbol']}* just hit *{x}x*! Current Price: ${current_price:.6f}"
                    )
                    tracked[f"{x}x"] = True
        except:
            continue

# === WEEKLY SUMMARY ===
def send_weekly_summary():
    sorted_tokens = sorted(
        POSTED_TOKENS.items(),
        key=lambda item: item[1].get("price", 0),
        reverse=True
    )
    top_tokens = sorted_tokens[:5]
    message = "📈 *Weekly Top Performers:*\n"
    for i, (addr, data) in enumerate(top_tokens, start=1):
        name = data.get("name")
        symbol = data.get("symbol")
        message += f"{i}. {name} ({symbol})\n"
    send_telegram_message(message)
    summary_timer = threading.Timer(7 * 24 * 60 * 60, send_weekly_summary)
    summary_timer.start()

# === LOOP ===
def main_loop():
    while True:
        scan_dexscreener_tokens()
        check_multipliers()
        time.sleep(120)

# === FLASK UPTIME ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems Bot is alive! 🔥"

# === START ===
def main():
    threading.Thread(target=main_loop).start()
    send_weekly_summary()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    main()
    app.run(host="0.0.0.0", port=port)