import os
import requests
import time
import logging
from datetime import datetime, timedelta
from telegram import Bot
from flask import Flask
import threading

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL = "@zeusgemscalls"
HELIUS_API_KEY = os.getenv("HELIUS_KEY")
MIN_VOLUME = 50_000  # USD

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === DATA STORAGE ===
posted = {}
x_alerts = {}
token_history = {}

# === UTILS ===
def shorten(address):
    return address[:6] + "..." + address[-4:]

def fetch_new_tokens():
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}&limit=50"
    try:
        res = requests.get(url)
        return res.json()
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []

def passes_filters(token):
    try:
        if float(token.get("volumeUsd", 0)) < MIN_VOLUME:
            return False
        if not token.get("liquidityLocked", False):
            return False
        if token.get("canMint", True) and not token.get("renounced", False):
            return False
        return True
    except:
        return False

def build_message(token, is_alert=False, x_value=None):
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

    if is_alert:
        return f"🔥 *{name} ({symbol})* just hit *{x_value}x*!\nFrom ${posted[address]:,} to {mc} MC!\n[View Chart]({chart})"
    
    return f"""🔔 Zeus Gems | 🚀 {name} ({symbol})
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

⚠️ Safe token: Locked LP, no mint, renounced or both
Gamble play. NFA. DYOR."""

def check_token_updates():
    logging.info("Checking tokens...")
    tokens = fetch_new_tokens()

    for token in tokens:
        if not isinstance(token, dict):
            continue

        addr = token.get("address")
        if not addr:
            continue

        # New token post
        if addr not in posted and passes_filters(token):
            try:
                msg = build_message(token)
                bot.send_message(chat_id=TELEGRAM_CHANNEL, text=msg, parse_mode='Markdown', disable_web_page_preview=False)
                posted[addr] = int(token.get("marketCapUsd", 0))
                token_history[addr] = {
                    "name": token.get("name", "N/A"),
                    "mc_start": posted[addr],
                    "mc_current": posted[addr],
                    "x": 1,
                    "time": datetime.now()
                }
                x_alerts[addr] = 2
                logging.info(f"Posted token: {addr}")
            except Exception as e:
                logging.error(f"Error posting token: {e}")
        
        # X-checking
        elif addr in posted:
            try:
                current_mc = int(token.get("marketCapUsd", 0))
                token_history[addr]["mc_current"] = current_mc
                start_mc = posted[addr]
                x = x_alerts.get(addr, 2)
                if current_mc >= start_mc * x:
                    alert_msg = build_message(token, is_alert=True, x_value=x)
                    bot.send_message(chat_id=TELEGRAM_CHANNEL, text=alert_msg, parse_mode='Markdown')
                    x_alerts[addr] = x + 1
                    logging.info(f"{addr} hit {x}x")
            except Exception as e:
                logging.error(f"Error checking X status: {e}")

def weekly_summary():
    now = datetime.now()
    summary = "*🔥 Weekly Zeus Gems Roundup!*\n\n"
    count = 0

    for addr, data in token_history.items():
        if "time" in data and now - data["time"] < timedelta(days=7):
            gain = round(data["mc_current"] / data["mc_start"], 2)
            if gain >= 1.5:
                count += 1
                summary += f"• {data['name']}: {gain}x\n"

    if count > 0:
        try:
            bot.send_message(chat_id=TELEGRAM_CHANNEL, text=summary, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Failed to post weekly summary: {e}")
    else:
        logging.info("No strong performers this week.")

def run_bot():
    logging.info("Zeus Gems Bot starting...")
    while True:
        try:
            check_token_updates()
            if datetime.now().weekday() == 6 and datetime.now().hour == 20:
                weekly_summary()
            time.sleep(60)
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(60)

# === RENDER FLASK APP ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=port)
