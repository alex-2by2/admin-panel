import telebot
import os
import db

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Channel Auto Caption Bot is running")

# ---------- CHANNEL POST HANDLER ----------
@bot.channel_post_handler(func=lambda m: True)
def auto_caption_channel_post(message):
    if db.captions is None:
        return

    data = db.captions.find_one({"type": "channel_caption"})
    if not data:
        return

    caption_text = data["text"]

    try:
        # If post has caption → edit
        if message.caption:
            bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption=caption_text
            )
        else:
            # If text post → edit text
            if message.text:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=message.text + "\n\n" + caption_text
                )
    except Exception as e:
        print("Edit failed:", e)

print("🤖 Bot running with channel auto-caption")

bot.infinity_polling(skip_pending=True)
