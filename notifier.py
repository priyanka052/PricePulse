"""
notifier.py — Sends Telegram price-drop alerts via pyTelegramBotAPI.
"""

import telebot

# ============================================================
# CONFIGURE THESE — replace with your Telegram bot credentials
# 1. Talk to @BotFather on Telegram to create a bot → get BOT_TOKEN
# 2. Message your bot, then visit:
#    https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
#    to find your CHAT_ID
# ============================================================
BOT_TOKEN = "6686356170"
CHAT_ID = "PricePulse_tracking_bot"


def send_alert(product_name: str, previous: int, latest: int):
    """
    Send a Telegram message when a price drop is detected.
    Shows product name, previous price, new price, and amount saved.
    """
    try:
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
            print(
                "[notifier] BOT_TOKEN / CHAT_ID not configured. "
                "Skipping Telegram alert. "
                f"{product_name}: Rs.{previous} → Now: Rs.{latest})"
            )
            return False

        bot = telebot.TeleBot(BOT_TOKEN)
        saved = previous - latest
        message = (
            f"Price Drop Detected! 📉\n"
            f"Product: {product_name}\n"
            f"Was: Rs.{previous}\n"
            f"Now: Rs.{latest}\n"
            f"Saved: Rs.{saved}"
        )
        bot.send_message(CHAT_ID, message)
        print(f"[notifier] Alert sent for {product_name} (saved Rs.{saved}).")
        return True
    except Exception as exc:
        print(f"[notifier] Failed to send Telegram alert: {exc}")
        return False


if __name__ == "__main__":
    # Standalone test — will skip if credentials are placeholders
    send_alert(product_name="iPhone 15", previous=59999, latest=54999)
