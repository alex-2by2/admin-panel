import telebot
import os

# Bot token from Railway Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🤖 Bot Connected Successfully!\n\n"
        "Send any message and I will reply."
    )

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"You said: {message.text}")

print("🤖 Telegram Bot running...")

bot.infinity_polling()
