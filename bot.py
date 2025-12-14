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

    caption_text = None

    # 📷 PHOTO
    if message.photo:
        doc = db.captions.find_one({"type": "photo_caption"})
        if doc:
            caption_text = doc["text"]

        if caption_text:
            try:
                bot.edit_message_caption(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    caption=caption_text
                )
            except Exception as e:
                print("Photo edit failed:", e)

    # 🎥 VIDEO
    elif message.video:
        doc = db.captions.find_one({"type": "video_caption"})
        if doc:
            caption_text = doc["text"]

        if caption_text:
            try:
                bot.edit_message_caption(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    caption=caption_text
                )
            except Exception as e:
                print("Video edit failed:", e)

    # 📝 TEXT
    elif message.text:
        doc = db.captions.find_one({"type": "text_caption"})
        if doc:
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=message.text + "\n\n" + doc["text"]
                )
            except Exception as e:
                print("Text edit failed:", e)

print("🤖 Bot running with channel auto-caption")

bot.infinity_polling(skip_pending=True)
