import telebot
import os
from db import captions

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Bot connected.\nSend any message.")

@bot.message_handler(func=lambda m: True)
def reply_with_caption(message):
    data = captions.find_one()
    caption = data["text"] if data else "No caption set"

    bot.reply_to(message, caption)

print("🤖 Bot running...")
bot.infinity_polling()
