import telebot
import os
from db import init_db, captions

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

init_db()

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Bot connected successfully!")

@bot.message_handler(func=lambda m: True)
def reply_with_caption(message):
    if captions is None:
        bot.reply_to(message, "DB not connected")
        return

    data = captions.find_one()
    bot.reply_to(message, data["text"] if data else "No caption set")

print("🤖 Bot running (single instance)")

bot.infinity_polling(skip_pending=True)
