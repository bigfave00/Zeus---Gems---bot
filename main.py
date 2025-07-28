import requests
import time
import threading
from datetime import datetime, timedelta
from flask import Flask
import os
import logging

# === CONFIGURATION ===
HELIUS_API_KEY = "your-helius-api-key"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHANNEL_ID = "@yourchannelusername"

MIN_VOLUME = 50000
MAX_VOLUME = 200000
POSTED_TOKENS = {}
PERFORMANCE_LOG = {}

# === LOGGER ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# === FLASK SERVER FOR UPTIMEROBOT ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems Bot is alive! 🔥"

# === SEND TELEGRAM MESSAGE ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload)
    return res.status_code == 200

# === FETCH NEW TOKENS FROM HELIUS ===
def fetch_tokens():
    logger.info("Scanning tokens from Helius...")
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}"
    headers = {"accept": "application/json"}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        if not isinstance(data, list):
            logger.error("Unexpected response from Helius.")
            return []

        return data
    except Exception as e:
        logger.error(f"Error fetching Helius tokens: {e}")
        return []

# === FORMAT TELEGRAM MESSAGE ===
def format_message(token):
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "???")
    address = token.get("token_address", "N/A")
    mc = token.get("market_cap", 0)
    volume = token.get("volume_24h", 0)
    liquidity = token.get("liquidity", 0)
    age = token.get("age_minutes", 0)
    holders = token.get("holders", "N/A")
    dev = token.get("creator", "N/A")
    top_holders = token.get("top10_holders_pct", "N/A")
    bonding = token.get("bonding_curve", "N/A")

    # Dexscreener link
    dexscreener_link = f"https://dexscreener.com/solana/{address}"

    # Referral links
    trojan = "https://t.me/agamemnon_trojanbot?start=r-bigfave_001"
    gmgnai = "https://t.me/gmgnaibot?start=i_QCOzrSSn"
    axiom = "http://axiom.trade/@bigfave00"

    msg = (
        f"🔔 *{name}* | {symbol}\n"
        f"`{address}`\n\n"
        f"🧢 Marketcap: ${int(mc):,}\n"
        f"⏱️ Age: {int(age)}m\n\n"
        f"🧑‍💻 Dev: {dev} (💰 0%)\n"
        f"👥 Holders: {holders}\n"
        f"🔝 Top 10 holders: {top_holders}%\n"
        f"🚀 Volume: ${int(volume):,}\n\n"
        f"🏛️ Platform: Launchlab\n"
        f"💧 Liquidity: ${int(liquidity):,}\n"
        f"📊 Bonding Curve: {bonding}%\n\n"
        f"📈 [View on Dexscreener]({dexscreener_link})\n\n"
        f"🎯 [Trojan Bot]({trojan}) | [GMGNAI]({gmgnai}) | [Axiom]({axiom})\n\n"
        f"_Gamble Play, NFA, DYOR_"
    )
    return msg

# === TRACK 2x/3x/4x TOKENS ===
def check_performance():
    for addr, info in POSTED_TOKENS.items():
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{addr}"
            res = requests.get(url)
            data = res.json()
            price = data.get("pair", {}).get("priceUsd", 0)
            if not price: continue
            price = float(price)
            original_price = info["price"]

            x_gain = round(price / original_price)
            if x_gain >= 2 and x_gain <= 4 and x_gain not in info["alerts"]:
                msg = f"🔥 ${info['symbol']} just hit *{x_gain}x* from original call!\n[View Chart](https://dexscreener.com/solana/{addr})"
                send_telegram_message(msg)
                info["alerts"].append(x_gain)
        except Exception as e:
            logger.error(f"Error checking performance for {addr}: {e}")

# === WEEKLY SUMMARY ===
def send_weekly_summary():
    if not PERFORMANCE_LOG:
        send_telegram_message("📊 No top tokens to summarize this week.")
        return

    summary = "*📈 Weekly Zeus Gems Summary:*\n"
    sorted_tokens = sorted(PERFORMANCE_LOG.items(), key=lambda x: x[1]["x"], reverse=True)
    for addr, info in sorted_tokens[:5]:
        summary += f"• {info['name']} | {info['symbol']} → {info['x']}x\n"

    send_telegram_message(summary)

# === MAIN SCANNER LOOP ===
def scanner_loop():
    while True:
        tokens = fetch_tokens()
        for token in tokens:
            address = token.get("token_address")
            volume = token.get("volume_24h", 0)
            age = token.get("age_minutes", 999)
            if not address or address in POSTED_TOKENS: continue
            if MIN_VOLUME <= volume <= MAX_VOLUME and age <= 60:
                message = format_message(token)
                sent = send_telegram_message(message)
                if sent:
                    POSTED_TOKENS[address] = {
                        "price": float(token.get("price_usd", 0.0001)),
                        "symbol": token.get("symbol", "???"),
                        "alerts": []
                    }
                    PERFORMANCE_LOG[address] = {
                        "name": token.get("name", ""),
                        "symbol": token.get("symbol", ""),
                        "x": 1
                    }
                    logger.info(f"Posted: {token.get('symbol')}")

        check_performance()

        # Weekly summary every Sunday 6pm UTC
        now = datetime.utcnow()
        if now.weekday() == 6 and now.hour == 18 and now.minute < 5:
            send_weekly_summary()

        time.sleep(120)

# === START BOT ===
def main():
    threading.Thread(target=scanner_loop).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    main()
    app.run(host="0.0.0.0", port=port)