import telebot

BOT_TOKEN = "8675135375:AAGt-DgEgRWxvL3VWr3eM2j8oYchNlQ9TkY"
CHAT_ID = "6686356170"

bot = telebot.TeleBot(BOT_TOKEN)
bot.send_message(CHAT_ID, "PricePulse is alive!")   