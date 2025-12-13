import telebot
import os
import db   # 🔥 IMPORT MODULE

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Bot connected")

@bot.message_handler(func=lambda m: True)
def reply_with_caption(message):
    if db.captions is None:
        bot.reply_to(message, "DB not connected")
        return

    data = db.captions.find_one()
    bot.reply_to(message, data["text"] if data else "No caption set")

print("🤖 Bot running")

bot.infinity_polling(skip_pending=True)
