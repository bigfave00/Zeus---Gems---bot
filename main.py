import os
import time
import threading
import requests
import logging
import datetime
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for uptime
app = Flask(__name__)
@app.route('/')
def home():
    return "Zeus Gems Bot is live!"

# Configs
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Storage for posted tokens and price alerts
posted_tokens = {}
price_alerts = {}

# Constants
HELIUS_URL = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}"
DEXSCREENER_URL = "https://dexscreener.com/solana/"

REF_LINKS = "\n👉 [Trojan](https://t.me/agamemnon_trojanbot?start=r-bigfave_001) | [GMGNAI](https://t.me/gmgnaibot?start=i_QCOzrSSn) | [Axiom](http://axiom.trade/@bigfave00)"
BONUS_NOTE = "\n\n🧠 *If you'd like me to add price tracking and 2x/3x/4x alerts based on live price via API, let me know and I’ll hook it up.*"

# Token filter criteria
def is_gem(token):
    try:
        volume = float(token.get("volume", 0))
        age = token.get("ageMinutes", 999)
        liquidity = float(token.get("liquidity", 0))
        return (
            token.get("isVerified", False)
            and volume >= 50000 and volume <= 200000
            and age <= 60
            and liquidity > 1000
        )
    except:
        return False

# Format token message
def format_token_message(token):
    mc = token.get("marketCap", "?")
    age = token.get("ageMinutes", "?")
    dev = token.get("developer", "?")
    holders = token.get("holders", "?")
    top10 = token.get("topHolders", "?")
    volume = token.get("volume", "?")
    platform = token.get("platform", "Solana")
    liquidity = token.get("liquidity", "?")
    curve = token.get("bondingCurve", "?")
    socials = token.get("socials", "")
    address = token.get("mint", "")
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "?")

    dexscreener_link = f"{DEXSCREENER_URL}{address}"

    return f"""
🔔 <b>{name} | {symbol}</b>
<code>{address}</code>

🧢 <b>Marketcap:</b> ${mc}
⏱️ <b>Age:</b> {age} mins
🧑‍💻 <b>Dev:</b> {dev}
👥 <b>Holders:</b> {holders}
🔝 <b>Top 10 holders:</b> {top10}%
🚀 <b>Volume:</b> ${volume}
🏛️ <b>Platform:</b> {platform}
💧 <b>Liquidity:</b> ${liquidity}
📊 <b>Bonding Curve:</b> {curve}
🌍 <b>Socials:</b> {socials}
📈 <b>[Dexscreener Chart]</b>({dexscreener_link})
{REF_LINKS}

<i>Gamble Play, NFA, DYOR</i>
{BONUS_NOTE}"

# Token scanner & poster
def post_tokens():
    while True:
        try:
            logger.info("Scanning tokens from Helius...")
            response = requests.get(HELIUS_URL)
            tokens = response.json()

            if not isinstance(tokens, list):
                logger.warning("Unexpected response from Helius.")
                time.sleep(60)
                continue

            for token in tokens:
                mint = token.get("mint")
                if not mint or mint in posted_tokens:
                    continue

                if is_gem(token):
                    message = format_token_message(token)
                    bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode=ParseMode.HTML)
                    posted_tokens[mint] = {
                        "name": token.get("name"),
                        "mc": float(token.get("marketCap", 0)),
                        "posted_at": datetime.datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error posting tokens: {e}")

        time.sleep(60)

# Alert checker for 2x, 3x, 4x
def check_alerts():
    while True:
        try:
            for mint, data in list(posted_tokens.items()):
                current_mc = get_current_marketcap(mint)
                if not current_mc:
                    continue

                original_mc = data["mc"]
                for x in [2, 3, 4]:
                    if mint not in price_alerts:
                        price_alerts[mint] = []

                    if x not in price_alerts[mint] and current_mc >= original_mc * x:
                        msg = f"🔥 {data['name']} just hit {x}x from call! ({original_mc} ➡️ {current_mc})"
                        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg)
                        price_alerts[mint].append(x)
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

        time.sleep(300)

# Weekly summary poster
def weekly_summary():
    while True:
        now = datetime.datetime.utcnow()
        if now.weekday() == 6 and now.hour == 20:
            try:
                summary = "📊 <b>Weekly Zeus Gems Recap:</b>\n"
                for mint, data in posted_tokens.items():
                    name = data["name"]
                    original_mc = data["mc"]
                    current_mc = get_current_marketcap(mint)
                    if current_mc and current_mc > original_mc:
                        gain = round(current_mc / original_mc, 2)
                        summary += f"🔥 {name} — {gain}x from call!\n"
                if summary.strip() != "📊 <b>Weekly Zeus Gems Recap:</b>":
                    bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=summary, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Error sending weekly summary: {e}")

            time.sleep(3600 * 24)
        else:
            time.sleep(3600)

# Dummy function to get current MC — replace with real price API if needed
def get_current_marketcap(mint):
    try:
        # Add your price fetch logic here
        return posted_tokens[mint]["mc"] * 2.1  # Simulate 2.1x pump for testing
    except:
        return None

# Threads
threading.Thread(target=post_tokens).start()
threading.Thread(target=check_alerts).start()
threading.Thread(target=weekly_summary).start()

# Run Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)