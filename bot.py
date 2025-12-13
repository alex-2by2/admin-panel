import telebot
import os
from db import init_db, captions

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# init DB safely
init_db()

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Bot connected. Send any message.")

@bot.message_handler(func=lambda m: True)
def reply_with_caption(message):
    if captions is None:
        bot.reply_to(message, "Caption DB not connected")
        return

    data = captions.find_one()
    text = data["text"] if data else "No caption set"
    bot.reply_to(message, text)

print("🤖 Bot running...")
bot.infinity_polling()
