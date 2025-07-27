import os
import requests
import time
import logging
from datetime import datetime, timezone
from telegram import Bot
from flask import Flask
import threading

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL = "@zeusgemscalls"
HELIUS_API_KEY = os.getenv("HELIUS_KEY")

# === FILTER SETTINGS ===
MIN_VOLUME = 200_000  # USD

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def shorten(address):
    return address[:6] + "..." + address[-4:]

def fetch_new_tokens():
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}&limit=50"
    try:
        res = requests.get(url)
        tokens = res.json()
        return tokens
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []

def passes_filters(token):
    try:
        if float(token.get("volumeUsd", 0)) < MIN_VOLUME:
            return False
        if not token.get("liquidityLocked", False):
            return False
        if not token.get("renounced", False):
            return False
        if token.get("canMint", True):
            return False
        return True
    except:
        return False

def build_message(token):
    name = token.get("name", "N/A")
    symbol = token.get("symbol", "N/A")
    address = token.get("address", "N/A")
    mc = f"${int(token.get('marketCapUsd', 0)):,}"
    age = token.get("age", "N/A")
    volume = f"${int(token.get('volumeUsd', 0)):,}"
    liquidity = f"${int(token.get('liquidityUsd', 0)):,}"
    dev = shorten(token.get("creator", "N/A"))
    dev_pct = token.get("creatorHoldPercent", 0)
    holders = token.get("holders", 0)
    top10 = token.get("top10HoldersPercent", 0)
    bonding = round(token.get("bondingCurvePct", 0), 2)
    platform = token.get("source", "Pump.fun")
    chart = f"https://dexscreener.com/solana/{address}"
    website = token.get("website", "N/A")
    twitter = token.get("twitter", "N/A")

    msg = f"""🔔 Zeus Gems | 🚀 {name} ({symbol})
`{address}`

🧂 Marketcap: {mc}
⏱️ Age: {age}
🚀 Volume: {volume}
💧 Liquidity: {liquidity} ✅ Locked

🧑‍💻 Dev: `{dev}` (💰 {dev_pct}%)
👥 Holders: {holders}
🔝 Top 10 Holders: {top10}%
📉 Bonding Curve: {bonding}%
🏧 Platform: {platform}

📊 [Chart on Dexscreener]({chart})

🌍 Website: {website}
🔦 Twitter: {twitter}

📲 Snipe with bots:
• [Trojan](https://t.me/trojanbot)
• [GMGNAI](https://t.me/gmgnai_bot)
• [Axiom](https://t.me/axiom_sol_bot)

⚠️ Ownership renounced, mint revoked, name frozen
Gamble play, NFA, DYOR"""
    
    return msg

def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.error("BOT_TOKEN not found in environment variables")
        return

    if not HELIUS_API_KEY:
        logging.error("HELIUS_KEY not found in environment variables")
        return

    posted = set()

    logging.info("Zeus Gems Bot starting...")

    while True:
        try:
            logging.info("Checking tokens...")
            tokens = fetch_new_tokens()

            for token in tokens:
                if not isinstance(token, dict):
                    continue

                addr = token.get("address")
                if addr in posted:
                    continue

                if passes_filters(token):
                    msg = build_message(token)
                    try:
                        bot.send_message(
                            chat_id=TELEGRAM_CHANNEL,
                            text=msg,
                            parse_mode='Markdown',
                            disable_web_page_preview=False
                        )
                        posted.add(addr)
                        logging.info(f"Posted: {addr}")
                    except Exception as e:
                        logging.error(f"Failed to post: {e}")

            time.sleep(60)

        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(60)

# === RENDER FIX ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Zeus Gems Bot is running!"

    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=port)
