import requests
import time
import threading
import os
import logging
from datetime import datetime, timedelta
from flask import Flask

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHANNEL = "@YourChannelUsername"
HELIUS_API_KEY = "YOUR_HELIUS_API_KEY"
MIN_VOLUME = 50000
MAX_VOLUME = 200000
POSTED_TOKENS = {}
TRACKED_TOKENS = {}

# === REFERRAL LINKS ===
TROJAN_REF = "https://t.me/agamemnon_trojanbot?start=r-bigfave_001"
GMGNAI_REF = "https://t.me/gmgnaibot?start=i_QCOzrSSn"
AXIOM_REF = "http://axiom.trade/@bigfave00"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# === TELEGRAM FUNCTION ===
def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": msg,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload)
    return res.status_code == 200

# === TOKEN SCANNER ===
def scan_tokens():
    logger.info("Scanning tokens...")
    url = f"https://api.helius.xyz/v0/tokens?api-key={HELIUS_API_KEY}"
    try:
        res = requests.get(url)
        tokens = res.json()

        for token in tokens:
            addr = token.get("token_address")
            if not addr or addr in POSTED_TOKENS:
                continue

            volume = token.get("volume_usd", 0)
            liquidity = token.get("liquidity_usd", 0)
            age_minutes = token.get("age_minutes", 999)

            if not (MIN_VOLUME <= volume <= MAX_VOLUME):
                continue
            if age_minutes < 60:
                continue

            name = token.get("name", "Unknown")
            symbol = token.get("symbol", "???")
            mc = token.get("market_cap_usd", 0)
            holders = token.get("holders", 0)
            dev = token.get("deployer", "")[:6] + "..." + token.get("deployer", "")[-5:]
            top_holders = token.get("top_10_holders_percent", 0)
            bonding = token.get("bonding_curve", 0)
            platform = token.get("platform", "Unknown")
            birdeye_link = f"https://birdeye.so/token/{addr}?chain=solana"

            message = (
                f"🔔*{name.upper()}* | *{symbol}*\n"
                f"{addr}\n\n"
                f"🧢 Marketcap: ${mc:,.0f}\n"
                f"⏱️ Age: {int(age_minutes)}m\n\n"
                f"🧑‍💻 Dev: {dev} (💰 0%)\n"
                f"👥 Holders: {holders}\n"
                f"🔝 Top 10 holders: {top_holders}%\n"
                f"🚀 Volume: ${volume:,.0f}\n\n"
                f"🏛️ Platform: {platform}\n"
                f"💧 Liquidity: ${liquidity:,.0f}\n"
                f"📊 Bonding Curve: {bonding}%\n\n"
                f"🌍 Socials ↴\n\n"
                f"🐦 X profile\n"
                f"📝 X post\n"
                f"🔍 X community\n\n"
                f"[View on Birdeye]({birdeye_link})\n\n"
                f"Gamble Play, NFA, DYOR\n\n"
                f"🔗 [Trojan]({TROJAN_REF}) | [GMGNAI]({GMGNAI_REF}) | [Axiom]({AXIOM_REF})"
            )

            if send_telegram_message(message):
                POSTED_TOKENS[addr] = {
                    "price": token.get("price_usd", 0),
                    "mc": mc,
                    "time": time.time()
                }
                TRACKED_TOKENS[addr] = POSTED_TOKENS[addr]
                logger.info(f"Posted token: {symbol}")

    except Exception as e:
        logger.error(f"Error fetching tokens: {e}")

# === MULTIPLIER ALERTS ===
def check_multipliers():
    logger.info("Checking multipliers...")
    for addr, info in TRACKED_TOKENS.items():
        try:
            url = f"https://api.helius.xyz/v0/token/{addr}?api-key={HELIUS_API_KEY}"
            res = requests.get(url)
            token_data = res.json()

            current_mc = token_data.get("market_cap_usd", 0)
            posted_mc = info["mc"]

            for x in [2, 3, 4]:
                if current_mc >= posted_mc * x and not info.get(f"{x}x_alert"):
                    msg = (
                        f"🚀 *{token_data['name']}* (${token_data['symbol']}) just hit *{x}x* Market Cap!\n"
                        f"📈 From ${posted_mc:,.0f} to ${current_mc:,.0f}\n"
                        f"https://birdeye.so/token/{addr}?chain=solana"
                    )
                    send_telegram_message(msg)
                    info[f"{x}x_alert"] = True
                    logger.info(f"{token_data['symbol']} hit {x}x!")
        except Exception as e:
            logger.error(f"Error checking multipliers: {e}")

# === WEEKLY SUMMARY ===
def send_weekly_summary():
    logger.info("Sending weekly summary...")
    sorted_tokens = sorted(
        POSTED_TOKENS.items(),
        key=lambda item: item[1].get("mc", 0),
        reverse=True
    )[:5]

    summary = "*📊 Weekly Top 5 Tokens:*\n\n"
    for i, (addr, data) in enumerate(sorted_tokens, 1):
        summary += (
            f"{i}. [{addr[:6]}...] - MC: ${data['mc']:,.0f}\n"
        )
    summary += "\n✅ Tracked by Zeus Gems Bot\nDYOR 🔍"

    send_telegram_message(summary)

# === LOOP TASKS ===
def start_loop():
    while True:
        scan_tokens()
        check_multipliers()

        # Send summary every Monday at 9am
        if datetime.utcnow().weekday() == 0 and datetime.utcnow().hour == 9:
            send_weekly_summary()

        time.sleep(180)

# === FLASK FOR UPTIMEROBOT ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Zeus Gems Bot is live! 🔥"

def main():
    threading.Thread(target=start_loop).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    main()
    app.run(host="0.0.0.0", port=port)