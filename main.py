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

# === SETTINGS ===
MIN_VOLUME = 50_000
MAX_VOLUME = 200_000
MAX_AGE_SECONDS = 3600  # 1 hour

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Store posted tokens and their original market cap
posted = {}

# Store top performers for the week
top_performers = []

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

def get_token_age_seconds(launch_time):
    try:
        launch_dt = datetime.fromisoformat(launch_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - launch_dt).total_seconds()
    except:
        return float('inf')

def passes_filters(token):
    try:
        volume = float(token.get("volumeUsd", 0))
        age_seconds = get_token_age_seconds(token.get("timeCreated", ""))
        if not (MIN_VOLUME <= volume <= MAX_VOLUME):
            return False
        if age_seconds > MAX_AGE_SECONDS:
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
    mc = int(token.get("marketCapUsd", 0))
    mc_display = f"${mc:,}"
    age = token.get("age", "N/A")
    volume = f"${int(token.get('volumeUsd', 0)):,}"
    liquidity = f"${int(token.get('liquidityUsd', 0)):,}"
    dev = shorten(token.get("creator", "N/A"))
    dev_pct = token.get("creatorHoldPercent", 0)
    holders = token.get("holders", 0)
    top10 = token.get("top10HoldersPercent", 0)
    bonding = round(token.get("bondingCurvePct", 0), 2)
    platform = token.get("source", "N/A")
    chart = f"https://dexscreener.com/solana/{address}"
    website = token.get("website", "N/A")
    twitter = token.get("twitter", "N/A")

    msg = f"""🔔 Zeus Gems | 🚀 {name} ({symbol})
`{address}`

🧂 Marketcap: {mc_display}
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
    if not TELEGRAM_BOT_TOKEN or not HELIUS_API_KEY:
        logging.error("BOT_TOKEN or HELIUS_KEY missing!")
        return

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
                        mc = float(token.get("marketCapUsd", 0))
                        posted[addr] = mc
                        top_performers.append((token.get("name", "N/A"), mc))
                        logging.info(f"Posted token: {addr}")
                    except Exception as e:
                        logging.error(f"Failed to post: {e}")

            # Check for 2x/3x gains
            for addr, old_mc in posted.items():
                try:
                    res = requests.get(f"https://api.helius.xyz/v0/tokens/{addr}?api-key={HELIUS_API_KEY}")
                    data = res.json()
                    new_mc = float(data.get("marketCapUsd", 0))
                    x = new_mc / old_mc
                    if x >= 2:
                        try:
                            bot.send_message(
                                chat_id=TELEGRAM_CHANNEL,
                                text=f"🔥 {addr} has reached {x:.1f}x from ${int(old_mc):,} to ${int(new_mc):,}!",
                                parse_mode='Markdown'
                            )
                            posted[addr] = new_mc
                        except Exception as e:
                            logging.error(f"2x alert failed: {e}")
                except:
                    continue

            time.sleep(60)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(60)

# Flask app to keep alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=main).start()
    app.run(host="0.0.0.0", port=port)
